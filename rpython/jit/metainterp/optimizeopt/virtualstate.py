from rpython.jit.metainterp.walkvirtual import VirtualVisitor
from rpython.jit.metainterp.history import (ConstInt, Const,
        ConstPtr, ConstFloat)
from rpython.jit.metainterp.optimizeopt import virtualize
from rpython.jit.metainterp.optimizeopt.intutils import IntUnbounded
from rpython.jit.metainterp.resoperation import rop, ResOperation,\
     AbstractInputArg
from rpython.rlib.debug import debug_start, debug_stop, debug_print
from rpython.rlib.objectmodel import we_are_translated

LEVEL_UNKNOWN = '\x00'
LEVEL_NONNULL = '\x01'
LEVEL_CONSTANT = '\x02'

class BadVirtualState(Exception):
    pass

class VirtualStatesCantMatch(Exception):
    def __init__(self, msg='?', state=None):
        self.msg = msg
        self.state = state

class GenerateGuardState(object):
    def __init__(self, cpu=None, guards=None, renum=None, bad=None):
        self.cpu = cpu
        if guards is None:
            guards = []
        self.extra_guards = guards
        if renum is None:
            renum = {}
        self.renum = renum
        if bad is None:
            bad = {}
        self.bad = bad

class AbstractVirtualStateInfo(object):
    position = -1

    def generate_guards(self, other, value, state):
        """ generate guards (output in the list extra_guards) that make runtime
        values of the shape other match the shape of self. if that's not
        possible, VirtualStatesCantMatch is thrown and bad gets keys set which
        parts of the state are the problem.

        the function can peek into value (and particularly also the boxes in
        the value) as a guiding heuristic whether making such guards makes
        sense. if None is passed in for value, no guard is ever generated, and
        this function degenerates to a generalization check."""
        assert value is None or isinstance(value, OptValue)
        assert self.position != -1
        if self.position in state.renum:
            if state.renum[self.position] != other.position:
                state.bad[self] = state.bad[other] = None
                raise VirtualStatesCantMatch(
                        'The numbering of the virtual states does not ' +
                        'match. This means that two virtual fields ' +
                        'have been set to the same Box in one of the ' +
                        'virtual states but not in the other.',
                        state)
        else:
            state.renum[self.position] = other.position
            try:
                self._generate_guards(other, value, state)
            except VirtualStatesCantMatch, e:
                state.bad[self] = state.bad[other] = None
                if e.state is None:
                    e.state = state
                raise e

    def _generate_guards(self, other, value, state):
        raise VirtualStatesCantMatch(
                'Generating guards for making the VirtualStates ' +
                'at hand match have not been implemented')

    def enum_forced_boxes(self, boxes, value, optimizer):
        raise NotImplementedError

    def enum(self, virtual_state):
        if self.position != -1:
            return
        virtual_state.info_counter += 1
        self.position = virtual_state.info_counter
        self._enum(virtual_state)

    def _enum(self, virtual_state):
        raise NotImplementedError

    def debug_print(self, indent, seen, bad, metainterp_sd):
        mark = ''
        if self in bad:
            mark = '*'
        self.debug_header(indent + mark)
        if self not in seen:
            seen[self] = True
            for s in self.fieldstate:
                s.debug_print(indent + "    ", seen, bad, metainterp_sd)
        else:
            debug_print(indent + "    ...")

    def debug_header(self, indent):
        raise NotImplementedError


class AbstractVirtualStructStateInfo(AbstractVirtualStateInfo):
    def __init__(self, fielddescrs):
        self.fielddescrs = fielddescrs

    def _generate_guards(self, other, value, state):
        if not self._generalization_of_structpart(other):
            raise VirtualStatesCantMatch("different kinds of structs")

        assert isinstance(other, AbstractVirtualStructStateInfo)
        assert len(self.fielddescrs) == len(self.fieldstate)
        assert len(other.fielddescrs) == len(other.fieldstate)
        if value is not None:
            assert isinstance(value, virtualize.AbstractVirtualStructValue)
            assert value.is_virtual()

        if len(self.fielddescrs) != len(other.fielddescrs):
            raise VirtualStatesCantMatch("field descrs don't match")

        for i in range(len(self.fielddescrs)):
            if other.fielddescrs[i] is not self.fielddescrs[i]:
                raise VirtualStatesCantMatch("field descrs don't match")
            if value is not None:
                v = value._fields[self.fielddescrs[i]] # must be there
            else:
                v = None
            self.fieldstate[i].generate_guards(other.fieldstate[i], v, state)


    def _generalization_of_structpart(self, other):
        raise NotImplementedError

    def enum_forced_boxes(self, boxes, value, optimizer):
        if not isinstance(value, virtualize.AbstractVirtualStructValue):
            raise BadVirtualState
        if not value.is_virtual():
            raise BadVirtualState
        for i in range(len(self.fielddescrs)):
            try:
                v = value._fields[self.fielddescrs[i]]
            except KeyError:
                raise BadVirtualState
            s = self.fieldstate[i]
            if s.position > self.position:
                s.enum_forced_boxes(boxes, v, optimizer)

    def _enum(self, virtual_state):
        for s in self.fieldstate:
            s.enum(virtual_state)


