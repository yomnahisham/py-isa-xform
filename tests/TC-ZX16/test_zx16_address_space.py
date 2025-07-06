#!/usr/bin/env python3
"""
Specific test to verify ZX16 address space configuration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.symbol_table import SymbolTable

def test_zx16_address_space():
    """Test ZX16 address space configuration specifically"""
    
    print("=" * 80)
    print("ZX16 ADDRESS SPACE CONFIGURATION TEST")
    print("=" * 80)
    
    # Load ZX16 ISA
    loader = ISALoader()
    isa_definition = loader.load_isa("zx16")
    symbol_table = SymbolTable()
    disassembler = Disassembler(isa_definition, symbol_table)
    
    print(f"ZX16 ISA Configuration:")
    print(f"  Name: {isa_definition.name}")
    print(f"  Version: {isa_definition.version}")
    print(f"  Instruction size: {isa_definition.instruction_size} bits")
    print(f"  Word size: {isa_definition.word_size} bits")
    print(f"  Endianness: {isa_definition.endianness}")
    print()
    
    print(f"Address Space Configuration:")
    print(f"  default_code_start: 0x{isa_definition.address_space.default_code_start:04X}")
    print(f"  default_data_start: 0x{isa_definition.address_space.default_data_start:04X}")
    print(f"  default_stack_start: 0x{isa_definition.address_space.default_stack_start:04X}")
    
    if hasattr(isa_definition.address_space, 'memory_layout') and isa_definition.address_space.memory_layout:
        print(f"  memory_layout: {isa_definition.address_space.memory_layout}")
    else:
        print(f"  memory_layout: Not defined")
    
    print()
    
    # Test 1: Verify default start address
    print("TEST 1: Default Start Address")
    print("-" * 40)
    
    # Create test data with valid ZX16 instructions
    test_data = bytes([
        0x06, 0x0A,  # LI x6, 10
        0x07, 0xFB,  # LI x7, 0xFFFFFFFB (signed)
        0x06, 0x3F,  # LI x6, 63
        0x07, 0xC0,  # LI x7, 0xFFFFFFC0 (signed)
    ])
    
    print(f"Test data: {' '.join(f'{b:02X}' for b in test_data)}")
    print(f"Expected start address: 0x{isa_definition.address_space.default_code_start:04X}")
    
    # Test with start_address=0 (should use ISA default)
    result = disassembler.disassemble(test_data, start_address=0, debug=True)
    
    print(f"\nResults:")
    print(f"  Instructions found: {len(result.instructions)}")
    print(f"  Data sections: {len(result.data_sections)}")
    
    if result.instructions:
        first_addr = result.instructions[0].address
        last_addr = result.instructions[-1].address
        print(f"  Instruction range: 0x{first_addr:04X} - 0x{last_addr:04X}")
        print(f"  First instruction: {result.instructions[0].mnemonic} {', '.join(result.instructions[0].operands)}")
        
        # Verify it started at the correct address
        expected_start = isa_definition.address_space.default_code_start
        if first_addr == expected_start:
            print(f"  ✓ Correctly started at ISA default: 0x{expected_start:04X}")
        else:
            print(f"  ✗ Expected 0x{expected_start:04X}, got 0x{first_addr:04X}")
    
    print()
    
    # Test 2: Verify PC progression
    print("TEST 2: PC Progression")
    print("-" * 40)
    
    # Test with a longer sequence
    longer_data = bytes([
        0x06, 0x0A,  # LI x6, 10
        0x07, 0xFB,  # LI x7, 0xFFFFFFFB
        0x06, 0x3F,  # LI x6, 63
        0x07, 0xC0,  # LI x7, 0xFFFFFFC0
        0x01, 0x00,  # JAL x1
        0x01, 0x00,  # JAL x1
        0x00, 0x00,  # Unknown instruction
        0x00, 0x00,  # Unknown instruction
    ])
    
    print(f"Longer test data: {' '.join(f'{b:02X}' for b in longer_data)}")
    
    result2 = disassembler.disassemble(longer_data, start_address=0x20, debug=True)
    
    print(f"\nPC Progression Analysis:")
    expected_addresses = []
    current_addr = 0x20
    for i in range(len(longer_data) // 2):
        expected_addresses.append(current_addr)
        current_addr += 2
    
    print(f"  Expected addresses: {[f'0x{addr:04X}' for addr in expected_addresses]}")
    
    actual_addresses = [instr.address for instr in result2.instructions]
    print(f"  Actual addresses: {[f'0x{addr:04X}' for addr in actual_addresses]}")
    
    # Check if PC progression is correct
    pc_correct = True
    for i, (expected, actual) in enumerate(zip(expected_addresses, actual_addresses)):
        if expected != actual:
            pc_correct = False
            print(f"    ✗ Mismatch at instruction {i}: expected 0x{expected:04X}, got 0x{actual:04X}")
    
    if pc_correct:
        print(f"  ✓ PC progression is correct")
    else:
        print(f"  ✗ PC progression has errors")
    
    print()
    
    # Test 3: Verify with real ZX16 binary
    print("TEST 3: Real ZX16 Binary")
    print("-" * 40)
    
    binary_path = "tests/TC-ZX16/comprehensive/test_zx16_comprehensive.bin"
    
    if os.path.exists(binary_path):
        with open(binary_path, 'rb') as f:
            binary_data = f.read()
        
        print(f"Binary file: {binary_path}")
        print(f"Size: {len(binary_data)} bytes")
        print(f"First 16 bytes: {' '.join(f'{b:02X}' for b in binary_data[:16])}")
        
        # Test disassembly
        result3 = disassembler.disassemble(binary_data, start_address=0, debug=False)  # Less verbose
        
        print(f"\nReal Binary Analysis:")
        print(f"  Total instructions: {len(result3.instructions)}")
        print(f"  Data sections: {len(result3.data_sections)}")
        
        if result3.instructions:
            first_addr = result3.instructions[0].address
            last_addr = result3.instructions[-1].address
            print(f"  Instruction range: 0x{first_addr:04X} - 0x{last_addr:04X}")
            
            # Check if it started at the correct address
            expected_start = isa_definition.address_space.default_code_start
            if first_addr == expected_start:
                print(f"  ✓ Correctly started at ISA default: 0x{expected_start:04X}")
            else:
                print(f"  ✗ Expected 0x{expected_start:04X}, got 0x{first_addr:04X}")
            
            # Show some sample instructions
            print(f"  Sample instructions:")
            for i, instr in enumerate(result3.instructions[:5]):
                print(f"    0x{instr.address:04X}: {instr.mnemonic} {', '.join(instr.operands)}")
        
        if result3.data_sections:
            print(f"  Data sections:")
            for addr, data in result3.data_sections.items():
                print(f"    0x{addr:04X}: {len(data)} bytes - {' '.join(f'{b:02X}' for b in data)}")
    else:
        print(f"Binary file not found: {binary_path}")
    
    print()
    
    # Test 4: Verify ZX16 specific configuration
    print("TEST 4: ZX16 Specific Configuration")
    print("-" * 40)
    
    # Check ZX16 specific values according to specification
    expected_code_start = 0  # PC starts at 0x0000 on reset
    expected_code_section_start = 32  # Code section starts at 0x0020
    expected_instruction_size = 16
    expected_word_size = 16
    expected_endianness = "little"
    
    print(f"Expected ZX16 Configuration:")
    print(f"  default_code_start: 0x{expected_code_start:04X} (PC starts here on reset)")
    print(f"  CODE_START: 0x{expected_code_section_start:04X} (actual code section starts here)")
    print(f"  instruction_size: {expected_instruction_size} bits")
    print(f"  word_size: {expected_word_size} bits")
    print(f"  endianness: {expected_endianness}")
    
    print(f"\nActual ZX16 Configuration:")
    print(f"  default_code_start: 0x{isa_definition.address_space.default_code_start:04X}")
    print(f"  CODE_START: {isa_definition.constants['CODE_START']}")
    print(f"  instruction_size: {isa_definition.instruction_size} bits")
    print(f"  word_size: {isa_definition.word_size} bits")
    print(f"  endianness: {isa_definition.endianness}")
    
    # Verify all values
    code_start_ok = isa_definition.address_space.default_code_start == expected_code_start
    code_start_const = isa_definition.constants['CODE_START']
    code_section_ok = (code_start_const.value if hasattr(code_start_const, 'value') else code_start_const) == expected_code_section_start
    instruction_size_ok = isa_definition.instruction_size == expected_instruction_size
    word_size_ok = isa_definition.word_size == expected_word_size
    endianness_ok = isa_definition.endianness.lower() == expected_endianness.lower()
    
    print(f"\nVerification Results:")
    print(f"  Code start: {'✓' if code_start_ok else '✗'}")
    print(f"  CODE_START: {'✓' if code_section_ok else '✗'}")
    print(f"  Instruction size: {'✓' if instruction_size_ok else '✗'}")
    print(f"  Word size: {'✓' if word_size_ok else '✗'}")
    print(f"  Endianness: {'✓' if endianness_ok else '✗'}")
    
    all_correct = code_start_ok and code_section_ok and instruction_size_ok and word_size_ok and endianness_ok
    print(f"\nOverall ZX16 Configuration: {'✓ CORRECT' if all_correct else '✗ INCORRECT'}")

if __name__ == "__main__":
    test_zx16_address_space() 