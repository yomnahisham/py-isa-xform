#!/usr/bin/env python3

import sys
sys.path.append('../../src')
from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.assembler import Assembler
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.parser import Parser

def test_custom_modular():
    """Test custom modular ISA with custom instructions and directive"""
    loader = ISALoader()
    isa = loader.load_isa('custom_modular_isa')
    program = '''
.org 0
CUSTADD r1, r2
CUSTIMM r3, #123
.customdata 0xABCD, 0x1234
'''
    parser = Parser(isa)
    nodes = parser.parse(program)
    assembler = Assembler(isa)
    result = assembler.assemble(nodes)
    disassembler = Disassembler(isa)
    dis_result = disassembler.disassemble(result.machine_code, 0)
    print(disassembler.format_disassembly(dis_result, include_addresses=False))

if __name__ == '__main__':
    test_custom_modular() 