class VirtualStateInfo(AbstractVirtualStructStateInfo):
    def __init__(self, known_class, fielddescrs):
        AbstractVirtualStructStateInfo.__init__(self, fielddescrs)
        self.known_class = known_class

    def _generalization_of_structpart(self, other):
        return (isinstance(other, VirtualStateInfo) and
                self.known_class.same_constant(other.known_class))


    def debug_header(self, indent):
        debug_print(indent + 'VirtualStateInfo(%d):' % self.position)


class VStructStateInfo(AbstractVirtualStructStateInfo):
    def __init__(self, typedescr, fielddescrs):
        AbstractVirtualStructStateInfo.__init__(self, fielddescrs)
        self.typedescr = typedescr

    def _generalization_of_structpart(self, other):
        return (isinstance(other, VStructStateInfo) and
                self.typedescr is other.typedescr)

    def debug_header(self, indent):
        debug_print(indent + 'VStructStateInfo(%d):' % self.position)


class VArrayStateInfo(AbstractVirtualStateInfo):

    def __init__(self, arraydescr):
        self.arraydescr = arraydescr

    def _generate_guards(self, other, value, state):
        if not isinstance(other, VArrayStateInfo):
            raise VirtualStatesCantMatch("other is not an array")
        if self.arraydescr is not other.arraydescr:
            raise VirtualStatesCantMatch("other is a different kind of array")
        if len(self.fieldstate) != len(other.fieldstate):
            raise VirtualStatesCantMatch("other has a different length")
        v = None
        for i in range(len(self.fieldstate)):
            if value is not None:
                assert isinstance(value, virtualize.VArrayValue)
                v = value._items[i]
            self.fieldstate[i].generate_guards(other.fieldstate[i],
                                               v, state)

    def enum_forced_boxes(self, boxes, value, optimizer):
        if not isinstance(value, virtualize.VArrayValue):
            raise BadVirtualState
        if not value.is_virtual():
            raise BadVirtualState
        if len(self.fieldstate) > value.getlength():
            raise BadVirtualState
        for i in range(len(self.fieldstate)):
            v = value.get_item_value(i)
            if v is None:
                v = value.get_missing_null_value()
            s = self.fieldstate[i]
            if s.position > self.position:
                s.enum_forced_boxes(boxes, v, optimizer)

    def _enum(self, virtual_state):
        for s in self.fieldstate:
            s.enum(virtual_state)

    def debug_header(self, indent):
        debug_print(indent + 'VArrayStateInfo(%d):' % self.position)


