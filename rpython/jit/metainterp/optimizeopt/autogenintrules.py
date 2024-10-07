# Generated by ruleopt/generate.py, don't edit!

from rpython.jit.metainterp.history import ConstInt
from rpython.jit.metainterp.optimizeopt.util import (
    get_box_replacement)
from rpython.jit.metainterp.resoperation import rop

from rpython.rlib.rarithmetic import LONG_BIT, r_uint, intmask, ovfcheck, uint_mul_high, highest_bit

class OptIntAutoGenerated(object):
    _all_rules_fired = []
    _rule_names_int_add = ['add_reassoc_consts', 'add_zero']
    _rule_fired_int_add = [0] * 2
    _all_rules_fired.append((_rule_names_int_add, _rule_fired_int_add))
    def optimize_INT_ADD(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_1 = get_box_replacement(op.getarg(1))
        b_arg_1 = self.getintbound(arg_1)
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # add_zero: int_add(0, x) => x
            if C_arg_0 == 0:
                self.make_equal_to(op, arg_1)
                self._rule_fired_int_add[1] += 1
                return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # add_zero: int_add(x, 0) => x
            if C_arg_1 == 0:
                self.make_equal_to(op, arg_0)
                self._rule_fired_int_add[1] += 1
                return
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            arg_1_int_add = self.optimizer.as_operation(arg_1, rop.INT_ADD)
            if arg_1_int_add is not None:
                arg_1_0 = get_box_replacement(arg_1_int_add.getarg(0))
                b_arg_1_0 = self.getintbound(arg_1_0)
                arg_1_1 = get_box_replacement(arg_1_int_add.getarg(1))
                b_arg_1_1 = self.getintbound(arg_1_1)
                if b_arg_1_0.is_constant():
                    C_arg_1_0 = b_arg_1_0.get_constant_int()
                    # add_reassoc_consts: int_add(C2, int_add(C1, x)) => int_add(x, C)
                    C = intmask(r_uint(C_arg_1_0) + r_uint(C_arg_0))
                    newop = self.replace_op_with(op, rop.INT_ADD, args=[arg_1_1, ConstInt(C)])
                    self.optimizer.send_extra_operation(newop)
                    self._rule_fired_int_add[0] += 1
                    return
                if b_arg_1_1.is_constant():
                    C_arg_1_1 = b_arg_1_1.get_constant_int()
                    # add_reassoc_consts: int_add(C2, int_add(x, C1)) => int_add(x, C)
                    C = intmask(r_uint(C_arg_1_1) + r_uint(C_arg_0))
                    newop = self.replace_op_with(op, rop.INT_ADD, args=[arg_1_0, ConstInt(C)])
                    self.optimizer.send_extra_operation(newop)
                    self._rule_fired_int_add[0] += 1
                    return
        else:
            arg_0_int_add = self.optimizer.as_operation(arg_0, rop.INT_ADD)
            if arg_0_int_add is not None:
                arg_0_0 = get_box_replacement(arg_0_int_add.getarg(0))
                b_arg_0_0 = self.getintbound(arg_0_0)
                arg_0_1 = get_box_replacement(arg_0_int_add.getarg(1))
                b_arg_0_1 = self.getintbound(arg_0_1)
                if b_arg_0_0.is_constant():
                    C_arg_0_0 = b_arg_0_0.get_constant_int()
                    if b_arg_1.is_constant():
                        C_arg_1 = b_arg_1.get_constant_int()
                        # add_reassoc_consts: int_add(int_add(C1, x), C2) => int_add(x, C)
                        C = intmask(r_uint(C_arg_0_0) + r_uint(C_arg_1))
                        newop = self.replace_op_with(op, rop.INT_ADD, args=[arg_0_1, ConstInt(C)])
                        self.optimizer.send_extra_operation(newop)
                        self._rule_fired_int_add[0] += 1
                        return
                if b_arg_0_1.is_constant():
                    C_arg_0_1 = b_arg_0_1.get_constant_int()
                    if b_arg_1.is_constant():
                        C_arg_1 = b_arg_1.get_constant_int()
                        # add_reassoc_consts: int_add(int_add(x, C1), C2) => int_add(x, C)
                        C = intmask(r_uint(C_arg_0_1) + r_uint(C_arg_1))
                        newop = self.replace_op_with(op, rop.INT_ADD, args=[arg_0_0, ConstInt(C)])
                        self.optimizer.send_extra_operation(newop)
                        self._rule_fired_int_add[0] += 1
                        return
        return self.emit(op)
    _rule_names_int_sub = ['sub_zero', 'sub_from_zero', 'sub_x_x', 'sub_add_consts', 'sub_add']
    _rule_fired_int_sub = [0] * 5
    _all_rules_fired.append((_rule_names_int_sub, _rule_fired_int_sub))
    def optimize_INT_SUB(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_1 = get_box_replacement(op.getarg(1))
        b_arg_1 = self.getintbound(arg_1)
        # sub_x_x: int_sub(x, x) => 0
        if arg_1 is arg_0:
            self.make_constant_int(op, 0)
            self._rule_fired_int_sub[2] += 1
            return
        arg_0_int_add = self.optimizer.as_operation(arg_0, rop.INT_ADD)
        if arg_0_int_add is not None:
            arg_0_0 = get_box_replacement(arg_0_int_add.getarg(0))
            b_arg_0_0 = self.getintbound(arg_0_0)
            arg_0_1 = get_box_replacement(arg_0_int_add.getarg(1))
            b_arg_0_1 = self.getintbound(arg_0_1)
            # sub_add: int_sub(int_add(x, y), y) => x
            if arg_1 is arg_0_1:
                self.make_equal_to(op, arg_0_0)
                self._rule_fired_int_sub[4] += 1
                return
            # sub_add: int_sub(int_add(y, x), y) => x
            if arg_1 is arg_0_0:
                self.make_equal_to(op, arg_0_1)
                self._rule_fired_int_sub[4] += 1
                return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # sub_zero: int_sub(x, 0) => x
            if C_arg_1 == 0:
                self.make_equal_to(op, arg_0)
                self._rule_fired_int_sub[0] += 1
                return
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # sub_from_zero: int_sub(0, x) => int_neg(x)
            if C_arg_0 == 0:
                newop = self.replace_op_with(op, rop.INT_NEG, args=[arg_1])
                self.optimizer.send_extra_operation(newop)
                self._rule_fired_int_sub[1] += 1
                return
        else:
            arg_0_int_add = self.optimizer.as_operation(arg_0, rop.INT_ADD)
            if arg_0_int_add is not None:
                arg_0_0 = get_box_replacement(arg_0_int_add.getarg(0))
                b_arg_0_0 = self.getintbound(arg_0_0)
                arg_0_1 = get_box_replacement(arg_0_int_add.getarg(1))
                b_arg_0_1 = self.getintbound(arg_0_1)
                if b_arg_0_0.is_constant():
                    C_arg_0_0 = b_arg_0_0.get_constant_int()
                    if b_arg_1.is_constant():
                        C_arg_1 = b_arg_1.get_constant_int()
                        # sub_add_consts: int_sub(int_add(C1, x), C2) => int_sub(x, C)
                        C = intmask(r_uint(C_arg_1) - r_uint(C_arg_0_0))
                        newop = self.replace_op_with(op, rop.INT_SUB, args=[arg_0_1, ConstInt(C)])
                        self.optimizer.send_extra_operation(newop)
                        self._rule_fired_int_sub[3] += 1
                        return
                if b_arg_0_1.is_constant():
                    C_arg_0_1 = b_arg_0_1.get_constant_int()
                    if b_arg_1.is_constant():
                        C_arg_1 = b_arg_1.get_constant_int()
                        # sub_add_consts: int_sub(int_add(x, C1), C2) => int_sub(x, C)
                        C = intmask(r_uint(C_arg_1) - r_uint(C_arg_0_1))
                        newop = self.replace_op_with(op, rop.INT_SUB, args=[arg_0_0, ConstInt(C)])
                        self.optimizer.send_extra_operation(newop)
                        self._rule_fired_int_sub[3] += 1
                        return
        return self.emit(op)
    _rule_names_int_mul = ['mul_zero', 'mul_one', 'mul_minus_one', 'mul_pow2_const', 'mul_lshift']
    _rule_fired_int_mul = [0] * 5
    _all_rules_fired.append((_rule_names_int_mul, _rule_fired_int_mul))
    def optimize_INT_MUL(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_1 = get_box_replacement(op.getarg(1))
        b_arg_1 = self.getintbound(arg_1)
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # mul_zero: int_mul(0, x) => 0
            if C_arg_0 == 0:
                self.make_constant_int(op, 0)
                self._rule_fired_int_mul[0] += 1
                return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # mul_zero: int_mul(x, 0) => 0
            if C_arg_1 == 0:
                self.make_constant_int(op, 0)
                self._rule_fired_int_mul[0] += 1
                return
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # mul_one: int_mul(1, x) => x
            if C_arg_0 == 1:
                self.make_equal_to(op, arg_1)
                self._rule_fired_int_mul[1] += 1
                return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # mul_one: int_mul(x, 1) => x
            if C_arg_1 == 1:
                self.make_equal_to(op, arg_0)
                self._rule_fired_int_mul[1] += 1
                return
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # mul_minus_one: int_mul(-1, x) => int_neg(x)
            if C_arg_0 == -1:
                newop = self.replace_op_with(op, rop.INT_NEG, args=[arg_1])
                self.optimizer.send_extra_operation(newop)
                self._rule_fired_int_mul[2] += 1
                return
            # mul_pow2_const: int_mul(C, x) => int_lshift(x, shift)
            if C_arg_0 > 0 and C_arg_0 & intmask(r_uint(C_arg_0) - r_uint(1)) == 0:
                shift = highest_bit(C_arg_0)
                newop = self.replace_op_with(op, rop.INT_LSHIFT, args=[arg_1, ConstInt(shift)])
                self.optimizer.send_extra_operation(newop)
                self._rule_fired_int_mul[3] += 1
                return
        else:
            arg_0_int_lshift = self.optimizer.as_operation(arg_0, rop.INT_LSHIFT)
            if arg_0_int_lshift is not None:
                arg_0_0 = get_box_replacement(arg_0_int_lshift.getarg(0))
                b_arg_0_0 = self.getintbound(arg_0_0)
                arg_0_1 = get_box_replacement(arg_0_int_lshift.getarg(1))
                b_arg_0_1 = self.getintbound(arg_0_1)
                if b_arg_0_0.is_constant():
                    C_arg_0_0 = b_arg_0_0.get_constant_int()
                    # mul_lshift: int_mul(int_lshift(1, y), x) => int_lshift(x, y)
                    if C_arg_0_0 == 1:
                        if b_arg_0_1.known_ge_const(0) and b_arg_0_1.known_le_const(LONG_BIT):
                            newop = self.replace_op_with(op, rop.INT_LSHIFT, args=[arg_1, arg_0_1])
                            self.optimizer.send_extra_operation(newop)
                            self._rule_fired_int_mul[4] += 1
                            return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # mul_minus_one: int_mul(x, -1) => int_neg(x)
            if C_arg_1 == -1:
                newop = self.replace_op_with(op, rop.INT_NEG, args=[arg_0])
                self.optimizer.send_extra_operation(newop)
                self._rule_fired_int_mul[2] += 1
                return
            # mul_pow2_const: int_mul(x, C) => int_lshift(x, shift)
            if C_arg_1 > 0 and C_arg_1 & intmask(r_uint(C_arg_1) - r_uint(1)) == 0:
                shift = highest_bit(C_arg_1)
                newop = self.replace_op_with(op, rop.INT_LSHIFT, args=[arg_0, ConstInt(shift)])
                self.optimizer.send_extra_operation(newop)
                self._rule_fired_int_mul[3] += 1
                return
        else:
            arg_1_int_lshift = self.optimizer.as_operation(arg_1, rop.INT_LSHIFT)
            if arg_1_int_lshift is not None:
                arg_1_0 = get_box_replacement(arg_1_int_lshift.getarg(0))
                b_arg_1_0 = self.getintbound(arg_1_0)
                arg_1_1 = get_box_replacement(arg_1_int_lshift.getarg(1))
                b_arg_1_1 = self.getintbound(arg_1_1)
                if b_arg_1_0.is_constant():
                    C_arg_1_0 = b_arg_1_0.get_constant_int()
                    # mul_lshift: int_mul(x, int_lshift(1, y)) => int_lshift(x, y)
                    if C_arg_1_0 == 1:
                        if b_arg_1_1.known_ge_const(0) and b_arg_1_1.known_le_const(LONG_BIT):
                            newop = self.replace_op_with(op, rop.INT_LSHIFT, args=[arg_0, arg_1_1])
                            self.optimizer.send_extra_operation(newop)
                            self._rule_fired_int_mul[4] += 1
                            return
        return self.emit(op)
    _rule_names_int_and = ['and_zero', 'and_x_x', 'and_minus_1', 'and_reassoc_consts', 'and_x_c_in_range', 'and_x_y_covered_ones', 'and_known_result']
    _rule_fired_int_and = [0] * 7
    _all_rules_fired.append((_rule_names_int_and, _rule_fired_int_and))
    def optimize_INT_AND(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_1 = get_box_replacement(op.getarg(1))
        b_arg_1 = self.getintbound(arg_1)
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # and_zero: int_and(0, a) => 0
            if C_arg_0 == 0:
                self.make_constant_int(op, 0)
                self._rule_fired_int_and[0] += 1
                return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # and_zero: int_and(a, 0) => 0
            if C_arg_1 == 0:
                self.make_constant_int(op, 0)
                self._rule_fired_int_and[0] += 1
                return
        # and_known_result: int_and(a, b) => C
        if b_arg_0.and_bound(b_arg_1).is_constant():
            C = b_arg_0.and_bound(b_arg_1).get_constant_int()
            self.make_equal_to(op, ConstInt(C))
            self._rule_fired_int_and[6] += 1
            return
        # and_known_result: int_and(b, a) => C
        if b_arg_1.and_bound(b_arg_0).is_constant():
            C = b_arg_1.and_bound(b_arg_0).get_constant_int()
            self.make_equal_to(op, ConstInt(C))
            self._rule_fired_int_and[6] += 1
            return
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # and_minus_1: int_and(-1, x) => x
            if C_arg_0 == -1:
                self.make_equal_to(op, arg_1)
                self._rule_fired_int_and[2] += 1
                return
            # and_x_c_in_range: int_and(C, x) => x
            if b_arg_1.lower >= 0 and b_arg_1.upper <= C_arg_0 & ~intmask(r_uint(C_arg_0) + r_uint(1)):
                self.make_equal_to(op, arg_1)
                self._rule_fired_int_and[4] += 1
                return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # and_minus_1: int_and(x, -1) => x
            if C_arg_1 == -1:
                self.make_equal_to(op, arg_0)
                self._rule_fired_int_and[2] += 1
                return
            # and_x_c_in_range: int_and(x, C) => x
            if b_arg_0.lower >= 0 and b_arg_0.upper <= C_arg_1 & ~intmask(r_uint(C_arg_1) + r_uint(1)):
                self.make_equal_to(op, arg_0)
                self._rule_fired_int_and[4] += 1
                return
        # and_x_x: int_and(a, a) => a
        if arg_1 is arg_0:
            self.make_equal_to(op, arg_0)
            self._rule_fired_int_and[1] += 1
            return
        # and_x_y_covered_ones: int_and(x, y) => x
        if ~b_arg_1.tvalue & (b_arg_0.tmask | b_arg_0.tvalue) == 0:
            self.make_equal_to(op, arg_0)
            self._rule_fired_int_and[5] += 1
            return
        # and_x_y_covered_ones: int_and(y, x) => x
        if ~b_arg_0.tvalue & (b_arg_1.tmask | b_arg_1.tvalue) == 0:
            self.make_equal_to(op, arg_1)
            self._rule_fired_int_and[5] += 1
            return
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            arg_1_int_and = self.optimizer.as_operation(arg_1, rop.INT_AND)
            if arg_1_int_and is not None:
                arg_1_0 = get_box_replacement(arg_1_int_and.getarg(0))
                b_arg_1_0 = self.getintbound(arg_1_0)
                arg_1_1 = get_box_replacement(arg_1_int_and.getarg(1))
                b_arg_1_1 = self.getintbound(arg_1_1)
                if b_arg_1_0.is_constant():
                    C_arg_1_0 = b_arg_1_0.get_constant_int()
                    # and_reassoc_consts: int_and(C2, int_and(C1, x)) => int_and(x, C)
                    C = C_arg_1_0 & C_arg_0
                    newop = self.replace_op_with(op, rop.INT_AND, args=[arg_1_1, ConstInt(C)])
                    self.optimizer.send_extra_operation(newop)
                    self._rule_fired_int_and[3] += 1
                    return
                if b_arg_1_1.is_constant():
                    C_arg_1_1 = b_arg_1_1.get_constant_int()
                    # and_reassoc_consts: int_and(C2, int_and(x, C1)) => int_and(x, C)
                    C = C_arg_1_1 & C_arg_0
                    newop = self.replace_op_with(op, rop.INT_AND, args=[arg_1_0, ConstInt(C)])
                    self.optimizer.send_extra_operation(newop)
                    self._rule_fired_int_and[3] += 1
                    return
        else:
            arg_0_int_and = self.optimizer.as_operation(arg_0, rop.INT_AND)
            if arg_0_int_and is not None:
                arg_0_0 = get_box_replacement(arg_0_int_and.getarg(0))
                b_arg_0_0 = self.getintbound(arg_0_0)
                arg_0_1 = get_box_replacement(arg_0_int_and.getarg(1))
                b_arg_0_1 = self.getintbound(arg_0_1)
                if b_arg_0_0.is_constant():
                    C_arg_0_0 = b_arg_0_0.get_constant_int()
                    if b_arg_1.is_constant():
                        C_arg_1 = b_arg_1.get_constant_int()
                        # and_reassoc_consts: int_and(int_and(C1, x), C2) => int_and(x, C)
                        C = C_arg_0_0 & C_arg_1
                        newop = self.replace_op_with(op, rop.INT_AND, args=[arg_0_1, ConstInt(C)])
                        self.optimizer.send_extra_operation(newop)
                        self._rule_fired_int_and[3] += 1
                        return
                if b_arg_0_1.is_constant():
                    C_arg_0_1 = b_arg_0_1.get_constant_int()
                    if b_arg_1.is_constant():
                        C_arg_1 = b_arg_1.get_constant_int()
                        # and_reassoc_consts: int_and(int_and(x, C1), C2) => int_and(x, C)
                        C = C_arg_0_1 & C_arg_1
                        newop = self.replace_op_with(op, rop.INT_AND, args=[arg_0_0, ConstInt(C)])
                        self.optimizer.send_extra_operation(newop)
                        self._rule_fired_int_and[3] += 1
                        return
        return self.emit(op)
    _rule_names_int_or = ['or_minus_1', 'or_zero', 'or_x_x', 'or_known_result']
    _rule_fired_int_or = [0] * 4
    _all_rules_fired.append((_rule_names_int_or, _rule_fired_int_or))
    def optimize_INT_OR(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_1 = get_box_replacement(op.getarg(1))
        b_arg_1 = self.getintbound(arg_1)
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # or_minus_1: int_or(-1, x) => -1
            if C_arg_0 == -1:
                self.make_constant_int(op, -1)
                self._rule_fired_int_or[0] += 1
                return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # or_minus_1: int_or(x, -1) => -1
            if C_arg_1 == -1:
                self.make_constant_int(op, -1)
                self._rule_fired_int_or[0] += 1
                return
        # or_known_result: int_or(a, b) => C
        if b_arg_0.or_bound(b_arg_1).is_constant():
            C = b_arg_0.or_bound(b_arg_1).get_constant_int()
            self.make_equal_to(op, ConstInt(C))
            self._rule_fired_int_or[3] += 1
            return
        # or_known_result: int_or(b, a) => C
        if b_arg_1.or_bound(b_arg_0).is_constant():
            C = b_arg_1.or_bound(b_arg_0).get_constant_int()
            self.make_equal_to(op, ConstInt(C))
            self._rule_fired_int_or[3] += 1
            return
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # or_zero: int_or(0, x) => x
            if C_arg_0 == 0:
                self.make_equal_to(op, arg_1)
                self._rule_fired_int_or[1] += 1
                return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # or_zero: int_or(x, 0) => x
            if C_arg_1 == 0:
                self.make_equal_to(op, arg_0)
                self._rule_fired_int_or[1] += 1
                return
        # or_x_x: int_or(a, a) => a
        if arg_1 is arg_0:
            self.make_equal_to(op, arg_0)
            self._rule_fired_int_or[2] += 1
            return
        return self.emit(op)
    _rule_names_int_xor = ['xor_x_x', 'xor_absorb', 'xor_zero', 'xor_minus_1']
    _rule_fired_int_xor = [0] * 4
    _all_rules_fired.append((_rule_names_int_xor, _rule_fired_int_xor))
    def optimize_INT_XOR(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_1 = get_box_replacement(op.getarg(1))
        b_arg_1 = self.getintbound(arg_1)
        # xor_x_x: int_xor(a, a) => 0
        if arg_1 is arg_0:
            self.make_constant_int(op, 0)
            self._rule_fired_int_xor[0] += 1
            return
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # xor_zero: int_xor(0, a) => a
            if C_arg_0 == 0:
                self.make_equal_to(op, arg_1)
                self._rule_fired_int_xor[2] += 1
                return
        else:
            arg_0_int_xor = self.optimizer.as_operation(arg_0, rop.INT_XOR)
            if arg_0_int_xor is not None:
                arg_0_0 = get_box_replacement(arg_0_int_xor.getarg(0))
                b_arg_0_0 = self.getintbound(arg_0_0)
                arg_0_1 = get_box_replacement(arg_0_int_xor.getarg(1))
                b_arg_0_1 = self.getintbound(arg_0_1)
                # xor_absorb: int_xor(int_xor(a, b), b) => a
                if arg_1 is arg_0_1:
                    self.make_equal_to(op, arg_0_0)
                    self._rule_fired_int_xor[1] += 1
                    return
                # xor_absorb: int_xor(int_xor(b, a), b) => a
                if arg_1 is arg_0_0:
                    self.make_equal_to(op, arg_0_1)
                    self._rule_fired_int_xor[1] += 1
                    return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # xor_zero: int_xor(a, 0) => a
            if C_arg_1 == 0:
                self.make_equal_to(op, arg_0)
                self._rule_fired_int_xor[2] += 1
                return
        else:
            arg_1_int_xor = self.optimizer.as_operation(arg_1, rop.INT_XOR)
            if arg_1_int_xor is not None:
                arg_1_0 = get_box_replacement(arg_1_int_xor.getarg(0))
                b_arg_1_0 = self.getintbound(arg_1_0)
                arg_1_1 = get_box_replacement(arg_1_int_xor.getarg(1))
                b_arg_1_1 = self.getintbound(arg_1_1)
                # xor_absorb: int_xor(b, int_xor(a, b)) => a
                if arg_1_1 is arg_0:
                    self.make_equal_to(op, arg_1_0)
                    self._rule_fired_int_xor[1] += 1
                    return
                # xor_absorb: int_xor(b, int_xor(b, a)) => a
                if arg_1_0 is arg_0:
                    self.make_equal_to(op, arg_1_1)
                    self._rule_fired_int_xor[1] += 1
                    return
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # xor_minus_1: int_xor(-1, x) => int_invert(x)
            if C_arg_0 == -1:
                newop = self.replace_op_with(op, rop.INT_INVERT, args=[arg_1])
                self.optimizer.send_extra_operation(newop)
                self._rule_fired_int_xor[3] += 1
                return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # xor_minus_1: int_xor(x, -1) => int_invert(x)
            if C_arg_1 == -1:
                newop = self.replace_op_with(op, rop.INT_INVERT, args=[arg_0])
                self.optimizer.send_extra_operation(newop)
                self._rule_fired_int_xor[3] += 1
                return
        return self.emit(op)
    _rule_names_int_lshift = ['lshift_zero_x', 'lshift_x_zero', 'lshift_rshift_c_c', 'lshift_urshift_c_c']
    _rule_fired_int_lshift = [0] * 4
    _all_rules_fired.append((_rule_names_int_lshift, _rule_fired_int_lshift))
    def optimize_INT_LSHIFT(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_1 = get_box_replacement(op.getarg(1))
        b_arg_1 = self.getintbound(arg_1)
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # lshift_zero_x: int_lshift(0, x) => 0
            if C_arg_0 == 0:
                self.make_constant_int(op, 0)
                self._rule_fired_int_lshift[0] += 1
                return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # lshift_x_zero: int_lshift(x, 0) => x
            if C_arg_1 == 0:
                self.make_equal_to(op, arg_0)
                self._rule_fired_int_lshift[1] += 1
                return
        arg_0_int_rshift = self.optimizer.as_operation(arg_0, rop.INT_RSHIFT)
        if arg_0_int_rshift is not None:
            arg_0_0 = get_box_replacement(arg_0_int_rshift.getarg(0))
            b_arg_0_0 = self.getintbound(arg_0_0)
            arg_0_1 = get_box_replacement(arg_0_int_rshift.getarg(1))
            b_arg_0_1 = self.getintbound(arg_0_1)
            if b_arg_0_1.is_constant():
                C_arg_0_1 = b_arg_0_1.get_constant_int()
                if b_arg_1.is_constant():
                    C_arg_1 = b_arg_1.get_constant_int()
                    # lshift_rshift_c_c: int_lshift(int_rshift(x, C1), C1) => int_and(x, C)
                    if C_arg_1 == C_arg_0_1:
                        if 0 <= C_arg_0_1 and C_arg_0_1 < LONG_BIT:
                            C = -1 >> C_arg_0_1 << C_arg_0_1
                            newop = self.replace_op_with(op, rop.INT_AND, args=[arg_0_0, ConstInt(C)])
                            self.optimizer.send_extra_operation(newop)
                            self._rule_fired_int_lshift[2] += 1
                            return
        else:
            arg_0_uint_rshift = self.optimizer.as_operation(arg_0, rop.UINT_RSHIFT)
            if arg_0_uint_rshift is not None:
                arg_0_0 = get_box_replacement(arg_0_uint_rshift.getarg(0))
                b_arg_0_0 = self.getintbound(arg_0_0)
                arg_0_1 = get_box_replacement(arg_0_uint_rshift.getarg(1))
                b_arg_0_1 = self.getintbound(arg_0_1)
                if b_arg_0_1.is_constant():
                    C_arg_0_1 = b_arg_0_1.get_constant_int()
                    if b_arg_1.is_constant():
                        C_arg_1 = b_arg_1.get_constant_int()
                        # lshift_urshift_c_c: int_lshift(uint_rshift(x, C1), C1) => int_and(x, C)
                        if C_arg_1 == C_arg_0_1:
                            if 0 <= C_arg_0_1 and C_arg_0_1 < LONG_BIT:
                                C = -1 >> C_arg_0_1 << C_arg_0_1
                                newop = self.replace_op_with(op, rop.INT_AND, args=[arg_0_0, ConstInt(C)])
                                self.optimizer.send_extra_operation(newop)
                                self._rule_fired_int_lshift[3] += 1
                                return
        return self.emit(op)
    _rule_names_int_rshift = ['rshift_zero_x', 'rshift_x_zero', 'rshift_known_result']
    _rule_fired_int_rshift = [0] * 3
    _all_rules_fired.append((_rule_names_int_rshift, _rule_fired_int_rshift))
    def optimize_INT_RSHIFT(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_1 = get_box_replacement(op.getarg(1))
        b_arg_1 = self.getintbound(arg_1)
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # rshift_zero_x: int_rshift(0, x) => 0
            if C_arg_0 == 0:
                self.make_constant_int(op, 0)
                self._rule_fired_int_rshift[0] += 1
                return
        # rshift_known_result: int_rshift(a, b) => C
        if b_arg_0.rshift_bound(b_arg_1).is_constant():
            C = b_arg_0.rshift_bound(b_arg_1).get_constant_int()
            self.make_equal_to(op, ConstInt(C))
            self._rule_fired_int_rshift[2] += 1
            return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # rshift_x_zero: int_rshift(x, 0) => x
            if C_arg_1 == 0:
                self.make_equal_to(op, arg_0)
                self._rule_fired_int_rshift[1] += 1
                return
        return self.emit(op)
    _rule_names_uint_rshift = ['urshift_zero_x', 'urshift_x_zero', 'urshift_known_result', 'urshift_lshift_x_c_c']
    _rule_fired_uint_rshift = [0] * 4
    _all_rules_fired.append((_rule_names_uint_rshift, _rule_fired_uint_rshift))
    def optimize_UINT_RSHIFT(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_1 = get_box_replacement(op.getarg(1))
        b_arg_1 = self.getintbound(arg_1)
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # urshift_zero_x: uint_rshift(0, x) => 0
            if C_arg_0 == 0:
                self.make_constant_int(op, 0)
                self._rule_fired_uint_rshift[0] += 1
                return
        # urshift_known_result: uint_rshift(a, b) => C
        if b_arg_0.urshift_bound(b_arg_1).is_constant():
            C = b_arg_0.urshift_bound(b_arg_1).get_constant_int()
            self.make_equal_to(op, ConstInt(C))
            self._rule_fired_uint_rshift[2] += 1
            return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # urshift_x_zero: uint_rshift(x, 0) => x
            if C_arg_1 == 0:
                self.make_equal_to(op, arg_0)
                self._rule_fired_uint_rshift[1] += 1
                return
        arg_0_int_lshift = self.optimizer.as_operation(arg_0, rop.INT_LSHIFT)
        if arg_0_int_lshift is not None:
            arg_0_0 = get_box_replacement(arg_0_int_lshift.getarg(0))
            b_arg_0_0 = self.getintbound(arg_0_0)
            arg_0_1 = get_box_replacement(arg_0_int_lshift.getarg(1))
            b_arg_0_1 = self.getintbound(arg_0_1)
            if b_arg_0_1.is_constant():
                C_arg_0_1 = b_arg_0_1.get_constant_int()
                if b_arg_1.is_constant():
                    C_arg_1 = b_arg_1.get_constant_int()
                    # urshift_lshift_x_c_c: uint_rshift(int_lshift(x, C), C) => int_and(x, mask)
                    if C_arg_1 == C_arg_0_1:
                        mask = intmask(r_uint(-1 << C_arg_0_1) >> r_uint(C_arg_0_1))
                        newop = self.replace_op_with(op, rop.INT_AND, args=[arg_0_0, ConstInt(mask)])
                        self.optimizer.send_extra_operation(newop)
                        self._rule_fired_uint_rshift[3] += 1
                        return
        return self.emit(op)
    _rule_names_int_eq = ['eq_different_knownbits', 'eq_same', 'eq_one', 'eq_zero']
    _rule_fired_int_eq = [0] * 4
    _all_rules_fired.append((_rule_names_int_eq, _rule_fired_int_eq))
    def optimize_INT_EQ(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_1 = get_box_replacement(op.getarg(1))
        b_arg_1 = self.getintbound(arg_1)
        # eq_same: int_eq(x, x) => 1
        if arg_1 is arg_0:
            self.make_constant_int(op, 1)
            self._rule_fired_int_eq[1] += 1
            return
        # eq_different_knownbits: int_eq(x, y) => 0
        if b_arg_0.known_ne(b_arg_1):
            self.make_constant_int(op, 0)
            self._rule_fired_int_eq[0] += 1
            return
        # eq_different_knownbits: int_eq(y, x) => 0
        if b_arg_1.known_ne(b_arg_0):
            self.make_constant_int(op, 0)
            self._rule_fired_int_eq[0] += 1
            return
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # eq_one: int_eq(1, x) => x
            if C_arg_0 == 1:
                if b_arg_1.is_bool():
                    self.make_equal_to(op, arg_1)
                    self._rule_fired_int_eq[2] += 1
                    return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # eq_one: int_eq(x, 1) => x
            if C_arg_1 == 1:
                if b_arg_0.is_bool():
                    self.make_equal_to(op, arg_0)
                    self._rule_fired_int_eq[2] += 1
                    return
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # eq_zero: int_eq(0, x) => int_is_zero(x)
            if C_arg_0 == 0:
                newop = self.replace_op_with(op, rop.INT_IS_ZERO, args=[arg_1])
                self.optimizer.send_extra_operation(newop)
                self._rule_fired_int_eq[3] += 1
                return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # eq_zero: int_eq(x, 0) => int_is_zero(x)
            if C_arg_1 == 0:
                newop = self.replace_op_with(op, rop.INT_IS_ZERO, args=[arg_0])
                self.optimizer.send_extra_operation(newop)
                self._rule_fired_int_eq[3] += 1
                return
        return self.emit(op)
    _rule_names_int_ne = ['ne_different_knownbits', 'ne_same', 'ne_zero']
    _rule_fired_int_ne = [0] * 3
    _all_rules_fired.append((_rule_names_int_ne, _rule_fired_int_ne))
    def optimize_INT_NE(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_1 = get_box_replacement(op.getarg(1))
        b_arg_1 = self.getintbound(arg_1)
        # ne_same: int_ne(x, x) => 0
        if arg_1 is arg_0:
            self.make_constant_int(op, 0)
            self._rule_fired_int_ne[1] += 1
            return
        # ne_different_knownbits: int_ne(x, y) => 1
        if b_arg_0.known_ne(b_arg_1):
            self.make_constant_int(op, 1)
            self._rule_fired_int_ne[0] += 1
            return
        # ne_different_knownbits: int_ne(y, x) => 1
        if b_arg_1.known_ne(b_arg_0):
            self.make_constant_int(op, 1)
            self._rule_fired_int_ne[0] += 1
            return
        if b_arg_0.is_constant():
            C_arg_0 = b_arg_0.get_constant_int()
            # ne_zero: int_ne(0, x) => int_is_true(x)
            if C_arg_0 == 0:
                newop = self.replace_op_with(op, rop.INT_IS_TRUE, args=[arg_1])
                self.optimizer.send_extra_operation(newop)
                self._rule_fired_int_ne[2] += 1
                return
        if b_arg_1.is_constant():
            C_arg_1 = b_arg_1.get_constant_int()
            # ne_zero: int_ne(x, 0) => int_is_true(x)
            if C_arg_1 == 0:
                newop = self.replace_op_with(op, rop.INT_IS_TRUE, args=[arg_0])
                self.optimizer.send_extra_operation(newop)
                self._rule_fired_int_ne[2] += 1
                return
        return self.emit(op)
    _rule_names_int_force_ge_zero = ['force_ge_zero_pos', 'force_ge_zero_neg']
    _rule_fired_int_force_ge_zero = [0] * 2
    _all_rules_fired.append((_rule_names_int_force_ge_zero, _rule_fired_int_force_ge_zero))
    def optimize_INT_FORCE_GE_ZERO(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        # force_ge_zero_neg: int_force_ge_zero(x) => 0
        if b_arg_0.known_lt_const(0):
            self.make_constant_int(op, 0)
            self._rule_fired_int_force_ge_zero[1] += 1
            return
        # force_ge_zero_pos: int_force_ge_zero(x) => x
        if b_arg_0.known_nonnegative():
            self.make_equal_to(op, arg_0)
            self._rule_fired_int_force_ge_zero[0] += 1
            return
        return self.emit(op)
    _rule_names_int_invert = ['invert_invert']
    _rule_fired_int_invert = [0] * 1
    _all_rules_fired.append((_rule_names_int_invert, _rule_fired_int_invert))
    def optimize_INT_INVERT(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_0_int_invert = self.optimizer.as_operation(arg_0, rop.INT_INVERT)
        if arg_0_int_invert is not None:
            arg_0_0 = get_box_replacement(arg_0_int_invert.getarg(0))
            b_arg_0_0 = self.getintbound(arg_0_0)
            # invert_invert: int_invert(int_invert(x)) => x
            self.make_equal_to(op, arg_0_0)
            self._rule_fired_int_invert[0] += 1
            return
        return self.emit(op)
    _rule_names_int_neg = ['neg_neg']
    _rule_fired_int_neg = [0] * 1
    _all_rules_fired.append((_rule_names_int_neg, _rule_fired_int_neg))
    def optimize_INT_NEG(self, op):
        arg_0 = get_box_replacement(op.getarg(0))
        b_arg_0 = self.getintbound(arg_0)
        arg_0_int_neg = self.optimizer.as_operation(arg_0, rop.INT_NEG)
        if arg_0_int_neg is not None:
            arg_0_0 = get_box_replacement(arg_0_int_neg.getarg(0))
            b_arg_0_0 = self.getintbound(arg_0_0)
            # neg_neg: int_neg(int_neg(x)) => x
            self.make_equal_to(op, arg_0_0)
            self._rule_fired_int_neg[0] += 1
            return
        return self.emit(op)
