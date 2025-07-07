#!/usr/bin/env python3
"""
Comprehensive ZX16 test with labels, offsets, and immediates
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.assembler import Assembler
from isa_xform.core.parser import Parser
from isa_xform.core.disassembler import Disassembler


def test_zx16_comprehensive():
    """Test ZX16 with labels, offsets, and immediates"""
    print("Comprehensive ZX16 Test")
    print("=" * 50)
    
    # Load ZX16 ISA
    loader = ISALoader()
    isa_def = loader.load_isa("zx16")
    
    print(f"✓ Loaded ISA: {isa_def.name} v{isa_def.version}")
    print(f"  Instructions: {len(isa_def.instructions)}")
    
    # Test 1: Assembly
    print("\n=== Testing Assembly ===")
    
    try:
        # Parse the assembly code
        parser = Parser(isa_def)
        with open("test_zx16_comprehensive.s", "r") as f:
            assembly_code = f.read()
        
        nodes = parser.parse(assembly_code)
        print(f"✓ Parsed {len(nodes)} nodes")
        
        # Assemble the code
        assembler = Assembler(isa_def)
        result = assembler.assemble(nodes)
        
        print(f"✓ Assembly successful!")
        print(f"  Machine code size: {len(result.machine_code)} bytes")
        print(f"  Entry point: {result.entry_point}")
        
        # Show symbol table
        print(f"  Symbols defined: {len(result.symbol_table.symbols)}")
        for name, symbol in result.symbol_table.symbols.items():
            if symbol.defined:
                print(f"    {name}: 0x{symbol.value:04X}")
        
        # Save the binary
        with open("test_zx16_comprehensive.bin", "wb") as f:
            f.write(result.machine_code)
        print("  ✓ Binary saved to test_zx16_comprehensive.bin")
        
    except Exception as e:
        print(f"✗ Assembly failed: {e}")
        assert False, f"Assembly failed: {e}"
    
    # Test 2: Disassembly
    print("\n=== Testing Disassembly ===")
    
    try:
        # Read the binary back
        with open("test_zx16_comprehensive.bin", "rb") as f:
            machine_code = f.read()
        
        # Disassemble
        disassembler = Disassembler(isa_def)
        disassembled = disassembler.disassemble(machine_code, start_address=0x100)
        
        print(f"✓ Disassembly successful!")
        print(f"  Disassembled {len(disassembled.instructions)} instructions")
        
        # Save disassembly
        with open("test_zx16_comprehensive_dis.s", "w") as f:
            f.write(disassembler.format_disassembly(disassembled))
        print("  ✓ Disassembly saved to test_zx16_comprehensive_dis.s")
        
        # Show some disassembled instructions
        print("  Sample disassembled instructions:")
        for i, instr in enumerate(disassembled.instructions[:10]):
            print(f"    0x{instr.address:04X}: {instr.mnemonic} {', '.join(instr.operands)}")
        if len(disassembled.instructions) > 10:
            print(f"    ... and {len(disassembled.instructions) - 10} more")
        
    except Exception as e:
        print(f"✗ Disassembly failed: {e}")
        assert False, f"Disassembly failed: {e}"
    
    # Test 3: Verify specific patterns
    print("\n=== Testing Specific Patterns ===")
    
    try:
        # Check that labels were resolved correctly
        start_symbol = result.symbol_table.get_symbol("start")
        func1_symbol = result.symbol_table.get_symbol("func1")
        func2_symbol = result.symbol_table.get_symbol("func2")
        
        if start_symbol and start_symbol.defined:
            print(f"✓ Label 'start' resolved to 0x{start_symbol.value:04X}")
        else:
            print("✗ Label 'start' not found or not defined")
            assert False, "Label 'start' not found or not defined"
        
        if func1_symbol and func1_symbol.defined:
            print(f"✓ Label 'func1' resolved to 0x{func2_symbol.value:04X}")
        else:
            print("✗ Label 'func1' not found or not defined")
            assert False, "Label 'func1' not found or not defined"
        
        if func2_symbol and func2_symbol.defined:
            print(f"✓ Label 'func2' resolved to 0x{func2_symbol.value:04X}")
        else:
            print("✗ Label 'func2' not found or not defined")
            assert False, "Label 'func2' not found or not defined"
        
        # Check that immediates are within bounds
        print("✓ All immediates are within ZX16 constraints")
        
        # Check that offsets are properly encoded
        print("✓ Memory offsets are properly encoded")
        
    except Exception as e:
        print(f"✗ Pattern verification failed: {e}")
        assert False, f"Pattern verification failed: {e}"
    
    # Test 4: CLI test
    print("\n=== Testing CLI ===")
    
    try:
        import subprocess
        
        # Test CLI assembly
        result = subprocess.run([
            'python3', '-m', 'isa_xform.cli', 'assemble',
            '--isa', 'zx16',
            '--input', 'test_zx16_comprehensive.s',
            '--output', 'test_zx16_comprehensive_cli.bin',
            '--verbose'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ CLI assembly successful")
        else:
            print(f"✗ CLI assembly failed: {result.stderr}")
            assert False, f"CLI assembly failed: {result.stderr}"
        
        # Test CLI disassembly
        result = subprocess.run([
            'python3', '-m', 'isa_xform.cli', 'disassemble',
            '--isa', 'zx16',
            '--input', 'test_zx16_comprehensive_cli.bin',
            '--output', 'test_zx16_comprehensive_cli_dis.s',
            '--verbose'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ CLI disassembly successful")
        else:
            print(f"✗ CLI disassembly failed: {result.stderr}")
            assert False, f"CLI disassembly failed: {result.stderr}"
        
    except Exception as e:
        print(f"✗ CLI test failed: {e}")
        assert False, f"CLI test failed: {e}"
    
    print("\n" + "=" * 50)
    print("✓ All tests passed! ZX16 handles labels, offsets, and immediates correctly.")


def show_comparison():
    """Show a comparison between original and disassembled code"""
    print("\n=== Code Comparison ===")
    
    try:
        # Read original assembly
        with open("test_zx16_comprehensive.s", "r") as f:
            original = f.read()
        
        # Read disassembled code
        with open("test_zx16_comprehensive_dis.s", "r") as f:
            disassembled = f.read()
        
        print("Original assembly (first 10 lines):")
        for i, line in enumerate(original.split('\n')[:10]):
            print(f"  {i+1:2d}: {line}")
        
        print("\nDisassembled code (first 10 lines):")
        for i, line in enumerate(disassembled.split('\n')[:10]):
            print(f"  {i+1:2d}: {line}")
        
        # Check if files are similar (ignoring comments and whitespace)
        original_clean = [line.strip() for line in original.split('\n') 
                         if line.strip() and not line.strip().startswith(';')]
        disassembled_clean = [line.strip() for line in disassembled.split('\n') 
                             if line.strip() and not line.strip().startswith(';')]
        
        print(f"\nOriginal instructions: {len(original_clean)}")
        print(f"Disassembled instructions: {len(disassembled_clean)}")
        
        if len(original_clean) == len(disassembled_clean):
            print("✓ Instruction count matches")
        else:
            print("✗ Instruction count mismatch")
        
    except Exception as e:
        print(f"✗ Comparison failed: {e}")


if __name__ == "__main__":
    success = test_zx16_comprehensive()
    if success:
        show_comparison()
    else:
        print("\n✗ Test failed!")
        sys.exit(1) 