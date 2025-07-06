#!/usr/bin/env python3
"""
Test to verify ISA address space configuration is correctly followed
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.symbol_table import SymbolTable

def test_isa_address_space_compliance():
    """Test that disassembler correctly follows ISA address space configuration"""
    
    print("=" * 80)
    print("ISA ADDRESS SPACE COMPLIANCE TEST")
    print("=" * 80)
    
    # Load different ISAs to test their address space configurations
    loader = ISALoader()
    test_cases = [
        {
            "name": "ZX16",
            "isa_name": "zx16",
            "expected_code_start": 32,
            "expected_data_start": None,  # Not defined in ZX16
            "test_data": bytes([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0])
        },
        {
            "name": "SimpleRISC16", 
            "isa_name": "simple_risc",
            "expected_code_start": 4096,
            "expected_data_start": 8192,
            "test_data": bytes([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0])
        },
        {
            "name": "ModularExample",
            "isa_name": "modular_example", 
            "expected_code_start": 4096,
            "expected_data_start": 8192,
            "test_data": bytes([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0])
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"TESTING: {test_case['name']}")
        print(f"{'='*60}")
        
        try:
            # Load ISA
            isa_definition = loader.load_isa(test_case['isa_name'])
            symbol_table = SymbolTable()
            disassembler = Disassembler(isa_definition, symbol_table)
            
            # Check ISA address space configuration
            print(f"ISA Address Space Configuration:")
            print(f"  default_code_start: 0x{isa_definition.address_space.default_code_start:04X}")
            print(f"  default_data_start: 0x{isa_definition.address_space.default_data_start:04X}")
            print(f"  default_stack_start: 0x{isa_definition.address_space.default_stack_start:04X}")
            
            if hasattr(isa_definition.address_space, 'memory_layout') and isa_definition.address_space.memory_layout:
                print(f"  memory_layout: {isa_definition.address_space.memory_layout}")
            
            # Verify expected values
            code_start_ok = isa_definition.address_space.default_code_start == test_case['expected_code_start']
            print(f"  Code start correct: {'✓' if code_start_ok else '✗'}")
            
            if test_case['expected_data_start'] is not None:
                data_start_ok = isa_definition.address_space.default_data_start == test_case['expected_data_start']
                print(f"  Data start correct: {'✓' if data_start_ok else '✗'}")
            
            # Test disassembly with default start address (should use ISA default)
            print(f"\nTesting disassembly with default start address:")
            result_default = disassembler.disassemble(
                test_case['test_data'], 
                start_address=0,  # Should trigger ISA default
                debug=True
            )
            
            # Test disassembly with explicit start address
            print(f"\nTesting disassembly with explicit start address:")
            result_explicit = disassembler.disassemble(
                test_case['test_data'], 
                start_address=test_case['expected_code_start'],
                debug=True
            )
            
            # Verify results
            print(f"\nResults Analysis:")
            print(f"  Default start result: {len(result_default.instructions)} instructions")
            print(f"  Explicit start result: {len(result_explicit.instructions)} instructions")
            
            # Check if the disassembler started at the correct address
            if result_default.instructions:
                first_instr_addr = result_default.instructions[0].address
                expected_start = test_case['expected_code_start']
                start_correct = first_instr_addr == expected_start
                print(f"  First instruction address: 0x{first_instr_addr:04X}")
                print(f"  Expected start address: 0x{expected_start:04X}")
                print(f"  Start address correct: {'✓' if start_correct else '✗'}")
            
        except Exception as e:
            print(f"Error testing {test_case['name']}: {e}")
            continue

def test_memory_layout_compliance():
    """Test that disassembler respects memory layout boundaries"""
    
    print(f"\n{'='*80}")
    print("MEMORY LAYOUT COMPLIANCE TEST")
    print(f"{'='*80}")
    
    loader = ISALoader()
    
    # Test with SimpleRISC16 which has defined memory layout
    try:
        isa_definition = loader.load_isa("simple_risc")
        symbol_table = SymbolTable()
        disassembler = Disassembler(isa_definition, symbol_table)
        
        print(f"SimpleRISC16 Memory Layout:")
        memory_layout = isa_definition.address_space.memory_layout
        for section, bounds in memory_layout.items():
            print(f"  {section}: 0x{bounds['start']:04X} - 0x{bounds['end']:04X}")
        
        # Create test data that spans different sections
        # Code section: 4096-8191, Data section: 8192-12287
        test_data = bytes([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0] * 100)  # 800 bytes
        
        print(f"\nTesting disassembly of data spanning sections:")
        print(f"Test data size: {len(test_data)} bytes")
        print(f"Starting at code section: 0x{isa_definition.address_space.default_code_start:04X}")
        
        result = disassembler.disassemble(
            test_data,
            start_address=isa_definition.address_space.default_code_start,
            debug=True
        )
        
        print(f"\nAnalysis:")
        print(f"Total instructions: {len(result.instructions)}")
        print(f"Data sections: {len(result.data_sections)}")
        
        # Check if any instructions are in the data section range
        data_section_start = memory_layout['data_section']['start']
        data_section_end = memory_layout['data_section']['end']
        
        code_instructions = []
        data_instructions = []
        
        for instr in result.instructions:
            if data_section_start <= instr.address <= data_section_end:
                data_instructions.append(instr)
            else:
                code_instructions.append(instr)
        
        print(f"Instructions in code section: {len(code_instructions)}")
        print(f"Instructions in data section: {len(data_instructions)}")
        
        if data_instructions:
            print(f"WARNING: Found instructions in data section range!")
            for instr in data_instructions[:5]:  # Show first 5
                print(f"  {instr.address:04X}: {instr.mnemonic}")
        
    except Exception as e:
        print(f"Error testing memory layout: {e}")

def test_address_space_validation():
    """Test that the disassembler validates address space boundaries"""
    
    print(f"\n{'='*80}")
    print("ADDRESS SPACE VALIDATION TEST")
    print(f"{'='*80}")
    
    loader = ISALoader()
    
    try:
        isa_definition = loader.load_isa("zx16")
        symbol_table = SymbolTable()
        disassembler = Disassembler(isa_definition, symbol_table)
        
        # Test with different start addresses
        test_addresses = [0, 32, 100, 1000, 65535]
        test_data = bytes([0x12, 0x34, 0x56, 0x78])
        
        for start_addr in test_addresses:
            print(f"\nTesting start address: 0x{start_addr:04X}")
            try:
                result = disassembler.disassemble(
                    test_data,
                    start_address=start_addr,
                    debug=False  # Less verbose for this test
                )
                
                if result.instructions:
                    first_addr = result.instructions[0].address
                    last_addr = result.instructions[-1].address
                    print(f"  Instructions: 0x{first_addr:04X} - 0x{last_addr:04X}")
                else:
                    print(f"  No instructions decoded")
                    
            except Exception as e:
                print(f"  Error: {e}")
                
    except Exception as e:
        print(f"Error in address space validation: {e}")

if __name__ == "__main__":
    test_isa_address_space_compliance()
    test_memory_layout_compliance()
    test_address_space_validation() 