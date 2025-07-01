#!/usr/bin/env python3
"""
Test script demonstrating custom instruction implementations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.assembler import Assembler
from isa_xform.core.parser import Parser
from isa_xform.core.instruction_executor import get_instruction_executor, ExecutionContext
from isa_xform.utils.error_handling import ErrorReporter


def test_custom_isa_loading():
    """Test loading an ISA with custom instruction implementations"""
    print("=== Testing Custom ISA Loading ===")
    
    # Load the custom ISA
    loader = ISALoader()
    try:
        isa_def = loader.load_isa_from_file("src/isa_definitions/custom_isa_example.json")
        print(f"✓ Successfully loaded ISA: {isa_def.name} v{isa_def.version}")
        print(f"  Description: {isa_def.description}")
        print(f"  Instructions: {len(isa_def.instructions)}")
        
        # Check which instructions have implementations
        executor = get_instruction_executor()
        for instruction in isa_def.instructions:
            if instruction.implementation:
                print(f"  ✓ {instruction.mnemonic}: Has custom implementation")
            else:
                print(f"  - {instruction.mnemonic}: No custom implementation")
        
        return isa_def
    except Exception as e:
        print(f"✗ Failed to load ISA: {e}")
        return None


def test_custom_instruction_execution():
    """Test executing custom instruction implementations"""
    print("\n=== Testing Custom Instruction Execution ===")
    
    # Create execution context
    context = ExecutionContext(
        registers={'x0': 0, 'x1': 0, 'x2': 0, 'x3': 0, 'x4': 0, 'x5': 0, 'x6': 10, 'x7': 5},
        memory=bytearray(1024),
        pc=0,
        flags={}
    )
    
    executor = get_instruction_executor()
    
    # Test MULT instruction
    print("Testing MULT instruction:")
    print(f"  Before: x6={context.registers['x6']}, x7={context.registers['x7']}")
    
    try:
        # Execute MULT x6, x7 (x6 = x6 * x7)
        operands = {'rd': 'x6', 'rs2': 'x7'}
        executor.execute_instruction('MULT', context, operands)
        print(f"  After: x6={context.registers['x6']}, x7={context.registers['x7']}")
        print(f"  Flags: {context.flags}")
    except Exception as e:
        print(f"  ✗ Error executing MULT: {e}")
    
    # Test SWAP instruction
    print("\nTesting SWAP instruction:")
    print(f"  Before: x6={context.registers['x6']}, x7={context.registers['x7']}")
    
    try:
        # Execute SWAP x6, x7
        operands = {'rd': 'x6', 'rs2': 'x7'}
        executor.execute_instruction('SWAP', context, operands)
        print(f"  After: x6={context.registers['x6']}, x7={context.registers['x7']}")
    except Exception as e:
        print(f"  ✗ Error executing SWAP: {e}")


def test_assembly_with_custom_instructions():
    """Test assembling code with custom instructions"""
    print("\n=== Testing Assembly with Custom Instructions ===")
    
    # Load ISA
    loader = ISALoader()
    isa_def = loader.load_isa_from_file("src/isa_definitions/custom_isa_example.json")
    
    # Create assembler
    assembler = Assembler(isa_def)
    
    # Test assembly code with custom instructions
    assembly_code = """
    ; Test program with custom instructions
    .org 0x100
    
    start:
        ADD x6, x7      ; Add x7 to x6
        MULT x6, x7     ; Multiply x6 by x7
        SWAP x6, x7     ; Swap x6 and x7
        CRC16 x6, x7    ; Calculate CRC16
    """
    
    print("Assembly code:")
    print(assembly_code)
    
    try:
        # Parse the assembly code
        parser = Parser(isa_def)
        nodes = parser.parse(assembly_code)
        
        # Assemble the code
        result = assembler.assemble(nodes)
        
        print(f"✓ Assembly successful!")
        print(f"  Machine code size: {len(result.machine_code)} bytes")
        print(f"  Entry point: {result.entry_point}")
        
        # Show the machine code
        print("  Machine code:")
        for i in range(0, len(result.machine_code), 2):
            if i + 1 < len(result.machine_code):
                word = result.machine_code[i] | (result.machine_code[i + 1] << 8)
                print(f"    0x{i:04X}: 0x{word:04X}")
        
    except Exception as e:
        print(f"✗ Assembly failed: {e}")


def test_instruction_implementation_validation():
    """Test validation of instruction implementations"""
    print("\n=== Testing Instruction Implementation Validation ===")
    
    executor = get_instruction_executor()
    
    # Test invalid implementation
    print("Testing invalid implementation:")
    try:
        executor.compile_implementation("INVALID", "this is not valid python code {")
        print("  ✗ Should have failed")
    except Exception as e:
        print(f"  ✓ Correctly caught error: {e}")
    
    # Test valid implementation
    print("\nTesting valid implementation:")
    try:
        valid_code = "# Valid implementation\nresult = 42\nwrite_register('x0', result)"
        executor.compile_implementation("VALID", valid_code)
        print("  ✓ Successfully compiled valid implementation")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")


def main():
    """Main test function"""
    print("Custom Instruction Implementation Test Suite")
    print("=" * 50)
    
    # Test 1: Loading custom ISA
    isa_def = test_custom_isa_loading()
    if not isa_def:
        print("Failed to load ISA, aborting tests")
        return
    
    # Test 2: Executing custom instructions
    test_custom_instruction_execution()
    
    # Test 3: Assembly with custom instructions
    test_assembly_with_custom_instructions()
    
    # Test 4: Implementation validation
    test_instruction_implementation_validation()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")


if __name__ == "__main__":
    main() 