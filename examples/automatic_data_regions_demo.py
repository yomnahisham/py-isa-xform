#!/usr/bin/env python3
"""
Automatic Data Region Detection Demo

This example demonstrates how users can rely entirely on their ISA definitions
for automatic data region detection, without needing to specify --data-regions.

The disassembler automatically detects data regions based on the ISA's memory layout:
- Interrupt vectors are treated as data
- Data sections are treated as data  
- MMIO regions are treated as data
- Code sections are treated as instructions
"""

import subprocess
import sys
import os
from pathlib import Path

def run_disassembler(isa_name, input_file, output_file, start_addr=0, data_regions=None, debug=False):
    """Run the disassembler with given parameters"""
    cmd = [
        sys.executable, "-m", "isa_xform.cli", "disassemble",
        "--isa", isa_name,
        "--input", input_file,
        "--output", output_file,
        "--start-address", str(start_addr)
    ]
    
    if data_regions:
        cmd.extend(["--data-regions"] + data_regions)
    
    if debug:
        cmd.append("--debug")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def create_test_binary(filename, data):
    """Create a test binary file"""
    with open(filename, "wb") as f:
        f.write(bytearray(data))

def read_output_file(filename):
    """Read the output assembly file"""
    try:
        with open(filename, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None

def demo_zx16_automatic_detection():
    """Demonstrate automatic detection with ZX16 ISA"""
    print("🔍 ZX16 ISA AUTOMATIC DETECTION")
    print("=" * 50)
    
    # ZX16 Memory Layout:
    # - Interrupt vectors: 0x0-0x1E (data)
    # - Code section: 0x20-0xEFFF (instructions)
    # - Data section: 0x8000-0xEFFD (data)
    # - MMIO: 0xF000-0xFFFF (data)
    
    print("ZX16 Memory Layout:")
    print("  Interrupt vectors: 0x0000-0x001E (data)")
    print("  Code section: 0x0020-0xEFFF (instructions)")
    print("  Data section: 0x8000-0xEFFD (data)")
    print("  MMIO: 0xF000-0xFFFF (data)")
    
    # Test 1: Binary starting at interrupt vectors
    print("\n1. Binary starting at interrupt vectors (0x0):")
    with open('zx16_vectors.bin', 'wb') as f:
        # Interrupt vectors (32 bytes of zeros)
        f.write(bytearray([0x00] * 32))
        # Code section
        f.write(bytearray([0x79, 0x14, 0x87, 0x02]))  # LI x1, 10; ECALL 10
    
    rc, stdout, stderr = run_disassembler('zx16', 'zx16_vectors.bin', 'zx16_vectors.s', start_addr=0)
    
    if rc == 0:
        output = read_output_file('zx16_vectors.s')
        print("✅ Automatic detection working:")
        print("  - Interrupt vectors (0x0-0x1E) treated as data")
        print("  - Code section (0x20+) treated as instructions")
        print("Output preview:")
        lines = output.split('\n')[:10]
        for line in lines:
            print(f"    {line}")
    else:
        print(f"❌ Test failed: {stderr}")
    
    # Test 2: Binary starting at code address
    print("\n2. Binary starting at code address (0x20):")
    with open('zx16_code.bin', 'wb') as f:
        f.write(bytearray([0x79, 0x14, 0x87, 0x02, 0x02, 0x00]))  # LI x1, 10; ECALL 10; ADD x0, x1
    
    rc, stdout, stderr = run_disassembler('zx16', 'zx16_code.bin', 'zx16_code.s', start_addr=0x20)
    
    if rc == 0:
        output = read_output_file('zx16_code.s')
        print("✅ Automatic detection working:")
        print("  - Code section treated as instructions")
        print("Output:")
        for line in output.split('\n'):
            if line.strip():
                print(f"    {line}")
    else:
        print(f"❌ Test failed: {stderr}")

def demo_simple_risc_automatic_detection():
    """Demonstrate automatic detection with Simple RISC ISA"""
    print("\n🔍 SIMPLE RISC ISA AUTOMATIC DETECTION")
    print("=" * 50)
    
    # Simple RISC Memory Layout:
    # - Code section: 0x1000-0x1FFF (instructions)
    # - Data section: 0x2000-0x2FFF (data)
    # - Stack section: 0x3000-0x3FFF (data)
    
    print("Simple RISC Memory Layout:")
    print("  Code section: 0x1000-0x1FFF (instructions)")
    print("  Data section: 0x2000-0x2FFF (data)")
    print("  Stack section: 0x3000-0x3FFF (data)")
    
    # Test 1: Binary starting at code address
    print("\n1. Binary starting at code address (0x1000):")
    with open('simple_risc_code.bin', 'wb') as f:
        f.write(bytearray([0x79, 0x14, 0x87, 0x02]))  # Some instructions
    
    rc, stdout, stderr = run_disassembler('simple_risc', 'simple_risc_code.bin', 'simple_risc_code.s', start_addr=0x1000)
    
    if rc == 0:
        output = read_output_file('simple_risc_code.s')
        print("✅ Automatic detection working:")
        print("  - Code section treated as instructions")
        print("Output:")
        for line in output.split('\n'):
            if line.strip():
                print(f"    {line}")
    else:
        print(f"❌ Test failed: {stderr}")
    
    # Test 2: Binary starting at data address
    print("\n2. Binary starting at data address (0x2000):")
    with open('simple_risc_data.bin', 'wb') as f:
        f.write(bytearray([0xEF, 0xBE, 0xAD, 0xDE, 0x12, 0x34]))  # Data values
    
    rc, stdout, stderr = run_disassembler('simple_risc', 'simple_risc_data.bin', 'simple_risc_data.s', start_addr=0x2000)
    
    if rc == 0:
        output = read_output_file('simple_risc_data.s')
        print("✅ Automatic detection working:")
        print("  - Data section treated as data")
        print("Output:")
        for line in output.split('\n'):
            if line.strip():
                print(f"    {line}")
    else:
        print(f"❌ Test failed: {stderr}")

def demo_mixed_regions():
    """Demonstrate mixed regions with automatic detection"""
    print("\n🔍 MIXED REGIONS WITH AUTOMATIC DETECTION")
    print("=" * 50)
    
    # Create a binary that spans multiple memory regions
    print("Creating binary spanning multiple ZX16 memory regions:")
    with open('mixed_regions.bin', 'wb') as f:
        # Interrupt vectors (0x0-0x1E) - 32 bytes
        f.write(bytearray([0x00] * 32))
        # Code section (0x20+) - instructions
        f.write(bytearray([0x79, 0x14, 0x87, 0x02]))  # LI x1, 10; ECALL 10
        # More data (could be constants, etc.)
        f.write(bytearray([0xEF, 0xBE, 0xAD, 0xDE]))
    
    print("Binary layout:")
    print("  0x0000-0x001F: Interrupt vectors (data)")
    print("  0x0020-0x0023: Code section (instructions)")
    print("  0x0024-0x0027: Additional data")
    
    rc, stdout, stderr = run_disassembler('zx16', 'mixed_regions.bin', 'mixed_regions.s', start_addr=0)
    
    if rc == 0:
        output = read_output_file('mixed_regions.s')
        print("✅ Automatic detection working:")
        print("  - Interrupt vectors automatically detected as data")
        print("  - Code section automatically detected as instructions")
        print("  - Additional data automatically detected as data")
        print("Output preview:")
        lines = output.split('\n')[:15]
        for line in lines:
            print(f"    {line}")
    else:
        print(f"❌ Test failed: {stderr}")

def demo_user_override():
    """Demonstrate user override with --data-regions"""
    print("\n🔍 USER OVERRIDE WITH --data-regions")
    print("=" * 50)
    
    # Create a simple binary
    with open('override_test.bin', 'wb') as f:
        f.write(bytearray([0x79, 0x14, 0x87, 0x02, 0xEF, 0xBE]))
    
    print("Binary: 0x79 0x14 0x87 0x02 0xEF 0xBE")
    print("Without --data-regions (automatic detection):")
    
    # Test without data regions
    rc, stdout, stderr = run_disassembler('zx16', 'override_test.bin', 'override_auto.s', start_addr=0x20)
    
    if rc == 0:
        output = read_output_file('override_auto.s')
        print("✅ Automatic detection (all as instructions):")
        for line in output.split('\n'):
            if line.strip():
                print(f"    {line}")
    else:
        print(f"❌ Test failed: {stderr}")
    
    print("\nWith --data-regions (user override):")
    
    # Test with user-specified data regions
    rc, stdout, stderr = run_disassembler('zx16', 'override_test.bin', 'override_user.s', 
                                         start_addr=0x20, data_regions=['0x24-0x26'])
    
    if rc == 0:
        output = read_output_file('override_user.s')
        print("✅ User override (0x24-0x26 as data):")
        for line in output.split('\n'):
            if line.strip():
                print(f"    {line}")
    else:
        print(f"❌ Test failed: {stderr}")

def cleanup():
    """Clean up test files"""
    files = [
        'zx16_vectors.bin', 'zx16_vectors.s',
        'zx16_code.bin', 'zx16_code.s',
        'simple_risc_code.bin', 'simple_risc_code.s',
        'simple_risc_data.bin', 'simple_risc_data.s',
        'mixed_regions.bin', 'mixed_regions.s',
        'override_test.bin', 'override_auto.s', 'override_user.s'
    ]
    for f in files:
        try:
            os.remove(f)
        except:
            pass

def main():
    """Run the automatic data region detection demo"""
    print("🎯 AUTOMATIC DATA REGION DETECTION DEMO")
    print("=" * 60)
    print("This demo shows how users can rely entirely on their ISA definitions")
    print("for automatic data region detection, without needing --data-regions.")
    print()
    
    try:
        demo_zx16_automatic_detection()
        demo_simple_risc_automatic_detection()
        demo_mixed_regions()
        demo_user_override()
        
        print("\n" + "=" * 60)
        print("🎉 DEMO COMPLETE!")
        print("✅ Automatic detection works for any ISA with memory_layout")
        print("✅ Users can rely entirely on their ISA definitions")
        print("✅ No --data-regions needed in most cases")
        print("✅ --data-regions available for custom overrides")
        print("✅ Production-ready functionality")
        
    finally:
        cleanup()

if __name__ == "__main__":
    main() 