from __future__ import print_function

import sys, os
from rply.errors import ParsingError, LexingError
from rpython.jit.metainterp.ruleopt import parse, proof, codegen

def main(argv):
    here = os.path.dirname(__file__)
    def_file = os.path.join(here, "real.rules")
    out_file = os.path.join(here, "..", "optimizeopt", "autogenintrules.py")
    with open(def_file) as f:
        content = f.read()
    try:
        ast = proof.prove_source(content)
    except (ParsingError, LexingError) as e:
        pos = e.getsourcepos()
        print("Parse error in line %s:" % pos.lineno)
        line = content.splitlines()[pos.lineno - 1]
        print("    " + line)
        print("    " + " " * (pos.colno - 1) + "^")
        return -1
    except parse.TypeCheckError as e:
        print(e.format(content))
        return -2
    except proof.CouldNotProve as e:
        print("_" * 60)
        print(e.format())
        return -3
    cgen = codegen.Codegen()
    result = cgen.generate_mixin(ast)
    with open(out_file, "w") as f:
        f.write("""# Generated by ruleopt/generate.py, don't edit!

from rpython.jit.metainterp.history import ConstInt
from rpython.jit.metainterp.optimizeopt.util import (
    get_box_replacement)
from rpython.jit.metainterp.resoperation import rop

from rpython.rlib.rarithmetic import LONG_BIT, r_uint, intmask, ovfcheck, uint_mul_high, highest_bit
""")
        f.write(result)



if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception:
        import pdb;pdb.xpm()
