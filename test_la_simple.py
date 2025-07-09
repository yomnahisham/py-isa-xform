#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.assembler import Assembler
from isa_xform.core.parser import Parser
from isa_xform.core.isa_loader import ISALoader

def test_la_simple():
    """Simple test for LA calculation"""
    
    # Load ZX16 ISA
    loader = ISALoader()
    isa = loader.load_isa_from_file("src/isa_definitions/zx16.json")
    
    # Create assembler
    assembler = Assembler(isa)
    
    # Test with a simple case: LA at address 0x200, label at 0x100
    assembly_code = """
    .org 0x200
    LA x6, target_label
    NOP
    
    .org 0x100
    target_label:
        .word 0x1234
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
    
    # Extract the LA instruction (should be at offset 28 + 0x200 - 0x200 = 28)
    code_start = 28
    code_bytes = result.machine_code[code_start:]
    
    print(f"\nMachine code at LA instruction:")
    for i in range(0, 4, 2):  # First two instructions (LA expands to 2 instructions)
        word = int.from_bytes(code_bytes[i:i+2], 'little')
        opcode = word & 0x7
        if opcode == 0b110:  # AUIPC opcode
            imm = (word >> 9) & 0x3F
            imm2 = (word >> 3) & 0x7
            full_imm = (imm << 3) | imm2
            print(f"AUIPC: imm={full_imm:#x} (decimal: {full_imm})")
        elif opcode == 0b001:  # ADDI opcode
            imm = (word >> 9) & 0x1FF
            print(f"ADDI: imm={imm:#x} (decimal: {imm})")
    
    # Verify the calculation
    label_addr = 0x100  # 256
    pc = 0x200          # 512
    lower_bits = label_addr & 0x7F  # 0
    expected_imm = (label_addr - lower_bits - pc) >> 7
    print(f"\nExpected calculation:")
    print(f"  Label address: 0x{label_addr:04X} ({label_addr})")
    print(f"  PC: 0x{pc:04X} ({pc})")
    print(f"  Lower bits: 0x{lower_bits:02X} ({lower_bits})")
    print(f"  Expected AUIPC imm: {expected_imm}")
    
    # Check what the assembler actually calculated
    # If AUIPC imm=2, then: PC + (2 << 7) = PC + 256
    # So: PC = label_addr - 256 = 256 - 256 = 0
    actual_pc = label_addr - (2 << 7)
    print(f"\nActual PC used by assembler: 0x{actual_pc:04X} ({actual_pc})")

if __name__ == "__main__":
    test_la_simple() 