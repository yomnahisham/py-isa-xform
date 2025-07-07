#!/usr/bin/env python3
"""
Comprehensive example demonstrating debug disassembly functionality
Shows PC counter progression and code vs data separation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.symbol_table import SymbolTable

def demonstrate_debug_disassembly():
    """Demonstrate debug disassembly with various scenarios"""
    
    print("=" * 80)
    print("DEBUG DISASSEMBLY DEMONSTRATION")
    print("=" * 80)
    
    # Load different ISAs to test
    loader = ISALoader()
    isas_to_test = ["zx16", "simple_risc", "modular_example"]
    
    for isa_name in isas_to_test:
        try:
            print(f"\n{'='*60}")
            print(f"TESTING ISA: {isa_name}")
            print(f"{'='*60}")
            
            isa_definition = loader.load_isa(isa_name)
            symbol_table = SymbolTable()
            disassembler = Disassembler(isa_definition, symbol_table)
            
            # Create test programs with different characteristics
            test_cases = [
                {
                    "name": "Code Only",
                    "data": bytes([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0]),
                    "start_addr": 0x1000
                },
                {
                    "name": "Code + Data",
                    "data": bytes([0x12, 0x34, 0x56, 0x78, 0x00, 0x00, 0x41, 0x42, 0x43, 0x44]),
                    "start_addr": 0x2000
                },
                {
                    "name": "Code + Return + Data",
                    "data": bytes([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0x00, 0x00, 0x41, 0x42, 0x43, 0x44]),
                    "start_addr": 0x3000
                }
            ]
            
            for test_case in test_cases:
                print(f"\n--- {test_case['name']} ---")
                print(f"Data: {' '.join(f'{b:02X}' for b in test_case['data'])}")
                print(f"Start address: 0x{test_case['start_addr']:04X}")
                print("-" * 40)
                
                # Run disassembly with debug
                result = disassembler.disassemble(
                    test_case['data'], 
                    start_address=test_case['start_addr'], 
                    debug=True
                )
                
                print(f"\nResults for {test_case['name']}:")
                print(f"  Instructions: {len(result.instructions)}")
                print(f"  Data sections: {len(result.data_sections)}")
                
                if result.instructions:
                    print("  Instructions found:")
                    for instr in result.instructions:
                        print(f"    0x{instr.address:04X}: {instr.mnemonic} {', '.join(instr.operands)}")
                
                if result.data_sections:
                    print("  Data sections:")
                    for addr, data in result.data_sections.items():
                        print(f"    0x{addr:04X}: {len(data)} bytes - {' '.join(f'{b:02X}' for b in data)}")
                
                print()
                
        except Exception as e:
            print(f"Error testing {isa_name}: {e}")
            continue

def analyze_real_binary():
    """Analyze a real binary file with debug output"""
    
    print("\n" + "=" * 80)
    print("ANALYZING REAL BINARY FILE")
    print("=" * 80)
    
    # Test with a real binary file
    binary_path = "tests/TC-ZX16/comprehensive/test_zx16_comprehensive.bin"
    
    if not os.path.exists(binary_path):
        print(f"Binary file not found: {binary_path}")
        return
    
    try:
        with open(binary_path, 'rb') as f:
            binary_data = f.read()
        
        print(f"Binary file: {binary_path}")
        print(f"Size: {len(binary_data)} bytes")
        print(f"First 16 bytes: {' '.join(f'{b:02X}' for b in binary_data[:16])}")
        print()
        
        # Load ISA and disassemble
        loader = ISALoader()
        isa_definition = loader.load_isa("zx16")
        symbol_table = SymbolTable()
        disassembler = Disassembler(isa_definition, symbol_table)
        
        print("Running debug disassembly:")
        print("-" * 60)
        result = disassembler.disassemble(binary_data, start_address=0x20, debug=True)
        print("-" * 60)
        
        # Analyze results
        print(f"\nANALYSIS RESULTS:")
        print(f"Total instructions decoded: {len(result.instructions)}")
        print(f"Data sections found: {len(result.data_sections)}")
        
        # Show instruction distribution
        instruction_types = {}
        for instr in result.instructions:
            mnemonic = instr.mnemonic
            instruction_types[mnemonic] = instruction_types.get(mnemonic, 0) + 1
        
        print(f"\nInstruction types:")
        for mnemonic, count in sorted(instruction_types.items()):
            print(f"  {mnemonic}: {count}")
        
        # Show data section analysis
        if result.data_sections:
            print(f"\nData section analysis:")
            total_data_bytes = 0
            for addr, data in result.data_sections.items():
                total_data_bytes += len(data)
                print(f"  0x{addr:04X}: {len(data)} bytes")
                # Try to detect ASCII strings
                try:
                    ascii_str = data.decode('ascii', errors='replace')
                    if all(32 <= ord(c) <= 126 for c in ascii_str if c != '?'):
                        print(f"    ASCII: '{ascii_str}'")
                except:
                    pass
            
            print(f"  Total data bytes: {total_data_bytes}")
            print(f"  Data percentage: {(total_data_bytes / len(binary_data)) * 100:.1f}%")
        
    except Exception as e:
        print(f"Error analyzing binary: {e}")

if __name__ == "__main__":
    demonstrate_debug_disassembly()
    analyze_real_binary() 