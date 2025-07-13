#!/usr/bin/env python3

import sys
sys.path.append('../../../src')
from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.assembler import Assembler
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.parser import Parser

def test_zx16_all_types():
    """Test all ZX16 instruction types"""
    loader = ISALoader()
    isa = loader.load_isa('zx16')
    program = '''
.org 0x100
LI16 a0, 7
ADD a0, a1
SUB a0, a1
SLT a0, a1
SLTU a0, a1
SLL a0, a1
SRL a0, a1
SRA a0, a1
OR a0, a1
AND a0, a1
XOR a0, a1
MV a0, a1
LW a0, 0(a1)
SW a1, 0(a0)
ADDI a0, 7
SLTI a0, -8
ANDI a0, 7
ORI a0, -8
XORI a0, 7
SLLI a0, 3
SRLI a0, 4
SRAI a0, 2
LUI a0, 5
AUIPC a1, 6
JAL a0, 0x6
J 0x4
BEQ a0, a1, 0x2
BNE a0, a1, 0
JR a1
ECALL 0x1F
'''
    parser = Parser(isa)
    nodes = parser.parse(program)
    assembler = Assembler(isa)
    result = assembler.assemble(nodes)
    disassembler = Disassembler(isa)
    dis_result = disassembler.disassemble(result.machine_code, 0x100)
    print(disassembler.format_disassembly(dis_result, include_addresses=False))

if __name__ == '__main__':
    test_zx16_all_types() 