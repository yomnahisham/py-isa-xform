#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.assembler import Assembler
from isa_xform.core.parser import Parser
from isa_xform.core.isa_loader import ISALoader

def test_li16_with_labels():
    """Test LI16 instruction with labels"""
    
    # Load ZX16 ISA
    loader = ISALoader()
    isa = loader.load_isa_from_file("src/isa_definitions/zx16.json")
    
    # Create assembler
    assembler = Assembler(isa)
    
    # Test assembly code with LI16 and labels
    assembly_code = """
    .org 0x1000
    
    start:
        li16 t0, words
        li16 x0, name
        NOP
    
    .org 0x2000
    words:
        .word 0x1234
        .word 0x5678
    
    .org 0x3000
    name:
        .ascii "Hello"
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
    
    # Extract the LI16 instructions (should be at offset 28 + 0x1000 - 0x1000 = 28)
    code_start = 28
    code_bytes = result.machine_code[code_start:]
    
    print(f"\nMachine code at LI16 instructions:")
    for i in range(0, 8, 2):  # First 4 instructions (2 LI16 expand to 4 instructions each)
        word = int.from_bytes(code_bytes[i:i+2], 'little')
        opcode = word & 0x7
        if opcode == 0b100:  # LUI opcode
            imm = (word >> 9) & 0x3F
            imm2 = (word >> 3) & 0x7
            full_imm = (imm << 3) | imm2
            print(f"LUI at offset {i+code_start:#x}: imm={full_imm:#x} (decimal: {full_imm})")
        elif opcode == 0b001:  # ORI opcode
            imm = (word >> 9) & 0x1FF
            print(f"ORI at offset {i+code_start:#x}: imm={imm:#x} (decimal: {imm})")
    
    # Verify the calculations
    words_addr = 0x2000  # 8192
    name_addr = 0x3000   # 12288
    
    print(f"\nExpected calculations:")
    print(f"  words address: 0x{words_addr:04X} ({words_addr})")
    print(f"  name address: 0x{name_addr:04X} ({name_addr})")
    print(f"  words[15:9]: {(words_addr >> 9) & 0x3F} (decimal: {(words_addr >> 9) & 0x3F})")
    print(f"  words[8:0]: {words_addr & 0x1FF} (decimal: {words_addr & 0x1FF})")
    print(f"  name[15:9]: {(name_addr >> 9) & 0x3F} (decimal: {(name_addr >> 9) & 0x3F})")
    print(f"  name[8:0]: {name_addr & 0x1FF} (decimal: {name_addr & 0x1FF})")

if __name__ == "__main__":
    test_li16_with_labels() 