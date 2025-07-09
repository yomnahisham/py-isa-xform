#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.assembler import Assembler
from isa_xform.core.parser import Parser
from isa_xform.core.isa_loader import ISALoader

def test_li16_simple():
    """Simple test for LI16 with immediate value"""
    
    # Load ZX16 ISA
    loader = ISALoader()
    isa = loader.load_isa_from_file("src/isa_definitions/zx16.json")
    
    # Create assembler
    assembler = Assembler(isa)
    
    # Test assembly code with LI16 and immediate value
    assembly_code = """
    .org 0x1000
    
    start:
        li16 t0, 0x1234
        NOP
    """
    
    # Parse the code
    parser = Parser(isa)
    nodes = parser.parse(assembly_code)
    
    # Assemble
    result = assembler.assemble(nodes)
    
    print("Symbol table:")
    for name, symbol in result.symbol_table.symbols.items():
        if symbol.defined:
            print(f"  {name}: 0x{symbol.value:04X}")
    
    # Extract the LI16 instructions
    code_start = 28
    code_bytes = result.machine_code[code_start:]
    
    print(f"\nMachine code at LI16 instructions:")
    for i in range(0, 4, 2):  # First 2 instructions (LI16 expands to 2 instructions)
        word = int.from_bytes(code_bytes[i:i+2], 'little')
        opcode = word & 0x7
        if opcode == 0b110:  # LUI opcode
            flag = (word >> 15) & 0x1
            imm = (word >> 9) & 0x3F
            imm2 = (word >> 3) & 0x7
            full_imm = (imm << 3) | imm2
            print(f"LUI at offset {i+code_start:#x}: flag={flag}, imm={imm:#x}, imm2={imm2:#x}, full_imm={full_imm:#x} (decimal: {full_imm})")
        elif opcode == 0b001:  # ORI opcode
            imm = (word >> 9) & 0x1FF
            print(f"ORI at offset {i+code_start:#x}: imm={imm:#x} (decimal: {imm})")
    
    # Verify the calculations
    value = 0x1234  # 4660
    
    print(f"\nExpected calculations:")
    print(f"  Value: 0x{value:04X} ({value})")
    print(f"  Value[14:9]: {(value >> 9) & 0x3F} (decimal: {(value >> 9) & 0x3F})")
    print(f"  Value[8:2]: {(value >> 2) & 0x7F} (decimal: {(value >> 2) & 0x7F})")

if __name__ == "__main__":
    test_li16_simple() 