class VArrayStructStateInfo(AbstractVirtualStateInfo):
    def __init__(self, arraydescr, fielddescrs):
        self.arraydescr = arraydescr
        self.fielddescrs = fielddescrs

    def _generate_guards(self, other, value, state):
        if not isinstance(other, VArrayStructStateInfo):
            raise VirtualStatesCantMatch("other is not an VArrayStructStateInfo")
        if self.arraydescr is not other.arraydescr:
            raise VirtualStatesCantMatch("other is a different kind of array")

        if len(self.fielddescrs) != len(other.fielddescrs):
            raise VirtualStatesCantMatch("other has a different length")

        p = 0
        v = None
        for i in range(len(self.fielddescrs)):
            if len(self.fielddescrs[i]) != len(other.fielddescrs[i]):
                raise VirtualStatesCantMatch("other has a different length")
            for j in range(len(self.fielddescrs[i])):
                descr = self.fielddescrs[i][j]
                if descr is not other.fielddescrs[i][j]:
                    raise VirtualStatesCantMatch("other is a different kind of array")
                if value is not None:
                    assert isinstance(value, virtualize.VArrayStructValue)
                    v = value._items[i][descr]
                self.fieldstate[p].generate_guards(other.fieldstate[p],
                                                   v,
                                                   state)
                p += 1

    def _enum(self, virtual_state):
        for s in self.fieldstate:
            s.enum(virtual_state)

    def enum_forced_boxes(self, boxes, value, optimizer):
        if not isinstance(value, virtualize.VArrayStructValue):
            raise BadVirtualState
        if not value.is_virtual():
            raise BadVirtualState
        if len(self.fielddescrs) > len(value._items):
            raise BadVirtualState
        p = 0
        for i in range(len(self.fielddescrs)):
            for j in range(len(self.fielddescrs[i])):
                try:
                    v = value._items[i][self.fielddescrs[i][j]]
                except KeyError:
                    raise BadVirtualState
                s = self.fieldstate[p]
                if s.position > self.position:
                    s.enum_forced_boxes(boxes, v, optimizer)
                p += 1

    def debug_header(self, indent):
        debug_print(indent + 'VArrayStructStateInfo(%d):' % self.position)

