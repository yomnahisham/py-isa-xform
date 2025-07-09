#!/usr/bin/env python3

import sys
import os
# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.assembler import Assembler
from isa_xform.core.parser import Parser
from isa_xform.core.isa_loader import ISALoader

def test_la_calculation():
    """Test LA instruction calculation"""
    
    # Load ZX16 ISA
    loader = ISALoader()
    isa = loader.load_isa_from_file("src/isa_definitions/zx16.json")
    
    # Create assembler
    assembler = Assembler(isa)
    
    # Test assembly code with LA instruction
    assembly_code = """
    .org 0x100
    target_label:
        .word 0x1234
    start:
        LA x6, target_label
        NOP
    """
    
    # Parse the code
    parser = Parser(isa)
    nodes = parser.parse(assembly_code)
    
    # Assemble
    result = assembler.assemble(nodes)
    
    print("Assembly result:")
    print(f"Machine code length: {len(result.machine_code)} bytes")
    print(f"Machine code: {result.machine_code.hex()}")
    
    # Show symbol table
    print("\nSymbol table:")
    for name, symbol in result.symbol_table.symbols.items():
        if symbol.defined:
            print(f"  {name}: 0x{symbol.value:04X}")
    
    # Disassemble to verify
    from isa_xform.core.disassembler import Disassembler
    disassembler = Disassembler(isa)
    
    # Skip the ISAX header (first 28 bytes)
    code_start = 28
    code_bytes = result.machine_code[code_start:]
    
    print(f"\nDisassembly (starting at offset {code_start}):")
    disassembly = disassembler.disassemble(code_bytes, start_address=0x100)
    print(disassembly)

    # Print AUIPC and ADDI immediates for LA
    print("\nDecoded AUIPC and ADDI immediates:")
    # Find the AUIPC and ADDI instructions in the code_bytes
    for i in range(0, len(code_bytes), 2):
        word = int.from_bytes(code_bytes[i:i+2], 'little')
        opcode = word & 0x7
        if opcode == 0b110:  # AUIPC opcode
            imm = (word >> 9) & 0x3F
            imm2 = (word >> 3) & 0x7
            full_imm = (imm << 3) | imm2
            print(f"AUIPC at offset {i+code_start:#x}: imm={full_imm:#x}")
        elif opcode == 0b001:  # ADDI opcode
            imm = (word >> 9) & 0x1FF
            print(f"ADDI at offset {i+code_start:#x}: imm={imm:#x}")

def main():
    test_la_calculation()

if __name__ == "__main__":
    main() 