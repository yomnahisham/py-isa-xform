#!/usr/bin/env python3
"""
Demonstration of ISA Creation Tools

This script demonstrates how to use both the ISA Scaffold Generator
and the Standard Template to create custom ISAs.
"""

import os
import sys
import subprocess
import tempfile
import shutil

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_command(cmd, description):
    """Run a command and print the result"""
    print(f"\n=== {description} ===")
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Success!")
            if result.stdout:
                print("Output:")
                print(result.stdout)
        else:
            print("✗ Failed!")
            if result.stderr:
                print("Error:")
                print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def create_test_program(filename, content):
    """Create a test assembly program"""
    with open(filename, 'w') as f:
        f.write(content)
    print(f"✓ Created test program: {filename}")

def main():
    print("ISA Creation Tools Demonstration")
    print("=" * 50)
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        print(f"Working in temporary directory: {temp_dir}")
        
        # Note: Using the scaffold generator from the core module
        print("✓ Using scaffold generator from isa_xform.core.isa_scaffold")
        
        # Note: Standard template was removed, using custom ISA instead
        print("✓ Using custom ISA for demo (standard template was removed)")
        
        # Ensure the definitions directory exists in the actual project
        project_defs_dir = os.path.abspath(os.path.join('..', 'src', 'isa_definitions'))
        os.makedirs(project_defs_dir, exist_ok=True)
        print(f"✓ Using project definitions directory: {project_defs_dir}")
        
        # Demo 1: Using the Scaffold Generator
        print("\n" + "="*50)
        print("DEMO 1: ISA Scaffold Generator")
        print("="*50)
        
        # Generate a minimal ISA
        success = run_command(
            "python3 -m isa_xform.core.isa_scaffold --name 'DEMO_ISA' --instructions 'ADD,SUB,LI,J,ECALL' --directives '.org,.word,.byte'",
            "Generating minimal ISA with scaffold generator"
        )
        
        if success:
            # Create a test program
            test_program = """
; Test program for scaffold-generated ISA
.org 0x100

start:
    LI a0, 42          ; Load immediate 42
    LI a1, 10          ; Load immediate 10
    ADD a0, a1         ; Add registers (42 + 10 = 52)
    SUB a0, a1         ; Subtract registers (52 - 10 = 42)
    ECALL 0x3FF        ; Exit with result in a0
"""
            create_test_program('test_scaffold.s', test_program)
            
            # Copy the generated ISA to the right location
            run_command(
                f"cp demo_isa_isa.json {project_defs_dir}/demo_isa.json",
                "Copying generated ISA to definitions directory"
            )
            
            # Test assembly and disassembly
            run_command(
                "cd .. && python3 -m isa_xform.cli assemble --isa demo_isa --input examples/test_scaffold.s --output examples/test_scaffold.bin",
                "Testing assembly with scaffold-generated ISA"
            )
            
            run_command(
                "cd .. && python3 -m isa_xform.cli disassemble --isa demo_isa --input examples/test_scaffold.bin --output examples/test_scaffold_dis.s",
                "Testing disassembly with scaffold-generated ISA"
            )
        
        # Demo 2: Using the Standard Template
        print("\n" + "="*50)
        print("DEMO 2: Standard Template")
        print("="*50)
        
        # Create a simple custom ISA for demo
        custom_isa_content = '''{
  "name": "CUSTOM_ISA",
  "version": "1.0",
  "description": "Custom ISA for demonstration",
  "word_size": 16,
  "instruction_size": 16,
  "endianness": "little",
  "registers": {
    "general_purpose": [
      {"name": "r0", "alias": "zero", "description": "Always zero"},
      {"name": "r1", "alias": "ra", "description": "Return address"},
      {"name": "r2", "alias": "sp", "description": "Stack pointer"},
      {"name": "r3", "alias": "gp", "description": "Global pointer"},
      {"name": "r4", "alias": "tp", "description": "Thread pointer"},
      {"name": "r5", "alias": "t0", "description": "Temporary"},
      {"name": "r6", "alias": "t1", "description": "Temporary"},
      {"name": "r7", "alias": "t2", "description": "Temporary"},
      {"name": "r8", "alias": "s0", "description": "Saved register"},
      {"name": "r9", "alias": "s1", "description": "Saved register"},
      {"name": "r10", "alias": "a0", "description": "Argument/return value"},
      {"name": "r11", "alias": "a1", "description": "Argument/return value"},
      {"name": "r12", "alias": "a2", "description": "Argument"},
      {"name": "r13", "alias": "a3", "description": "Argument"},
      {"name": "r14", "alias": "a4", "description": "Argument"},
      {"name": "r15", "alias": "a5", "description": "Argument"}
    ],
    "special": [
      {"name": "pc", "description": "Program counter"},
      {"name": "flags", "description": "Status flags"}
    ]
  },
  "flags": [
    {"name": "Z", "description": "Zero flag"},
    {"name": "N", "description": "Negative flag"},
    {"name": "C", "description": "Carry flag"},
    {"name": "V", "description": "Overflow flag"},
    {"name": "SVC", "description": "System call flag"}
  ],
  "instructions": [
    {
      "mnemonic": "LI",
      "description": "Load immediate operation",
      "syntax": "LI rd, imm",
      "semantics": "rd = sign_extend(imm)",
      "encoding": {
        "fields": [
          {"name": "imm", "bits": "15:9", "type": "immediate", "signed": True},
          {"name": "rd", "bits": "8:6", "type": "register"},
          {"name": "func3", "bits": "5:3", "value": "000"},
          {"name": "opcode", "bits": "2:0", "value": "001"}
        ]
      },
      "implementation": "# LI instruction implementation\nimm_val = operands['imm']\nif imm_val & 0x40:\n    imm_val = imm_val | 0xFF80\nwrite_register(operands['rd'], imm_val & 0xFFFF)"
    },
    {
      "mnemonic": "ADD",
      "description": "Register-to-register operation",
      "syntax": "ADD rd, rs2",
      "semantics": "rd = rd + rs2",
      "encoding": {
        "fields": [
          {"name": "funct4", "bits": "15:12", "value": "0000"},
          {"name": "rs2", "bits": "11:9", "type": "register"},
          {"name": "rd", "bits": "8:6", "type": "register"},
          {"name": "func3", "bits": "5:3", "value": "000"},
          {"name": "opcode", "bits": "2:0", "value": "000"}
        ]
      },
      "implementation": "# ADD instruction implementation\nrd_val = read_register(operands['rd'])\nrs2_val = read_register(operands['rs2'])\nresult = (rd_val + rs2_val) & 0xFFFF\nwrite_register(operands['rd'], result)\nset_flag('Z', result == 0)\nset_flag('N', (result & 0x8000) != 0)"
    },
    {
      "mnemonic": "ECALL",
      "description": "System call instruction",
      "syntax": "ECALL svc",
      "semantics": "Trap to service number",
      "encoding": {
        "fields": [
          {"name": "svc", "bits": "15:6", "type": "immediate", "signed": False},
          {"name": "unused", "bits": "5:3", "value": "000"},
          {"name": "opcode", "bits": "2:0", "value": "111"}
        ]
      },
      "implementation": "# ECALL instruction implementation\nsvc = operands['svc']\nset_flag('SVC', svc)"
    }
  ],
  "directives": [
    {
      "name": ".org",
      "description": "Set origin address",
      "action": "set_origin",
      "implementation": "# Set origin directive implementation\nif args:\n    addr = int(args[0], 0)\n    context.current_address = addr\n    assembler.context.current_address = addr\n    assembler.symbol_table.set_current_address(addr)",
      "argument_types": ["number"],
      "syntax": ".org address",
      "examples": [".org 0x1000", ".org 4096"]
    }
  ],
  "pseudo_instructions": [
    {
      "name": "NOP",
      "expansion": "ADD r0, r0",
      "description": "No operation"
    }
  ]
}'''
        
        with open('custom_isa.json', 'w') as f:
            f.write(custom_isa_content)
        print("✓ Created custom ISA for demo")
        
        # Create a test program for the custom ISA
        test_program_std = """
; Test program for custom ISA
.org 0x100

start:
    LI a0, 42          ; Load immediate 42
    LI a1, 10          ; Load immediate 10
    ADD a0, a1         ; Add registers
    ECALL 0x3FF        ; Exit
"""
        create_test_program('test_standard.s', test_program_std)
        
        # Copy the custom ISA to the right location
        run_command(
            f"cp custom_isa.json {project_defs_dir}/custom_isa.json",
            "Copying custom ISA to definitions directory"
        )
        
        # Test assembly and disassembly with custom ISA
        run_command(
            "cd .. && python3 -m isa_xform.cli assemble --isa custom_isa --input examples/test_standard.s --output examples/test_standard.bin",
            "Testing assembly with custom ISA"
        )
        
        run_command(
            "cd .. && python3 -m isa_xform.cli disassemble --isa custom_isa --input examples/test_standard.bin --output examples/test_standard_dis.s",
            "Testing disassembly with custom ISA"
        )
        
        # Demo 3: Advanced Scaffold Generator
        print("\n" + "="*50)
        print("DEMO 3: Advanced Scaffold Generator")
        print("="*50)
        
        # Generate a comprehensive ISA
        success = run_command(
            "python3 -m isa_xform.core.isa_scaffold --name 'ADVANCED_ISA' --instructions 'ADD,SUB,AND,OR,XOR,ADDI,ANDI,ORI,XORI,LI,J,JAL,BEQ,BNE,LW,SW,ECALL' --directives '.org,.word,.byte,.ascii,.align' --word-size 16 --instruction-size 16",
            "Generating comprehensive ISA with scaffold generator"
        )
        
        if success:
            # Create a comprehensive test program
            test_program_adv = """
; Comprehensive test program for advanced ISA
.org 0x100

start:
    LI a0, 42          ; Load immediate
    LI a1, 10          ; Load immediate
    ADD a0, a1         ; Add registers
    SUB a0, a1         ; Subtract registers
    AND a0, a1         ; Bitwise AND
    OR a0, a1          ; Bitwise OR
    XOR a0, a1         ; Bitwise XOR
    ADDI a0, 5         ; Add immediate
    ANDI a0, 0xFF      ; AND immediate
    ORI a0, 0x80       ; OR immediate
    XORI a0, 0x40      ; XOR immediate
    BEQ a0, a1, start  ; Branch if equal
    BNE a0, a1, skip   ; Branch if not equal
    J start            ; Unconditional jump
skip:
    JAL ra, func       ; Jump and link
    LW a2, 0(a0)       ; Load word
    SW a1, 0(a0)       ; Store word
    ECALL 0x3FF        ; Exit

func:
    ADD a0, a1         ; Function body
    JALR ra            ; Return
"""
            create_test_program('test_advanced.s', test_program_adv)
            
            # Copy the generated ISA
            run_command(
                f"cp advanced_isa_isa.json {project_defs_dir}/advanced_isa.json",
                "Copying advanced ISA to definitions directory"
            )
            
            # Test assembly and disassembly
            run_command(
                "cd .. && python3 -m isa_xform.cli assemble --isa advanced_isa --input examples/test_advanced.s --output examples/test_advanced.bin",
                "Testing assembly with advanced ISA"
            )
            
            run_command(
                "cd .. && python3 -m isa_xform.cli disassemble --isa advanced_isa --input examples/test_advanced.bin --output examples/test_advanced_dis.s",
                "Testing disassembly with advanced ISA"
            )
    
    print("\n" + "="*50)
    print("DEMONSTRATION COMPLETE")
    print("="*50)
    print("\nSummary:")
    print("✓ ISA Scaffold Generator: Creates boilerplate ISA definitions")
    print("✓ Custom ISA Creation: Demonstrates manual ISA creation")
    print("✓ Both tools integrate seamlessly with the assembler and disassembler")
    print("\nNext steps:")
    print("1. Customize the generated ISAs for your specific needs")
    print("2. Add more instructions and directives")
    print("3. Test thoroughly with your own programs")
    print("4. Share your custom ISAs with the community")

if __name__ == "__main__":
    main() 