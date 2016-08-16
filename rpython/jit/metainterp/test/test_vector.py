import py
import pytest
import math
import functools
from hypothesis import given, note, strategies as st
from rpython.jit.metainterp.warmspot import ll_meta_interp, get_stats
from rpython.jit.metainterp.test.support import LLJitMixin
from rpython.jit.codewriter.policy import StopAtXPolicy
from rpython.jit.metainterp.resoperation import rop
from rpython.jit.metainterp import history
from rpython.rlib.jit import JitDriver, hint, set_param
from rpython.rlib.objectmodel import compute_hash
from rpython.rlib import rfloat
from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.rlib.rarithmetic import r_uint, intmask, r_int
from rpython.rlib.rawstorage import (alloc_raw_storage, raw_storage_setitem,
                                     free_raw_storage, raw_storage_getitem)
from rpython.rlib.objectmodel import (specialize, is_annotation_constant,
        always_inline)
from rpython.jit.backend.detect_cpu import getcpuclass
from rpython.jit.tool.oparser import parse
from rpython.jit.metainterp.history import (AbstractFailDescr,
                                            AbstractDescr,
                                            BasicFailDescr, BasicFinalDescr,
                                            JitCellToken, TargetToken,
                                            ConstInt, ConstPtr,
                                            Const, ConstFloat)

CPU = getcpuclass()

@specialize.argtype(0,1)
def malloc(T,n):
    return lltype.malloc(T, n, flavor='raw', zero=True)
def free(mem):
    lltype.free(mem, flavor='raw')

def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol) \
           or (math.isnan(a) and math.isnan(b)) or \
                  (math.isinf(a) and math.isinf(b) and \
                   (a < 0.0 and b < 0.0) or \
                   (a > 0.0 and b > 0.0))

class RawStorage(object):
    def __init__(self):
        self.arrays = []

    def new(self, values, type, size=None, zero=True):
        bytecount = rffi.sizeof(type)
        if not values:
            array = alloc_raw_storage(size*bytecount, zero=zero)
            self.arrays.append(array)
            return array
        else:
            size = len(values)*bytecount
            array = alloc_raw_storage(size, zero=zero)
            for i,v in enumerate(values):
                raw_storage_setitem(array, i*bytecount, rffi.cast(type,v))
            self.arrays.append(array)
            return array

    def clear(self):
        while self.arrays:
            array = self.arrays.pop()
            free_raw_storage(array)

@pytest.fixture(scope='function')
def rawstorage(request):
    rs = RawStorage()
    request.addfinalizer(rs.clear)
    request.cls.a
    return rs


def rdiv(v1,v2):
    # TODO unused, interpeting this on top of llgraph does not work correctly
    try:
        return v1 / v2
    except ZeroDivisionError:
        if v1 == v2 == 0.0:
            return rfloat.NAN
        return rfloat.copysign(rfloat.INFINITY, v1 * v2)

