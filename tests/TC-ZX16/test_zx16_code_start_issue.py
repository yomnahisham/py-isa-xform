#!/usr/bin/env python3
"""
Test to demonstrate the ZX16 code start address issue
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.symbol_table import SymbolTable

def test_zx16_code_start_issue():
    """Test to demonstrate the ZX16 code start address issue"""
    
    print("=" * 80)
    print("ZX16 CODE START ADDRESS ISSUE DEMONSTRATION")
    print("=" * 80)
    
    # Load ZX16 ISA
    loader = ISALoader()
    isa_definition = loader.load_isa("zx16")
    
    print(f"Current ZX16 Configuration:")
    print(f"  default_code_start: 0x{isa_definition.address_space.default_code_start:04X}")
    print(f"  RESET_VECTOR: {isa_definition.constants['RESET_VECTOR']}")
    print(f"  CODE_START: {isa_definition.constants['CODE_START']}")
    print()
    
    # The issue: There's a mismatch between what the ISA says and what it should be
    print("ISSUE IDENTIFIED:")
    print("  - RESET_VECTOR: 0x0000 (where processor starts)")
    print("  - CODE_START: 0x0020 (where code should start)")
    print("  - default_code_start: 0x0020 (what disassembler uses)")
    print()
    print("PROBLEM: If the ISA specification says code should start at 0x0000,")
    print("         then default_code_start should be 0, not 32!")
    print()
    
    # Test with different start addresses
    test_data = bytes([
        0x06, 0x0A,  # LI x6, 10
        0x07, 0xFB,  # LI x7, 0xFFFFFFFB
        0x06, 0x3F,  # LI x6, 63
        0x07, 0xC0,  # LI x7, 0xFFFFFFC0
    ])
    
    print("Testing different start addresses:")
    print("-" * 50)
    
    test_addresses = [0, 32, 256]  # 0x0000, 0x0020, 0x0100
    
    for start_addr in test_addresses:
        print(f"\nTest with start_address=0x{start_addr:04X}:")
        
        disassembler = Disassembler(isa_definition)
        result = disassembler.disassemble(test_data, start_address=start_addr, debug=False)
        
        if result.instructions:
            first_addr = result.instructions[0].address
            last_addr = result.instructions[-1].address
            print(f"  Instructions: 0x{first_addr:04X} - 0x{last_addr:04X}")
            print(f"  First instruction: {result.instructions[0].mnemonic} {', '.join(result.instructions[0].operands)}")
        else:
            print(f"  No instructions decoded")
    
    print()
    print("RECOMMENDATION:")
    print("  If ZX16 ISA specification says code should start at 0x0000:")
    print("  1. Change default_code_start from 32 to 0")
    print("  2. Update CODE_START constant from 32 to 0")
    print("  3. Update test files to use .org 0x0000 instead of .org 0x100 or .org 32")
    print()
    print("  If ZX16 ISA specification says code should start at 0x0020:")
    print("  Then the current configuration is correct, but documentation should clarify this.")
    print()
    print("  The disassembler correctly follows the ISA definition - the issue is")
    print("  whether the ISA definition matches the actual ZX16 specification.")

if __name__ == "__main__":
    test_zx16_code_start_issue() 