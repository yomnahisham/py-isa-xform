#!/usr/bin/env python3
"""
Test script demonstrating custom directive implementations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.assembler import Assembler
from isa_xform.core.parser import Parser
from isa_xform.core.directive_executor import get_directive_executor, DirectiveContext
from isa_xform.utils.error_handling import ErrorReporter


def test_custom_directive_loading():
    """Test loading an ISA with custom directive implementations"""
    print("=== Testing Custom Directive Loading ===")
    
    # Load the custom ISA
    loader = ISALoader()
    try:
        isa_def = loader.load_isa_from_file("src/isa_definitions/custom_isa_example.json")
        print(f"✓ Successfully loaded ISA: {isa_def.name} v{isa_def.version}")
        print(f"  Instructions: {len(isa_def.instructions)}")
        print(f"  Directives: {len(isa_def.directives)}")
        
        # Check which directives have implementations
        executor = get_directive_executor()
        for directive_name, directive in isa_def.directives.items():
            if directive.implementation:
                print(f"  ✓ {directive_name}: Has custom implementation")
                print(f"    Description: {directive.description}")
                print(f"    Syntax: {directive.syntax}")
            else:
                print(f"  - {directive_name}: No custom implementation")
        
        return isa_def
    except Exception as e:
        print(f"✗ Failed to load ISA: {e}")
        return None


def test_custom_directive_execution():
    """Test executing custom directive implementations"""
    print("\n=== Testing Custom Directive Execution ===")
    
    executor = get_directive_executor()
    
    # Test .magic directive
    print("Testing .magic directive:")
    try:
        # Create a mock context for testing
        class MockAssembler:
            def __init__(self):
                self.context = type('obj', (object,), {'current_address': 0})()
                self.symbol_table = type('obj', (object,), {'set_current_address': lambda x: None})()
        
        context = DirectiveContext(
            assembler=MockAssembler(),
            symbol_table=None,
            memory=bytearray(),
            current_address=0x100,
            section="text",
            args=["42"],
            extra={}
        )
        
        result = executor.execute_directive(".magic", context)
        print(f"  Input: .magic 42")
        print(f"  Output: {result.hex() if result else 'None'}")
        print(f"  New address: {context.current_address}")
        
    except Exception as e:
        print(f"  ✗ Error executing .magic: {e}")
    
    # Test .repeat directive
    print("\nTesting .repeat directive:")
    try:
        context = DirectiveContext(
            assembler=MockAssembler(),
            symbol_table=None,
            memory=bytearray(),
            current_address=0x104,
            section="text",
            args=["0xFF", "4"],
            extra={}
        )
        
        result = executor.execute_directive(".repeat", context)
        print(f"  Input: .repeat 0xFF 4")
        print(f"  Output: {result.hex() if result else 'None'}")
        print(f"  New address: {context.current_address}")
        
    except Exception as e:
        print(f"  ✗ Error executing .repeat: {e}")


def test_assembly_with_custom_directives():
    """Test assembling code with custom directives"""
    print("\n=== Testing Assembly with Custom Directives ===")
    
    # Load ISA
    loader = ISALoader()
    isa_def = loader.load_isa_from_file("src/isa_definitions/custom_isa_example.json")
    
    # Create assembler
    assembler = Assembler(isa_def)
    
    # Test assembly code with custom directives
    assembly_code = """
    ; Test program with custom directives
    .org 0x100
    
    start:
        LI x6, 10          ; Load immediate 10
        MULT x6, x7        ; Custom multiply instruction
        SWAP x6, x7        ; Custom swap instruction
    
    data_section:
        .magic 42          ; Custom directive: creates magic data
        .repeat 0xFF 4     ; Custom directive: repeats value
        .word 0x1234       ; Standard directive
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
            else:
                print(f"    0x{i:04X}: 0x{result.machine_code[i]:02X}")
        
        # Show the raw bytes for data section
        print("  Raw bytes (including directive data):")
        for i in range(0, len(result.machine_code), 16):
            chunk = result.machine_code[i:i+16]
            hex_bytes = ' '.join(f'{b:02X}' for b in chunk)
            print(f"    0x{i:04X}: {hex_bytes}")
        
    except Exception as e:
        print(f"✗ Assembly failed: {e}")


def test_cli_with_custom_directives():
    """Test CLI with custom directives"""
    print("\n=== Testing CLI with Custom Directives ===")
    
    try:
        # Test the actual CLI command
        import subprocess
        result = subprocess.run([
            'python3', '-m', 'isa_xform.cli', 'assemble',
            '--isa', 'custom_isa_example',
            '--input', 'test_custom_directives.s',
            '--output', 'test_custom_directives.bin',
            '--verbose'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ CLI assembly successful!")
            print("  Output:")
            print(result.stdout)
            
            # Check if the output file was created
            if os.path.exists('test_custom_directives.bin'):
                with open('test_custom_directives.bin', 'rb') as f:
                    data = f.read()
                print(f"  Generated file size: {len(data)} bytes")
                print(f"  File contents (hex): {data.hex()}")
        else:
            print("✗ CLI assembly failed:")
            print(result.stderr)
            
    except Exception as e:
        print(f"✗ CLI test failed: {e}")


def test_directive_implementation_validation():
    """Test validation of directive implementations"""
    print("\n=== Testing Directive Implementation Validation ===")
    
    executor = get_directive_executor()
    
    # Test invalid implementation
    print("Testing invalid directive implementation:")
    try:
        executor.compile_implementation("INVALID_DIRECTIVE", "this is not valid python code {")
        print("  ✗ Should have failed")
    except Exception as e:
        print(f"  ✓ Correctly caught error: {e}")
    
    # Test valid implementation
    print("\nTesting valid directive implementation:")
    try:
        valid_code = "# Valid directive implementation\nresult = bytearray([0x42])\ncontext.current_address += 1"
        executor.compile_implementation("VALID_DIRECTIVE", valid_code)
        print("  ✓ Successfully compiled valid implementation")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")


def main():
    """Main test function"""
    print("Custom Directive Implementation Test Suite")
    print("=" * 60)
    
    # Test 1: Loading custom ISA with directives
    isa_def = test_custom_directive_loading()
    if not isa_def:
        print("Failed to load ISA, aborting tests")
        return
    
    # Test 2: Executing custom directives
    test_custom_directive_execution()
    
    # Test 3: Assembly with custom directives
    test_assembly_with_custom_directives()
    
    # Test 4: CLI with custom directives
    test_cli_with_custom_directives()
    
    # Test 5: Implementation validation
    test_directive_implementation_validation()
    
    print("\n" + "=" * 60)
    print("Custom directive test suite completed!")


if __name__ == "__main__":
    main() 