class NotVirtualStateInfo(AbstractVirtualStateInfo):
    lenbound = None
    intbound = None
    
    def __init__(self, optimizer, box):
        info = optimizer.getinfo(box)
        if info and info.is_constant():
            self.level = LEVEL_CONSTANT
        elif box.type == 'r' and info and info.is_nonnull():
            self.level = LEVEL_NONNULL
        else:
            self.level = LEVEL_UNKNOWN
        return
        yyy
        self.level = LEVEL_UNKNOWN
        if ptrinfo is not None:
            self.known_class = ptrinfo.get_known_class(cpu)
        return
        xxx
        self.is_opaque = is_opaque
        self.known_class = value.get_known_class()
        self.level = value.getlevel()
        if value.getintbound() is None:
            self.intbound = IntUnbounded()
        else:
            self.intbound = value.getintbound().clone()
        if value.is_constant():
            self.constbox = value.box
        else:
            self.constbox = None
        self.position_in_notvirtuals = -1
        self.lenbound = value.getlenbound()


    def _generate_guards(self, other, value, state):
        if value is None or self.is_opaque:
            box = None # generating guards for opaque pointers isn't safe
        else:
            box = value.box
        # XXX This will always retrace instead of forcing anything which
        # might be what we want sometimes?
        if not isinstance(other, NotVirtualStateInfo):
            raise VirtualStatesCantMatch(
                    'The VirtualStates does not match as a ' +
                    'virtual appears where a pointer is needed ' +
                    'and it is too late to force it.')


        extra_guards = state.extra_guards
        cpu = state.cpu
        if self.lenbound and not self.lenbound.generalization_of(other.lenbound):
            raise VirtualStatesCantMatch("length bound does not match")

        if self.level == LEVEL_UNKNOWN:
            # confusingly enough, this is done also for pointers
            # which have the full range as the "bound", so it always works
            return self._generate_guards_intbounds(other, box, extra_guards)

        # the following conditions often peek into the runtime value that the
        # box had when tracing. This value is only used as an educated guess.
        # It is used here to choose between either emitting a guard and jumping
        # to an existing compiled loop or retracing the loop. Both alternatives
        # will always generate correct behaviour, but performance will differ.
        elif self.level == LEVEL_NONNULL:
            if other.level == LEVEL_UNKNOWN:
                if box is not None and box.nonnull():
                    op = ResOperation(rop.GUARD_NONNULL, [box], None)
                    extra_guards.append(op)
                    return
                else:
                    raise VirtualStatesCantMatch("other not known to be nonnull")
            elif other.level == LEVEL_NONNULL:
                return
            elif other.level == LEVEL_KNOWNCLASS:
                return # implies nonnull
            else:
                assert other.level == LEVEL_CONSTANT
                assert other.constbox
                if not other.constbox.nonnull():
                    raise VirtualStatesCantMatch("constant is null")
                return

        elif self.level == LEVEL_KNOWNCLASS:
            if other.level == LEVEL_UNKNOWN:
                if (box and box.nonnull() and
                        self.known_class.same_constant(cpu.ts.cls_of_box(box))):
                    op = ResOperation(rop.GUARD_NONNULL_CLASS, [box, self.known_class], None)
                    extra_guards.append(op)
                    return
                else:
                    raise VirtualStatesCantMatch("other's class is unknown")
            elif other.level == LEVEL_NONNULL:
                if box and self.known_class.same_constant(cpu.ts.cls_of_box(box)):
                    op = ResOperation(rop.GUARD_CLASS, [box, self.known_class], None)
                    extra_guards.append(op)
                    return
                else:
                    raise VirtualStatesCantMatch("other's class is unknown")
            elif other.level == LEVEL_KNOWNCLASS:
                if self.known_class.same_constant(other.known_class):
                    return
                raise VirtualStatesCantMatch("classes don't match")
            else:
                assert other.level == LEVEL_CONSTANT
                if (other.constbox.nonnull() and
                        self.known_class.same_constant(cpu.ts.cls_of_box(other.constbox))):
                    return
                else:
                    raise VirtualStatesCantMatch("classes don't match")

        else:
            assert self.level == LEVEL_CONSTANT
            if other.level == LEVEL_CONSTANT:
                if self.constbox.same_constant(other.constbox):
                    return
                raise VirtualStatesCantMatch("different constants")
            if box is not None and self.constbox.same_constant(box.constbox()):
                op = ResOperation(rop.GUARD_VALUE, [box, self.constbox], None)
                extra_guards.append(op)
                return
            else:
                raise VirtualStatesCantMatch("other not constant")
        assert 0, "unreachable"

    def _generate_guards_intbounds(self, other, box, extra_guards):
        if self.intbound is None:
            return
        if self.intbound.contains_bound(other.intbound):
            return
        xxx
        if (box is not None and isinstance(box, BoxInt) and
                self.intbound.contains(box.getint())):
            # this may generate a few more guards than needed, but they are
            # optimized away when emitting them
            self.intbound.make_guards(box, extra_guards)
            return
        raise VirtualStatesCantMatch("intbounds don't match")

    def enum_forced_boxes(self, boxes, value, optimizer):
        if self.level == LEVEL_CONSTANT:
            return
        assert 0 <= self.position_in_notvirtuals
        if optimizer:
            box = value.force_box(optimizer)
        else:
            if value.is_virtual():
                raise BadVirtualState
            box = value.get_key_box()
        boxes[self.position_in_notvirtuals] = box

    def _enum(self, virtual_state):
        if self.level == LEVEL_CONSTANT:
            return
        self.position_in_notvirtuals = virtual_state.numnotvirtuals
        virtual_state.numnotvirtuals += 1

    def debug_print(self, indent, seen, bad, metainterp_sd=None):
        mark = ''
        if self in bad:
            mark = '*'
        if self.level == LEVEL_UNKNOWN:
            l = "Unknown"
        elif self.level == LEVEL_NONNULL:
            l = "NonNull"
        elif self.level == LEVEL_KNOWNCLASS:
            addr = self.known_class.getaddr()
            if metainterp_sd:
                name = metainterp_sd.get_name_from_address(addr)
            else:
                name = "?"
            l = "KnownClass(%s)" % name
        else:
            assert self.level == LEVEL_CONSTANT
            const = self.constbox
            if isinstance(const, ConstInt):
                l = "ConstInt(%s)" % (const.value, )
            elif isinstance(const, ConstPtr):
                if const.value:
                    l = "ConstPtr"
                else:
                    l = "ConstPtr(null)"
            else:
                assert isinstance(const, ConstFloat)
                l = "ConstFloat(%s)" % const.getfloat()

        lb = ''
        if self.lenbound:
            lb = ', ' + self.lenbound.bound.__repr__()

        debug_print(indent + mark + 'NotVirtualInfo(%d' % self.position +
                    ', ' + l + ', ' + self.intbound.__repr__() + lb + ')')


