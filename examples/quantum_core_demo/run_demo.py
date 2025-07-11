#!/usr/bin/env python3
"""
QuantumCore ISA Demo Runner

This script demonstrates the full workflow of the py-isa-xform toolkit
with the custom QuantumCore ISA.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Success!")
        if result.stdout:
            print("Output:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Error!")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("Stdout:")
            print(e.stdout)
        if e.stderr:
            print("Stderr:")
            print(e.stderr)
        return False

def main():
    """Main demo function"""
    print("🚀 QuantumCore ISA Demo")
    print("=" * 60)
    
    # Get the demo directory and project root
    demo_dir = Path(__file__).parent
    project_root = demo_dir.parent.parent
    
    print(f"Working directory: {demo_dir}")
    print(f"Project root: {project_root}")
    
    # Change to project root for CLI commands
    os.chdir(project_root)
    
    # Check if files exist
    required_files = [
        demo_dir / "quantum_core_isa.json",
        demo_dir / "quantum_core_test.s"
    ]
    
    for file in required_files:
        if not file.exists():
            print(f"❌ Missing required file: {file}")
            return False
    
    print("✅ All required files found")
    
    # Step 1: Assemble the test program
    assemble_cmd = [
        sys.executable, "-m", "src.isa_xform.cli", "assemble",
        "--isa", str(demo_dir / "quantum_core_isa.json"),
        "--input", str(demo_dir / "quantum_core_test.s"),
        "--output", str(demo_dir / "quantum_core_test.bin"),
        "--verbose"
    ]
    
    if not run_command(assemble_cmd, "Assembling QuantumCore test program"):
        return False
    
    # Step 2: Disassemble the binary
    disassemble_cmd = [
        sys.executable, "-m", "src.isa_xform.cli", "disassemble",
        "--isa", str(demo_dir / "quantum_core_isa.json"),
        "--input", str(demo_dir / "quantum_core_test.bin"),
        "--show-addresses",
        "--output", str(demo_dir / "quantum_core_test_dis.s"),
        "--verbose"
    ]
    
    if not run_command(disassemble_cmd, "Disassembling QuantumCore binary"):
        return False
    
    # Step 3: Show file sizes
    print(f"\n{'='*60}")
    print("File Information")
    print('='*60)
    
    files_to_check = [
        demo_dir / "quantum_core_test.s",
        demo_dir / "quantum_core_test.bin", 
        demo_dir / "quantum_core_test_dis.s"
    ]
    
    for file in files_to_check:
        if file.exists():
            size = file.stat().st_size
            print(f"📄 {file.name}: {size} bytes")
        else:
            print(f"❌ {file.name}: Not found")
    
    # Step 4: Show a sample of the disassembly
    print(f"\n{'='*60}")
    print("Sample Disassembly Output")
    print('='*60)
    
    disasm_file = demo_dir / "quantum_core_test_dis.s"
    if disasm_file.exists():
        with open(disasm_file, "r") as f:
            lines = f.readlines()
            # Show first 20 lines
            for i, line in enumerate(lines[:20]):
                print(f"{i+1:2d}: {line.rstrip()}")
            if len(lines) > 20:
                print(f"... and {len(lines) - 20} more lines")
    else:
        print("❌ Disassembly file not found")
    
    print(f"\n{'='*60}")
    print("🎉 Demo completed successfully!")
    print("=" * 60)
    print("\nFiles generated:")
    print("  • quantum_core_test.bin - Assembled binary")
    print("  • quantum_core_test_dis.s - Disassembled output")
    print("\nYou can now:")
    print("  • Examine the binary file")
    print("  • Compare original vs disassembled code")
    print("  • Modify the ISA definition and test again")
    print("  • Create your own custom ISA!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 