class VectorizeTests(object):
    enable_opts = 'intbounds:rewrite:virtualize:string:earlyforce:pure:heap:unroll'

    def setup_method(self, method):
        if not self.supports_vector_ext():
            py.test.skip("this cpu %s has no implemented vector backend" % CPU)

    def meta_interp(self, f, args, policy=None, vec=True, vec_all=False):
        return ll_meta_interp(f, args, enable_opts=self.enable_opts,
                              policy=policy,
                              CPUClass=self.CPUClass,
                              type_system=self.type_system,
                              vec=vec, vec_all=vec_all)

    # FLOAT UNARY

    def _vector_float_unary(self, func, type, data):
        func = always_inline(func)

        size = rffi.sizeof(type)
        myjitdriver = JitDriver(greens = [], reds = 'auto', vectorize=True)
        def f(bytecount, va, vc):
            i = 0
            while i < bytecount:
                myjitdriver.jit_merge_point()
                a = raw_storage_getitem(type,va,i)
                c = func(a)
                raw_storage_setitem(vc, i, rffi.cast(type,c))
                i += size

        la = data.draw(st.lists(st.floats(), min_size=10, max_size=150))
        l = len(la)

        rawstorage = RawStorage()
        va = rawstorage.new(la, type)
        vc = rawstorage.new(None, type, size=l)
        self.meta_interp(f, [l*size, va, vc])

        for i in range(l):
            c = raw_storage_getitem(type,vc,i*size)
            r = func(la[i])
            assert isclose(r, c)

        rawstorage.clear()

    def vec_int_unary(test_func, unary_func, type):
        return pytest.mark.parametrize('func,type', [
            (unary_func, type)
        ])(given(data=st.data())(test_func))

    vec_float_unary = functools.partial(vec_int_unary, _vector_float_unary)

    test_vec_abs_float = \
            vec_float_unary(lambda v: abs(v), rffi.DOUBLE)
    test_vec_neg_float = \
            vec_float_unary(lambda v: -v, rffi.DOUBLE)

    # FLOAT BINARY

    def _vector_simple_float(self, func, type, data):
        func = always_inline(func)

        size = rffi.sizeof(rffi.DOUBLE)
        myjitdriver = JitDriver(greens = [], reds = 'auto', vectorize=True)
        def f(bytecount, va, vb, vc):
            i = 0
            while i < bytecount:
                myjitdriver.jit_merge_point()
                a = raw_storage_getitem(type,va,i)
                b = raw_storage_getitem(type,vb,i)
                c = func(a,b)
                raw_storage_setitem(vc, i, rffi.cast(type,c))
                i += size

        la = data.draw(st.lists(st.floats(), min_size=10, max_size=150))
        #la = [0.0,0.0,0.0,0.0,0.0,0.0,0.0]
        #lb = [0.0,0.0,0.0,0.0,1.7976931348623157e+308,0.0,0.0]
        l = len(la)
        lb = data.draw(st.lists(st.floats(), min_size=l, max_size=l))

        rawstorage = RawStorage()
        va = rawstorage.new(la, type)
        vb = rawstorage.new(lb, type)
        vc = rawstorage.new(None, type, size=l)
        self.meta_interp(f, [l*size, va, vb, vc])

        for i in range(l):
            c = raw_storage_getitem(type,vc,i*size)
            r = rffi.cast(type, func(la[i], lb[i]))
            assert isclose(r, c)

        rawstorage.clear()

    def _vec_float_binary(test_func, func, type):
        return pytest.mark.parametrize('func,type', [
            (func, type)
        ])(given(data=st.data())(test_func))

    vec_float_binary = functools.partial(_vec_float_binary, _vector_simple_float)

    test_vec_float_add = \
        vec_float_binary(lambda a,b: a+b, rffi.DOUBLE)
    test_vec_float_sub = \
        vec_float_binary(lambda a,b: a-b, rffi.DOUBLE)
    test_vec_float_mul = \
        vec_float_binary(lambda a,b: a*b, rffi.DOUBLE)
    #test_vec_float_div = \
    #    vec_float_binary(lambda a,b: a/b, rffi.DOUBLE)

    test_vec_float_cmp_eq = \
        vec_float_binary(lambda a,b: a == b, rffi.DOUBLE)
    test_vec_float_cmp_ne = \
        vec_float_binary(lambda a,b: a != b, rffi.DOUBLE)

    def _vector_simple_int(self, func, type, data):
        func = always_inline(func)

        size = rffi.sizeof(type)
        myjitdriver = JitDriver(greens = [], reds = 'auto', vectorize=True)
        def f(bytecount, va, vb, vc):
            i = 0
            while i < bytecount:
                myjitdriver.jit_merge_point()
                a = raw_storage_getitem(type,va,i)
                b = raw_storage_getitem(type,vb,i)
                c = func(a,b)
                raw_storage_setitem(vc, i, rffi.cast(type,c))
                i += size

        bits = size*8
        integers = st.integers(min_value=-2**(bits-1), max_value=2**(bits-1)-1)
        la = data.draw(st.lists(integers, min_size=10, max_size=150))
        l = len(la)
        lb = data.draw(st.lists(integers, min_size=l, max_size=l))

        rawstorage = RawStorage()
        va = rawstorage.new(la, type)
        vb = rawstorage.new(lb, type)
        vc = rawstorage.new(None, type, size=l)
        self.meta_interp(f, [l*size, va, vb, vc])

        for i in range(l):
            c = raw_storage_getitem(type,vc,i*size)
            assert rffi.cast(type, func(la[i], lb[i])) == c

        rawstorage.clear()

    def vec_int_arith(test_func, arith_func, type):
        return pytest.mark.parametrize('func,type', [
            (arith_func, type)
        ])(given(data=st.data())(test_func))

    vec_int_arith = functools.partial(vec_int_arith, _vector_simple_int)

    test_vec_signed_add = \
        vec_int_arith(lambda a,b: intmask(a+b), rffi.SIGNED)
    test_vec_int_add = \
        vec_int_arith(lambda a,b: r_int(a)+r_int(b), rffi.INT)
    test_vec_short_add = \
        vec_int_arith(lambda a,b: r_int(a)+r_int(b), rffi.SHORT)

    test_vec_sub_signed = \
        vec_int_arith(lambda a,b: intmask(a-b), rffi.SIGNED)
    test_vec_sub_int = \
        vec_int_arith(lambda a,b: r_int(a)-r_int(b), rffi.INT)
    test_vec_sub_short = \
        vec_int_arith(lambda a,b: r_int(a)-r_int(b), rffi.SHORT)

    test_vec_signed_and = \
        vec_int_arith(lambda a,b: intmask(a)&intmask(b), rffi.SIGNED)
    test_vec_int_and = \
        vec_int_arith(lambda a,b: intmask(a)&intmask(b), rffi.INT)
    test_vec_short_and = \
        vec_int_arith(lambda a,b: intmask(a)&intmask(b), rffi.SHORT)

    test_vec_or_signed = \
        vec_int_arith(lambda a,b: intmask(a)|intmask(b), rffi.SIGNED)
    test_vec_or_int = \
        vec_int_arith(lambda a,b: intmask(a)|intmask(b), rffi.INT)
    test_vec_or_short = \
        vec_int_arith(lambda a,b: intmask(a)|intmask(b), rffi.SHORT)

    test_vec_xor_signed = \
        vec_int_arith(lambda a,b: intmask(a)^intmask(b), rffi.SIGNED)
    test_vec_xor_int = \
        vec_int_arith(lambda a,b: intmask(a)^intmask(b), rffi.INT)
    test_vec_xor_short = \
        vec_int_arith(lambda a,b: intmask(a)^intmask(b), rffi.SHORT)

    test_vec_int_eq = \
        vec_int_arith(lambda a,b: a == b, rffi.SIGNED)
    test_vec_int_ne = \
        vec_int_arith(lambda a,b: a == b, rffi.SIGNED)

    @py.test.mark.parametrize('i',[1,2,3,4,9])
    def test_vec_register_too_small_vector(self, i):
        myjitdriver = JitDriver(greens = [],
                                reds = 'auto',
                                vectorize=True)
        T = lltype.Array(rffi.SHORT, hints={'nolength': True})

        def g(d, va, vb):
            i = 0
            while i < d:
                myjitdriver.jit_merge_point()
                a = va[i]
                b = vb[i]
                ec = intmask(a) + intmask(b)
                va[i] = rffi.r_short(ec)
                i += 1

        def f(d):
            i = 0
            va = lltype.malloc(T, d+100, flavor='raw', zero=True)
            vb = lltype.malloc(T, d+100, flavor='raw', zero=True)
            for j in range(d+100):
                va[j] = rffi.r_short(1)
                vb[j] = rffi.r_short(2)

            g(d+100, va, vb)
            g(d, va, vb) # this iteration might not fit into the vector register

            res = intmask(va[d])
            lltype.free(va, flavor='raw')
            lltype.free(vb, flavor='raw')
            return res
        res = self.meta_interp(f, [i])
        assert res == f(i) == 3

    def test_vec_max(self):
        myjitdriver = JitDriver(greens = [],
                                reds = 'auto',
                                vectorize=True)
        def fmax(v1, v2):
            return v1 if v1 >= v2 or rfloat.isnan(v2) else v2
        T = lltype.Array(rffi.DOUBLE, hints={'nolength': True})
        def f(d):
            i = 0
            va = lltype.malloc(T, d, flavor='raw', zero=True)
            for j in range(d):
                va[j] = float(j)
            va[13] = 128.0
            m = -128.0
            while i < d:
                myjitdriver.jit_merge_point()
                a = va[i]
                m = fmax(a, m)
                i += 1
            lltype.free(va, flavor='raw')
            return m
        res = self.meta_interp(f, [30])
        assert res == f(30) == 128

    @py.test.mark.parametrize('type,func,init,insert,at,count,breaks',
            # all
           [(rffi.DOUBLE, lambda x: not bool(x), 1.0, None, -1,32, False),
            (rffi.DOUBLE, lambda x: x == 0.0,    1.0, None, -1,33, False),
            (rffi.DOUBLE, lambda x: x == 0.0,    1.0, 0.0,  33,34, True),
            (rffi.DOUBLE, lambda x: x == 0.0,    1.0, 0.1,  4,34, False),
            (lltype.Signed, lambda x: not bool(x), 1, None, -1,32, False),
            (lltype.Signed, lambda x: not bool(x), 1, 0,    14,32, True),
            (lltype.Signed, lambda x: not bool(x), 1, 0,    15,31, True),
            (lltype.Signed, lambda x: not bool(x), 1, 0,    4,30, True),
            (lltype.Signed, lambda x: x == 0,      1, None, -1,33, False),
            (lltype.Signed, lambda x: x == 0,      1, 0,  33,34, True),
            # any
            (rffi.DOUBLE, lambda x: x != 0.0,    0.0, 1.0,  33,35, True),
            (rffi.DOUBLE, lambda x: x != 0.0,    0.0, 1.0,  -1,36, False),
            (rffi.DOUBLE, lambda x: bool(x),     0.0, 1.0,  33,37, True),
            (rffi.DOUBLE, lambda x: bool(x),     0.0, 1.0,  -1,38, False),
            (lltype.Signed, lambda x: x != 0,    0, 1,  33,35, True),
            (lltype.Signed, lambda x: x != 0,    0, 1,  -1,36, False),
            (lltype.Signed, lambda x: bool(x),   0, 1,  33,37, True),
            (lltype.Signed, lambda x: bool(x),   0, 1,  -1,38, False),
            (rffi.INT, lambda x: intmask(x) != 0,    rffi.r_int(0), rffi.r_int(1),  33,35, True),
            (rffi.INT, lambda x: intmask(x) != 0,    rffi.r_int(0), rffi.r_int(1),  -1,36, False),
            (rffi.INT, lambda x: bool(intmask(x)),   rffi.r_int(0), rffi.r_int(1),  33,37, True),
            (rffi.INT, lambda x: bool(intmask(x)),   rffi.r_int(0), rffi.r_int(1),  -1,38, False),
           ])
    def test_bool_reduction(self, type, func, init, insert, at, count, breaks):
        myjitdriver = JitDriver(greens = [], reds = 'auto', vectorize=True)
        T = lltype.Array(type, hints={'nolength': True})
        def f(d):
            va = lltype.malloc(T, d, flavor='raw', zero=True)
            for i in range(d): va[i] = init
            if at != -1:
                va[at] = insert
            i = 0 ; nobreak = False
            while i < d:
                myjitdriver.jit_merge_point()
                b = func(va[i])
                if b:
                    assert b
                    break
                i += 1
            else:
                nobreak = True
            lltype.free(va, flavor='raw')
            return not nobreak
        res = self.meta_interp(f, [count])
        assert res == f(count) == breaks

    @py.test.mark.parametrize('type,func,cast',
            [(rffi.DOUBLE, lambda a,b: a+b, float),
             (rffi.DOUBLE, lambda a,b: a*b, float),
             (lltype.Signed, lambda a,b: a+b, int),
             (lltype.Signed, lambda a,b: a*b, int),
            ])
    def test_reduce(self, type, func, cast):
        func = always_inline(func)
        myjitdriver = JitDriver(greens = [], reds = 'auto', vectorize=True)
        T = lltype.Array(type, hints={'nolength': True})
        def f(d):
            va = lltype.malloc(T, d, flavor='raw', zero=True)
            for j in range(d):
                va[j] = cast(j+1)
            i = 0
            accum = 0
            while i < d:
                myjitdriver.jit_merge_point()
                accum = func(accum,va[i])
                i += 1
            lltype.free(va, flavor='raw')
            return accum
        res = self.meta_interp(f, [60])
        assert isclose(res, f(60))

    def test_constant_expand(self):
        myjitdriver = JitDriver(greens = [], reds = 'auto', vectorize=True)
        T = lltype.Array(rffi.DOUBLE, hints={'nolength': True})
        def f(d):
            va = lltype.malloc(T, d, flavor='raw', zero=True)
            i = 0
            while i < d:
                myjitdriver.jit_merge_point()
                va[i] = va[i] + 34.5
                i += 1
            val = va[0]
            lltype.free(va, flavor='raw')
            return val
        res = self.meta_interp(f, [60])
        assert res == f(60) == 34.5

    def test_constant_expand_vec_all(self):
        myjitdriver = JitDriver(greens = [], reds = 'auto')
        T = lltype.Array(rffi.DOUBLE, hints={'nolength': True})
        def f(d):
            va = lltype.malloc(T, d, flavor='raw', zero=True)
            i = 0
            while i < d:
                myjitdriver.jit_merge_point()
                if not (i < d):
                    raise IndexError
                va[i] = va[i] + 34.5
                i += 1
            val = va[0]
            lltype.free(va, flavor='raw')
            return val
        res = self.meta_interp(f, [60], vec_all=True)
        assert res == f(60) == 34.5

    @py.test.mark.parametrize('type,value', [(rffi.DOUBLE, 58.4547),
        (lltype.Signed, 2300000), (rffi.INT, 4321),
        (rffi.SHORT, 9922), (rffi.SIGNEDCHAR, -127)])
    def test_variable_expand(self, type, value):
        myjitdriver = JitDriver(greens = [], reds = 'auto', vectorize=True)
        T = lltype.Array(type, hints={'nolength': True})
        def f(d,variable):
            va = lltype.malloc(T, d, flavor='raw', zero=True)
            i = 0
            while i < d:
                myjitdriver.jit_merge_point()
                va[i] = rffi.cast(type, variable)
                i += 1
            val = va[d//2]
            lltype.free(va, flavor='raw')
            return val
        res = self.meta_interp(f, [60,value])
        assert res == f(60,value) == value

    @py.test.mark.parametrize('vec,vec_all',[(False,True),(True,False),(True,True),(False,False)])
    def test_accum(self, vec, vec_all):
        myjitdriver = JitDriver(greens = [], reds = 'auto', vectorize=vec)
        T = lltype.Array(rffi.DOUBLE)
        def f(d, value):
            va = lltype.malloc(T, d, flavor='raw', zero=True)
            for i in range(d):
                va[i] = value
            r = 0
            i = 0
            k = d + 2
            # in this case a guard k <= d is inserted which fails right away!
            while i < d:
                myjitdriver.jit_merge_point()
                if not(i < k):
                    k -= 1
                r += va[i]
                i += 1
            lltype.free(va, flavor='raw')
            return r
        res = self.meta_interp(f, [60,0.5], vec=vec, vec_all=vec_all)
        assert res == f(60,0.5) == 60*0.5


    @py.test.mark.parametrize('i',[15])
    def test_array_bounds_check_elimination(self,i):
        myjitdriver = JitDriver(greens = [],
                                reds = 'auto',
                                vectorize=True)
        T = lltype.Array(rffi.INT, hints={'nolength': True})
        def f(d):
            va = lltype.malloc(T, d, flavor='raw', zero=True)
            vb = lltype.malloc(T, d, flavor='raw', zero=True)
            for j in range(d):
                va[j] = rffi.r_int(j)
                vb[j] = rffi.r_int(j)
            i = 0
            while i < d:
                myjitdriver.jit_merge_point()

                if i < 0:
                    raise IndexError
                if i >= d:
                    raise IndexError
                a = va[i]
                if i < 0:
                    raise IndexError
                if i >= d:
                    raise IndexError
                b = vb[i]
                ec = intmask(a)+intmask(b)
                if i < 0:
                    raise IndexError
                if i >= d:
                    raise IndexError
                va[i] = rffi.r_int(ec)

                i += 1
            lltype.free(va, flavor='raw')
            lltype.free(vb, flavor='raw')
            return 0
        res = self.meta_interp(f, [i])
        assert res == f(i)

    @py.test.mark.parametrize('i,v1,v2',[(25,2.5,0.3),(25,2.5,0.3)])
    def test_list_vectorize(self,i,v1,v2):
        myjitdriver = JitDriver(greens = [],
                                reds = 'auto')
        class ListF(object):
            def __init__(self, size, init):
                self.list = [init] * size
            def __getitem__(self, key):
                return self.list[key]
            def __setitem__(self, key, value):
                self.list[key] = value
        def f(d, v1, v2):
            a = ListF(d, v1)
            b = ListF(d, v2)
            i = 0
            while i < d:
                myjitdriver.jit_merge_point()
                a[i] = a[i] + b[i]
                i += 1
            s = 0
            for i in range(d):
                s += a[i]
            return s
        res = self.meta_interp(f, [i,v1,v2], vec_all=True)
        # sum helps to generate the rounding error of floating points
        # return 69.999 ... instead of 70, (v1+v2)*i == 70.0
        assert res == f(i,v1,v2) == sum([v1+v2]*i)

    @py.test.mark.parametrize('size',[12])
    def test_body_multiple_accesses(self, size):
        myjitdriver = JitDriver(greens = [], reds = 'auto')
        T = lltype.Array(rffi.CHAR, hints={'nolength': True})
        def f(size):
            vector_a = malloc(T, size)
            vector_b = malloc(T, size)
            i = 0
            while i < size:
                myjitdriver.jit_merge_point()
                # should unroll and group them correctly
                c1 = vector_a[i]
                c2 = vector_a[i+1]
                c3 = vector_a[i+2]
                #
                vector_b[i] = c1
                vector_b[i+1] = c2
                vector_b[i+2] = c3
                i += 3
            free(vector_a)
            free(vector_b)
            return 0
        res = self.meta_interp(f, [size], vec_all=True)
        assert res == f(size)

    def test_max_byte(self):
        myjitdriver = JitDriver(greens = [], reds = 'auto')
        T = lltype.Array(rffi.SIGNEDCHAR, hints={'nolength': True})
        def f(size):
            vector_a = malloc(T, size)
            for i in range(size):
                vector_a[i] = rffi.r_signedchar(1)
            for i in range(size/2,size):
                vector_a[i] = rffi.r_signedchar(i)
            i = 0
            max = -127
            while i < size:
                myjitdriver.jit_merge_point()
                a = intmask(vector_a[i])
                a = a & 255
                if a > max:
                    max = a
                i += 1
            free(vector_a)
            return max
        res = self.meta_interp(f, [128], vec_all=True)
        assert res == f(128)


    def combinations(types, operators):
        import itertools
        size = 22

        class Typ(object):
            def __init__(self, type, storecast, loadcast):
                self.type = type
                self.storecast = storecast
                self.loadcast = loadcast
            def __repr__(self):
                return self.type.replace(".","_")

        sizes = [22]
        for t1, t2, t3, op, size in itertools.product(types, types, types, operators, sizes):
            yield (size, Typ(*t1), Typ(*t2), Typ(*t3), op[0], op[1])
    types = [('rffi.DOUBLE', 'float', 'float'),
             ('rffi.SIGNED', 'int', 'int'),
             #('rffi.FLOAT', 'rffi.r_singlefloat', 'float'),
            ]
    operators = [('add', '+'),
                ]
    for size, typ1, typ2, typ3, opname, op in combinations(types, operators):
        _source = """
        def test_binary_operations_{name}(self):
            myjitdriver = JitDriver(greens = [], reds = 'auto')
            T1 = lltype.Array({type_a}, hints={{'nolength': True}})
            T2 = lltype.Array({type_b}, hints={{'nolength': True}})
            T3 = lltype.Array({type_c}, hints={{'nolength': True}})
            def f(size):
                vector_a = lltype.malloc(T1, size, flavor='raw')
                vector_b = lltype.malloc(T2, size, flavor='raw')
                vector_c = lltype.malloc(T3, size, flavor='raw')
                for i in range(size):
                    vector_a[i] = {type_a_storecast}(1)
                for i in range(size):
                    vector_b[i] = {type_b_storecast}(1)
                for i in range(size):
                    vector_c[i] = {type_c_storecast}(1)
                i = 0
                while i < size:
                    myjitdriver.jit_merge_point()
                    a = {type_a_loadcast}(vector_a[i])
                    b = {type_b_loadcast}(vector_b[i])
                    c = (a {op} b)
                    vector_c[i] = {type_c_storecast}(c)
                    i += 1
                lltype.free(vector_a, flavor='raw')
                lltype.free(vector_b, flavor='raw')
                c = {type_c_loadcast}(0.0)
                for i in range(size):
                    c += {type_c_loadcast}(vector_c[i])
                lltype.free(vector_c, flavor='raw')
                return c
            res = self.meta_interp(f, [{size}], vec_all=True)
            assert res == f({size})
        """
        env = {
          'type_a': typ1.type,
          'type_b': typ2.type,
          'type_c': typ3.type,
          'type_a_loadcast': typ1.loadcast,
          'type_b_loadcast': typ2.loadcast,
          'type_c_loadcast': typ3.loadcast,
          'type_a_storecast': typ1.storecast,
          'type_b_storecast': typ2.storecast,
          'type_c_storecast': typ3.storecast,
          'size': size,
          'name': str(typ1) + '__' + str(typ2) + '__' + str(typ3) + \
                  '__' + str(size) + '__' + opname,
          'op': op,
        }
        formatted = _source.format(**env)
        exec py.code.Source(formatted).compile()

    def test_binary_operations_aa(self):
        myjitdriver = JitDriver(greens = [], reds = 'auto')
        T1 = lltype.Array(rffi.DOUBLE, hints={'nolength': True})
        T3 = lltype.Array(rffi.SIGNED, hints={'nolength': True})
        def f(size):
            vector_a = lltype.malloc(T1, size, flavor='raw', zero=True)
            vector_b = lltype.malloc(T1, size, flavor='raw', zero=True)
            vector_c = lltype.malloc(T3, size, flavor='raw', zero=True)
            i = 0
            while i < size:
                myjitdriver.jit_merge_point()
                a = (vector_a[i])
                b = (vector_b[i])
                c = (a + b)
                vector_c[i] = int(c)
                i += 1
            free(vector_a)
            free(vector_b)
            #c = 0.0
            #for i in range(size):
            #    c += vector_c[i]
            lltype.free(vector_c, flavor='raw')
            return 0
        res = self.meta_interp(f, [22], vec_all=True)
        assert res == f(22)

    def test_guard_test_location_assert(self):
        myjitdriver = JitDriver(greens = [], reds = 'auto')
        T1 = lltype.Array(rffi.SIGNED, hints={'nolength': True})
        def f(size):
            vector_a = lltype.malloc(T1, size, flavor='raw', zero=True)
            for i in range(size):
                vector_a[i] = 0
            i = 0
            breaks = 0
            while i < size:
                myjitdriver.jit_merge_point()
                a = vector_a[i]
                if a:
                    breaks = 1
                    break
                del a
                i += 1
            lltype.free(vector_a, flavor='raw')
            return breaks
        res = self.meta_interp(f, [22], vec_all=True, vec_guard_ratio=5)
        assert res == f(22)

    def run_unpack(self, unpack, vector_type, assignments, float=True):
        vars = {'v':0,'f':0,'i':0}
        def newvar(type):
            c = vars[type]
            vars[type] = c + 1
            if type == 'v':
                return type + str(c) + vector_type
            return type + str(c)
        targettoken = TargetToken()
        finaldescr = BasicFinalDescr(1)
        args = []
        args_values = []
        pack = []
        suffix = 'f' if float else 'i'
        for var, vals in assignments.items():
            v = newvar('v')
            pack.append('%s = vec_%s()' % (v, suffix))
            for i,val in enumerate(vals):
                args_values.append(val)
                f = newvar(suffix)
                args.append(f)
                count = 1
                # create a new variable
                vo = v
                v = newvar('v')
                pack.append('%s = vec_pack_%s(%s, %s, %d, %d)' % \
                            (v, suffix, vo, f, i, count))
            vars['x'] = v
        packs = '\n        '.join(pack)
        resvar = suffix + '{'+suffix+'}'

        # format the resoperations, take care that the lhs of =
        # is formated later with a new variable name
        unpackops = unpack
        if isinstance(unpack, str):
            unpackops = [unpack]
        unpacksf = []
        for up in unpackops:
            lhs, rhs = up.split("=")
            rhsf = rhs.format(**vars)
            newvar('i'); newvar('f'); newvar('v')
            lhsf = lhs.format(**vars)
            unpacksf.append(lhsf + '=' + rhsf)
        unpacks = '\n        '.join(unpacksf)

        source = '''
        [{args}]
        label({args}, descr=targettoken)
        {packs}
        {unpacks}
        finish({resvar}, descr=finaldescr)
        '''.format(args=','.join(args),packs=packs, unpacks=unpacks,
                   resvar=resvar.format(**vars))
        print(source)
        return self._compile_and_run(source, args_values, float,
                ns={'targettoken': targettoken, 'finaldescr': finaldescr})


    def _compile_and_run(self, source, args_values, float=True, ns={}):
        loop = parse(source, namespace=ns)
        cpu = self.CPUClass(rtyper=None, stats=None)
        cpu.setup_once()
        #
        looptoken = JitCellToken()
        cpu.compile_loop(loop.inputargs, loop.operations, looptoken)
        import pdb; pdb.set_trace()
        deadframe = cpu.execute_token(looptoken, *args_values)
        print(source)
        if float:
            return cpu.get_float_value(deadframe, 0)
        else:
            return cpu.get_int_value(deadframe, 0)

    def test_unpack_f(self):
        # double unpack
        assert self.run_unpack("f{f} = vec_unpack_f({x}, 0, 1)",
                               "[2xf64]", {'x': (1.2,-1.0)}) == 1.2
        assert self.run_unpack("f{f} = vec_unpack_f({x}, 1, 1)",
                               "[2xf64]", {'x': (50.33,4321.0)}) == 4321.0
    def test_unpack_i64(self):
        # int64
        assert self.run_unpack("i{i} = vec_unpack_i({x}, 0, 1)",
                               "[2xi64]", {'x': (11,12)}, float=False) == 11
        assert self.run_unpack("i{i} = vec_unpack_i({x}, 1, 1)",
                               "[2xi64]", {'x': (14,15)}, float=False) == 15

    def test_unpack_i(self):
        for i in range(16):
            # i8
            op = "i{i} = vec_unpack_i({x}, %d, 1)" % i
            assert self.run_unpack(op, "[16xi8]", {'x': [127,1]*8}, float=False) == \
                   (127 if i%2==0 else 1)
            # i16
            if i < 8:
                assert self.run_unpack(op, "[8xi16]", {'x': [2**15-1,0]*4}, float=False) == \
                       (2**15-1 if i%2==0 else 0)
            # i32
            if i < 4:
                assert self.run_unpack(op, "[4xi32]", {'x': [2**31-1,0]*4}, float=False) == \
                       (2**31-1 if i%2==0 else 0)

    def test_unpack_several(self):
        # count == 2
        values = [1,2,3,4]
        for i,v in enumerate(values):
            j = (i // 2) * 2
            op = ["v{v}[2xi32] = vec_unpack_i({x}, %d, 2)" % j,
                  "i{i} = vec_unpack_i(v{v}[2xi32], %d, 1)" % i]
            assert self.run_unpack(op, "[4xi32]", {'x': values}, float=False) == v

        values = [1,2,3,4,5,6,7,8]
        for i,v in enumerate(values):
            j = (i // 4) * 4
            op = ["v{v}[4xi16] = vec_unpack_i({x}, %d, 4)" % j,
                  "i{i} = vec_unpack_i(v{v}[4xi16], %d, 1)" % i]
            assert self.run_unpack(op, "[8xi16]", {'x': values}, float=False) == v

        values = [1,2,3,4,5,6,7,8] * 2
        for i,v in enumerate(values):
            j = (i // 8) * 8
            op = ["v{v}[8xi8] = vec_unpack_i({x}, %d, 8)" % j,
                  "i{i} = vec_unpack_i(v{v}[8xi8], %d, 1)" % i]
            assert self.run_unpack(op, "[16xi8]", {'x': values}, float=False) == v


class TestLLtype(LLJitMixin, VectorizeTests):
    pass
