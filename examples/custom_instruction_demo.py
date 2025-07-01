#!/usr/bin/env python3
"""
Custom Instruction Demo
Demonstrates how to create and use custom instruction implementations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.assembler import Assembler
from isa_xform.core.parser import Parser
from isa_xform.core.instruction_executor import get_instruction_executor, ExecutionContext


def create_custom_isa():
    """Create a custom ISA definition with user-defined instructions"""
    
    # Example: User wants to add a custom instruction for bit manipulation
    custom_isa = {
        "name": "UserCustomISA",
        "version": "1.0",
        "description": "User-defined ISA with custom bit manipulation instructions",
        "instruction_size": 16,
        "word_size": 16,
        "endianness": "little",
        "address_space": {
            "size": 65536,
            "default_code_start": 32
        },
        "registers": {
            "general_purpose": [
                {"name": "x0", "size": 16, "alias": ["zero"], "description": "Always zero"},
                {"name": "x1", "size": 16, "alias": ["ra"], "description": "Return address"},
                {"name": "x2", "size": 16, "alias": ["sp"], "description": "Stack pointer"},
                {"name": "x3", "size": 16, "alias": ["s0"], "description": "Saved/Frame pointer"},
                {"name": "x4", "size": 16, "alias": ["s1"], "description": "Saved"},
                {"name": "x5", "size": 16, "alias": ["t1"], "description": "Temporary"},
                {"name": "x6", "size": 16, "alias": ["a0"], "description": "Argument 0/Return value"},
                {"name": "x7", "size": 16, "alias": ["a1"], "description": "Argument 1"}
            ]
        },
        "instructions": [
            # Standard ADD instruction
            {
                "mnemonic": "ADD",
                "format": "R-type",
                "description": "Add registers",
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
                }
            },
            # User's custom bit manipulation instruction
            {
                "mnemonic": "BITREV",
                "format": "R-type",
                "description": "Reverse bits in register (user-defined)",
                "syntax": "BITREV rd, rs2",
                "semantics": "rd = reverse_bits(rs2)",
                "implementation": """
# User's custom bit reversal implementation
def reverse_bits_16(value):
    result = 0
    for i in range(16):
        if value & (1 << i):
            result |= (1 << (15 - i))
    return result

rs2_val = read_register(operands['rs2'])
reversed_val = reverse_bits_16(rs2_val)
write_register(operands['rd'], reversed_val)

# Set flags based on result
set_flag('Z', reversed_val == 0)
set_flag('N', (reversed_val & 0x8000) != 0)
""",
                "encoding": {
                    "fields": [
                        {"name": "funct4", "bits": "15:12", "value": "1010"},
                        {"name": "rs2", "bits": "11:9", "type": "register"},
                        {"name": "rd", "bits": "8:6", "type": "register"},
                        {"name": "func3", "bits": "5:3", "value": "000"},
                        {"name": "opcode", "bits": "2:0", "value": "000"}
                    ]
                }
            },
            # User's custom population count instruction
            {
                "mnemonic": "POPCNT",
                "format": "R-type",
                "description": "Count set bits in register (user-defined)",
                "syntax": "POPCNT rd, rs2",
                "semantics": "rd = count_set_bits(rs2)",
                "implementation": """
# User's custom population count implementation
def count_set_bits(value):
    count = 0
    for i in range(16):
        if value & (1 << i):
            count += 1
    return count

rs2_val = read_register(operands['rs2'])
bit_count = count_set_bits(rs2_val)
write_register(operands['rd'], bit_count)

# Set flags
set_flag('Z', bit_count == 0)
set_flag('N', False)  # Population count is never negative
""",
                "encoding": {
                    "fields": [
                        {"name": "funct4", "bits": "15:12", "value": "1011"},
                        {"name": "rs2", "bits": "11:9", "type": "register"},
                        {"name": "rd", "bits": "8:6", "type": "register"},
                        {"name": "func3", "bits": "5:3", "value": "000"},
                        {"name": "opcode", "bits": "2:0", "value": "000"}
                    ]
                }
            }
        ],
        "assembly_syntax": {
            "comment_char": ";",
            "label_suffix": ":",
            "register_prefix": "",
            "immediate_prefix": "#",
            "hex_prefix": "0x",
            "binary_prefix": "0b",
            "case_sensitive": False
        }
    }
    
    return custom_isa


def demo_custom_instructions():
    """Demonstrate the custom instructions"""
    print("Custom Instruction Demo")
    print("=" * 40)
    
    # Create the custom ISA
    custom_isa_data = create_custom_isa()
    
    # Save it to a temporary file
    import json
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(custom_isa_data, f, indent=2)
        temp_file = f.name
    
    try:
        # Load the custom ISA
        loader = ISALoader()
        isa_def = loader.load_isa_from_file(temp_file)
        
        print(f"✓ Loaded custom ISA: {isa_def.name}")
        print(f"  Instructions: {len(isa_def.instructions)}")
        
        # Show custom instructions
        for instruction in isa_def.instructions:
            if instruction.implementation:
                print(f"  ✓ {instruction.mnemonic}: {instruction.description}")
        
        # Test execution
        print("\nTesting Custom Instructions:")
        
        # Create execution context
        context = ExecutionContext(
            registers={'x0': 0, 'x1': 0, 'x2': 0, 'x3': 0, 'x4': 0, 'x5': 0, 'x6': 0, 'x7': 0x1234},
            memory=bytearray(1024),
            pc=0,
            flags={}
        )
        
        executor = get_instruction_executor()
        
        # Test BITREV instruction
        print(f"\nTesting BITREV:")
        print(f"  Input: x7 = 0x{context.registers['x7']:04X}")
        
        operands = {'rd': 'x6', 'rs2': 'x7'}
        executor.execute_instruction('BITREV', context, operands)
        
        print(f"  Output: x6 = 0x{context.registers['x6']:04X}")
        print(f"  Flags: {context.flags}")
        
        # Test POPCNT instruction
        print(f"\nTesting POPCNT:")
        print(f"  Input: x7 = 0x{context.registers['x7']:04X}")
        
        operands = {'rd': 'x5', 'rs2': 'x7'}
        executor.execute_instruction('POPCNT', context, operands)
        
        print(f"  Output: x5 = {context.registers['x5']} (set bits)")
        print(f"  Flags: {context.flags}")
        
        # Test assembly
        print(f"\nTesting Assembly:")
        
        assembly_code = """
        ; Test program with user's custom instructions
        .org 0x100
        
        start:
            ADD x6, x7      ; Standard add
            BITREV x6, x7   ; User's bit reverse
            POPCNT x5, x7   ; User's population count
        """
        
        print("Assembly code:")
        print(assembly_code)
        
        # Parse and assemble
        parser = Parser(isa_def)
        nodes = parser.parse(assembly_code)
        
        assembler = Assembler(isa_def)
        result = assembler.assemble(nodes)
        
        print(f"✓ Assembly successful!")
        print(f"  Machine code size: {len(result.machine_code)} bytes")
        
        # Show machine code
        print("  Machine code:")
        for i in range(0, len(result.machine_code), 2):
            if i + 1 < len(result.machine_code):
                word = result.machine_code[i] | (result.machine_code[i + 1] << 8)
                print(f"    0x{i:04X}: 0x{word:04X}")
        
        print(f"\n✓ Demo completed successfully!")
        print(f"  User can now use BITREV and POPCNT instructions in their assembly code")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        # Clean up temporary file
        os.unlink(temp_file)


if __name__ == "__main__":
    demo_custom_instructions() 