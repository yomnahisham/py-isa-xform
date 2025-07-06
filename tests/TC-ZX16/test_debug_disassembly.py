#!/usr/bin/env python3
"""
Test script to demonstrate debug disassembly with PC counter tracking
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.symbol_table import SymbolTable

def test_debug_disassembly():
    """Test debug disassembly with a simple program"""
    
    # Load a simple ISA
    loader = ISALoader()
    isa_definition = loader.load_isa("simple_risc")
    
    # Create a simple test program with some code and data
    # This will help demonstrate the PC progression and code/data separation
    test_program = bytes([
        # Some valid instructions (assuming simple_risc format)
        0x12, 0x34,  # Example instruction 1
        0x56, 0x78,  # Example instruction 2
        0x9A, 0xBC,  # Example instruction 3
        0xDE, 0xF0,  # Example instruction 4
        # Some data (non-zero bytes that might not decode as valid instructions)
        0x00, 0x00,  # Padding/zeros
        0x00, 0x00,  # More padding
        0x41, 0x42,  # ASCII data: "AB"
        0x43, 0x44,  # ASCII data: "CD"
        0x45, 0x46,  # ASCII data: "EF"
        0x47, 0x48,  # ASCII data: "GH"
    ])
    
    print("=" * 80)
    print("DEBUG DISASSEMBLY TEST")
    print("=" * 80)
    print(f"Test program size: {len(test_program)} bytes")
    print(f"Program bytes: {' '.join(f'{b:02X}' for b in test_program)}")
    print()
    
    # Create disassembler with debug enabled
    symbol_table = SymbolTable()
    disassembler = Disassembler(isa_definition, symbol_table)
    
    # Run disassembly with debug output
    print("Running disassembly with debug output:")
    print("-" * 60)
    result = disassembler.disassemble(test_program, start_address=0x1000, debug=True)
    print("-" * 60)
    
    # Show final results
    print("\nFINAL RESULTS:")
    print(f"Instructions found: {len(result.instructions)}")
    print(f"Data sections: {len(result.data_sections)}")
    
    print("\nInstructions:")
    for instr in result.instructions:
        print(f"  0x{instr.address:04X}: {instr.mnemonic} {', '.join(instr.operands)}")
    
    print("\nData sections:")
    for addr, data in result.data_sections.items():
        print(f"  0x{addr:04X}: {len(data)} bytes - {' '.join(f'{b:02X}' for b in data)}")
        # Try to decode as ASCII
        try:
            ascii_str = data.decode('ascii', errors='replace')
            if all(32 <= ord(c) <= 126 for c in ascii_str if c != '?'):
                print(f"    ASCII: '{ascii_str}'")
        except:
            pass

if __name__ == "__main__":
    test_debug_disassembly() 