class VirtualState(object):
    def __init__(self, state):
        self.state = state
        self.info_counter = -1
        self.numnotvirtuals = 0
        for s in state:
            if s:
                s.enum(self)

    def generalization_of(self, other, bad=None, cpu=None):
        state = GenerateGuardState(cpu=cpu, bad=bad)
        assert len(self.state) == len(other.state)
        try:
            for i in range(len(self.state)):
                self.state[i].generate_guards(other.state[i], None, state)
        except VirtualStatesCantMatch:
            return False
        return True

    def generate_guards(self, other, values, cpu):
        assert len(self.state) == len(other.state) == len(values)
        state = GenerateGuardState(cpu)
        for i in range(len(self.state)):
            self.state[i].generate_guards(other.state[i], values[i],
                                          state)
        return state

    def make_inputargs(self, inputargs, optimizer, keyboxes=False):
        if optimizer.optearlyforce:
            optimizer = optimizer.optearlyforce
        assert len(inputargs) == len(self.state)
        inpargs = []
        for i, state in enumerate(self.state):
            if state.level != LEVEL_CONSTANT:
                inpargs.append(inputargs[i])
        return inpargs
        inputargs = [None] * self.numnotvirtuals

        # We try twice. The first time around we allow boxes to be forced
        # which might change the virtual state if the box appear in more
        # than one place among the inputargs.
        for i in range(len(values)):
            self.state[i].enum_forced_boxes(inputargs, values[i], optimizer)
        for i in range(len(values)):
            self.state[i].enum_forced_boxes(inputargs, values[i], None)

        if keyboxes:
            for i in range(len(values)):
                if not isinstance(self.state[i], NotVirtualStateInfo):
                    box = values[i].get_key_box()
                    assert not isinstance(box, Const)
                    inputargs.append(box)

        assert None not in inputargs

        return inputargs

    def debug_print(self, hdr='', bad=None, metainterp_sd=None):
        if bad is None:
            bad = {}
        debug_print(hdr + "VirtualState():")
        seen = {}
        for s in self.state:
            s.debug_print("    ", seen, bad, metainterp_sd)


class VirtualStateConstructor(VirtualVisitor):

    def __init__(self, optimizer):
        self.fieldboxes = {}
        self.optimizer = optimizer
        self.info = {}

    def register_virtual_fields(self, keybox, fieldboxes):
        self.fieldboxes[keybox] = fieldboxes

    def already_seen_virtual(self, keybox):
        return keybox in self.fieldboxes

    def getvalue(self, box):
        return self.optimizer.getvalue(box)

    def state(self, box):
        if box.type == 'r':
            xxxx
        return None
        value = self.getvalue(box)
        box = value.get_key_box()
        try:
            info = self.info[box]
        except KeyError:
            self.info[box] = info = value.visitor_dispatch_virtual_type(self)
            if value.is_virtual():
                flds = self.fieldboxes[box]
                info.fieldstate = [self.state_or_none(b, value) for b in flds]
        return info

    def state_or_none(self, box, value):
        if box is None:
            box = value.get_missing_null_value().box
        return self.state(box)

    def get_virtual_state(self, jump_args):
        self.optimizer.force_at_end_of_preamble()
        already_forced = {}
        if self.optimizer.optearlyforce:
            opt = self.optimizer.optearlyforce
        else:
            opt = self.optimizer
        state = []
        for box in jump_args:
            box = opt.get_box_replacement(box)
            if box.type == 'r':
                info = opt.getptrinfo(box)
                if info is not None and info.is_virtual():
                    xxx
                else:
                    state.append(self.visit_not_virtual(box))
            elif box.type == 'i':
                intbound = opt.getintbound(box)
                state.append(self.visit_not_virtual(box))
            else:
                xxx
        #values = [self.getvalue(box).force_at_end_of_preamble(already_forced,
        #                                                      opt)
        #          for box in jump_args]

        return VirtualState(state)

    def visit_not_virtual(self, box):
        is_opaque = box in self.optimizer.opaque_pointers
        return NotVirtualStateInfo(self.optimizer, box)

    def visit_virtual(self, known_class, fielddescrs):
        return VirtualStateInfo(known_class, fielddescrs)

    def visit_vstruct(self, typedescr, fielddescrs):
        return VStructStateInfo(typedescr, fielddescrs)

    def visit_varray(self, arraydescr, clear):
        # 'clear' is ignored here.  I *think* it is correct, because so
        # far in force_at_end_of_preamble() we force all array values
        # to be non-None, so clearing is not important any more
        return VArrayStateInfo(arraydescr)

    def visit_varraystruct(self, arraydescr, fielddescrs):
        return VArrayStructStateInfo(arraydescr, fielddescrs)

