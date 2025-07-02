#!/usr/bin/env python3
"""
ISA Scaffold Generator: Creates boilerplate ISA definitions for rapid prototyping
"""

import argparse
import json
import os
import sys
from typing import List, Dict, Any
from pathlib import Path


class ISAScaffoldGenerator:
    """Generates ISA definition scaffolds with boilerplate implementations"""
    
    def __init__(self):
        self.instruction_templates = {
            "R-type": {
                "description": "Register-to-register operation",
                "syntax": "{mnemonic} rd, rs2",
                "semantics": "rd = rd {operation} rs2",
                "encoding": {
                    "fields": [
                        {"name": "funct4", "bits": "15:12", "value": "{opcode}"},
                        {"name": "rs2", "bits": "11:9", "type": "register"},
                        {"name": "rd", "bits": "8:6", "type": "register"},
                        {"name": "func3", "bits": "5:3", "value": "000"},
                        {"name": "opcode", "bits": "2:0", "value": "000"}
                    ]
                },
                "implementation_template": """# {mnemonic} instruction implementation
rd_val = read_register(operands['rd'])
rs2_val = read_register(operands['rs2'])
result = (rd_val {operation} rs2_val) & 0xFFFF
write_register(operands['rd'], result)
# Set flags
set_flag('Z', result == 0)
set_flag('N', (result & 0x8000) != 0)"""
            },
            "I-type": {
                "description": "Register-immediate operation",
                "syntax": "{mnemonic} rd, imm",
                "semantics": "rd = rd {operation} sign_extend(imm)",
                "encoding": {
                    "fields": [
                        {"name": "imm", "bits": "15:9", "type": "immediate", "signed": True},
                        {"name": "rd", "bits": "8:6", "type": "register"},
                        {"name": "func3", "bits": "5:3", "value": "000"},
                        {"name": "opcode", "bits": "2:0", "value": "001"}
                    ]
                },
                "implementation_template": """# {mnemonic} instruction implementation
rd_val = read_register(operands['rd'])
imm_val = operands['imm']
# Sign extend 7-bit immediate
if imm_val & 0x40:
    imm_val = imm_val | 0xFF80
result = (rd_val {operation} imm_val) & 0xFFFF
write_register(operands['rd'], result)
# Set flags
set_flag('Z', result == 0)
set_flag('N', (result & 0x8000) != 0)"""
            },
            "LI-type": {
                "description": "Load immediate operation",
                "syntax": "{mnemonic} rd, imm",
                "semantics": "rd = sign_extend(imm)",
                "encoding": {
                    "fields": [
                        {"name": "imm", "bits": "15:9", "type": "immediate", "signed": True},
                        {"name": "rd", "bits": "8:6", "type": "register"},
                        {"name": "func3", "bits": "5:3", "value": "000"},
                        {"name": "opcode", "bits": "2:0", "value": "001"}
                    ]
                },
                "implementation_template": """# {mnemonic} instruction implementation
imm_val = operands['imm']
# Sign extend 7-bit immediate
if imm_val & 0x40:
    imm_val = imm_val | 0xFF80
write_register(operands['rd'], imm_val & 0xFFFF)"""
            },
            "J-type": {
                "description": "Jump instruction",
                "syntax": "{mnemonic} label",
                "semantics": "PC = label",
                "encoding": {
                    "fields": [
                        {"name": "address", "bits": "15:3", "type": "address"},
                        {"name": "opcode", "bits": "2:0", "value": "010"}
                    ]
                },
                "implementation_template": """# {mnemonic} instruction implementation
target_addr = operands['address']
# Set PC to target address
context.pc = target_addr & 0xFFFF"""
            },
            "SYS-type": {
                "description": "System call instruction",
                "syntax": "{mnemonic} svc",
                "semantics": "Trap to service number",
                "encoding": {
                    "fields": [
                        {"name": "svc", "bits": "15:6", "type": "immediate", "signed": False},
                        {"name": "unused", "bits": "5:3", "value": "000"},
                        {"name": "opcode", "bits": "2:0", "value": "111"}
                    ]
                },
                "implementation_template": """# {mnemonic} instruction implementation
svc = operands['svc']
# Handle system call based on service number
# This is a placeholder - actual implementation would depend on system services
# For now, just store the service number in a special register or flag
set_flag('SVC', svc)
# Could also trigger an interrupt or system call handler here"""
            },
            "JALR-type": {
                "description": "Jump and link register",
                "syntax": "JALR rd, rs1",
                "semantics": "rd = PC + 2; PC = rs1",
                "encoding": {
                    "fields": [
                        {"name": "rs1", "bits": "15:13", "type": "register"},
                        {"name": "rd", "bits": "12:10", "type": "register"},
                        {"name": "opcode", "bits": "2:0", "value": "011"}
                    ]
                },
                "implementation_template": """# {mnemonic} instruction implementation\nrs1_val = read_register(operands['rs1'])\nreturn_addr = context.pc + 2\nwrite_register(operands['rd'], return_addr)\ncontext.pc = rs1_val & 0xFFFF"""
            }
        }
        
        self.directive_templates = {
            ".org": {
                "description": "Set origin address",
                "action": "set_origin",
                "implementation": """# Set origin directive implementation
if args:
    addr = int(args[0], 0)  # Parse as hex/decimal
    context.current_address = addr
    assembler.context.current_address = addr
    assembler.symbol_table.set_current_address(addr)""",
                "argument_types": ["number"],
                "syntax": ".org address",
                "examples": [".org 0x1000", ".org 4096"]
            },
            ".word": {
                "description": "Define word data",
                "action": "define_word",
                "implementation": """# Define word directive implementation
result = bytearray()
for arg in args:
    value = int(arg, 0)  # Parse as hex/decimal
    # Little endian 16-bit word
    result.extend([value & 0xFF, (value >> 8) & 0xFF])
    context.current_address += 2
assembler.context.current_address = context.current_address
assembler.symbol_table.set_current_address(context.current_address)""",
                "argument_types": ["number"],
                "syntax": ".word value1, value2, ...",
                "examples": [".word 0x1234", ".word 42, 0xABCD"]
            },
            ".byte": {
                "description": "Define byte data",
                "action": "define_byte",
                "implementation": """# Define byte directive implementation
result = bytearray()
for arg in args:
    value = int(arg, 0)  # Parse as hex/decimal
    result.append(value & 0xFF)
    context.current_address += 1
assembler.context.current_address = context.current_address
assembler.symbol_table.set_current_address(context.current_address)""",
                "argument_types": ["number"],
                "syntax": ".byte value1, value2, ...",
                "examples": [".byte 0x12", ".byte 65, 66, 67"]
            }
        }
    
    def generate_isa_scaffold(self, name: str, instructions: List[str], directives: List[str] = None,
                             word_size: int = 16, instruction_size: int = 16) -> Dict[str, Any]:
        """Generate a complete ISA scaffold"""
        
        # Generate instruction definitions
        generated_instructions = []
        opcode_counter = 0
        rtype_opcodes = ["0000", "0001", "0010", "0011", "0100", "0101", "0110", "0111", "1000", "1001", "1010", "1011", "1100", "1101", "1110", "1111"]
        rtype_used = 0
        
        for instr in instructions:
            instr_upper = instr.upper()
            
            # Determine instruction type and generate appropriate template
            if instr_upper in ["ADD", "SUB", "AND", "OR", "XOR", "SLT", "SLTU"]:
                template = self.instruction_templates["R-type"]
                operation_map = {
                    "ADD": ("+", rtype_opcodes[0]),
                    "SUB": ("-", rtype_opcodes[1]),
                    "AND": ("&", rtype_opcodes[2]),
                    "OR": ("|", rtype_opcodes[3]),
                    "XOR": ("^", rtype_opcodes[4]),
                    "SLT": ("<", rtype_opcodes[5]),
                    "SLTU": ("<", rtype_opcodes[6])
                }
                operation, opcode = operation_map[instr_upper]
                rtype_used += 1
                
                instruction_def = {
                    "mnemonic": instr_upper,
                    "description": template["description"],
                    "syntax": template["syntax"].format(mnemonic=instr_upper),
                    "semantics": template["semantics"].format(operation=operation),
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper, operation=operation)
                }
                instruction_def["encoding"]["fields"][0]["value"] = opcode
                
            elif instr_upper in ["ADDI", "ANDI", "ORI", "XORI"]:
                template = self.instruction_templates["I-type"]
                operation_map = {
                    "ADDI": "+",
                    "ANDI": "&",
                    "ORI": "|",
                    "XORI": "^"
                }
                operation = operation_map[instr_upper]
                
                instruction_def = {
                    "mnemonic": instr_upper,
                    "description": template["description"],
                    "syntax": template["syntax"].format(mnemonic=instr_upper),
                    "semantics": template["semantics"].format(operation=operation),
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper, operation=operation)
                }
                
            elif instr_upper == "LI":
                template = self.instruction_templates["LI-type"]
                instruction_def = {
                    "mnemonic": instr_upper,
                    "description": template["description"],
                    "syntax": template["syntax"].format(mnemonic=instr_upper),
                    "semantics": template["semantics"],
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper)
                }
                
            elif instr_upper in ["J", "JAL"]:
                template = self.instruction_templates["J-type"]
                instruction_def = {
                    "mnemonic": instr_upper,
                    "description": template["description"],
                    "syntax": template["syntax"].format(mnemonic=instr_upper),
                    "semantics": template["semantics"],
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper)
                }
                
            elif instr_upper in ["ECALL", "EBREAK"]:
                template = self.instruction_templates["SYS-type"]
                instruction_def = {
                    "mnemonic": instr_upper,
                    "description": template["description"],
                    "syntax": template["syntax"].format(mnemonic=instr_upper),
                    "semantics": template["semantics"],
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper)
                }
                
            elif instr_upper == "JALR":
                template = self.instruction_templates["JALR-type"]
                instruction_def = {
                    "mnemonic": instr_upper,
                    "description": template["description"],
                    "syntax": template["syntax"],
                    "semantics": template["semantics"],
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper)
                }
                
            else:
                # Generic instruction template
                instruction_def = {
                    "mnemonic": instr_upper,
                    "description": f"Custom {instr_upper} instruction",
                    "syntax": f"{instr_upper} rd, rs2",
                    "semantics": f"rd = rd + rs2  # Custom operation",
                    "encoding": {
                        "fields": [
                            {"name": "funct4", "bits": "15:12", "value": f"{opcode_counter:04b}"},
                            {"name": "rs2", "bits": "11:9", "type": "register"},
                            {"name": "rd", "bits": "8:6", "type": "register"},
                            {"name": "func3", "bits": "5:3", "value": "000"},
                            {"name": "opcode", "bits": "2:0", "value": "000"}
                        ]
                    },
                    "implementation": f"""# {instr_upper} instruction implementation
rd_val = read_register(operands['rd'])
rs2_val = read_register(operands['rs2'])
result = (rd_val + rs2_val) & 0xFFFF  # Custom operation
write_register(operands['rd'], result)
# Set flags
set_flag('Z', result == 0)
set_flag('N', (result & 0x8000) != 0)"""
                }
                opcode_counter += 1
            
            generated_instructions.append(instruction_def)
        
        # Generate directive definitions
        generated_directives = []
        if directives:
            for directive in directives:
                if directive in self.directive_templates:
                    template = self.directive_templates[directive]
                    directive_def = {
                        "name": directive,
                        "description": template["description"],
                        "action": template["action"],
                        "implementation": template["implementation"],
                        "argument_types": template["argument_types"],
                        "syntax": template["syntax"],
                        "examples": template["examples"]
                    }
                    generated_directives.append(directive_def)
        
        # Create complete ISA definition
        isa_definition = {
            "name": name,
            "version": "1.0",
            "description": f"Generated ISA scaffold for {name}",
            "word_size": word_size,
            "instruction_size": instruction_size,
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
            "instructions": generated_instructions,
            "directives": generated_directives,
            "pseudo_instructions": [
                {
                    "name": "NOP",
                    "expansion": "ADD r0, r0",
                    "description": "No operation"
                },
                {
                    "name": "MV",
                    "expansion": "ADD rd, rs, r0",
                    "description": "Move register"
                },
                {
                    "name": "NOT",
                    "expansion": "XOR rd, rs, -1",
                    "description": "Bitwise NOT"
                }
            ]
        }
        
        return isa_definition
    
    def save_isa_definition(self, isa_definition: Dict[str, Any], output_path: str):
        """Save ISA definition to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(isa_definition, f, indent=2)
    
    def print_usage_instructions(self, isa_name: str, output_path: str):
        """Print usage instructions for the generated ISA"""
        print(f"\n✅ ISA '{isa_name}' generated successfully!")
        print(f"📁 Output file: {output_path}")
        print(f"\n📖 Usage instructions:")
        print(f"1. Copy the generated file to src/isa_definitions/{isa_name.lower()}.json")
        print(f"2. Test the ISA with: python3 -m isa_xform.cli list-isas")
        print(f"3. Assemble code with: python3 -m isa_xform.cli assemble --isa {isa_name.lower()} --input program.s --output program.bin")
        print(f"4. Disassemble code with: python3 -m isa_xform.cli disassemble --isa {isa_name.lower()} --input program.bin --output program.s")


def main():
    """Main entry point for the ISA scaffold generator"""
    parser = argparse.ArgumentParser(
        description="Generate ISA definition scaffolds for rapid prototyping",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a basic ISA
  python3 -m isa_xform.core.isa_scaffold --name "MY_ISA" --instructions "ADD,SUB,LI,J,ECALL" --directives ".org,.word,.byte"

  # Generate a comprehensive ISA
  python3 -m isa_xform.core.isa_scaffold --name "ADVANCED_ISA" \\
    --instructions "ADD,SUB,AND,OR,XOR,ADDI,ANDI,ORI,XORI,LI,J,JAL,BEQ,BNE,LW,SW,ECALL" \\
    --directives ".org,.word,.byte,.ascii,.align" \\
    --word-size 16 \\
    --instruction-size 16
        """
    )
    
    parser.add_argument("--name", required=True, help="Name of the ISA")
    parser.add_argument("--instructions", required=True, 
                       help="Comma-separated list of instructions to include")
    parser.add_argument("--directives", 
                       help="Comma-separated list of directives to include")
    parser.add_argument("--word-size", type=int, default=16, 
                       help="Word size in bits (default: 16)")
    parser.add_argument("--instruction-size", type=int, default=16, 
                       help="Instruction size in bits (default: 16)")
    parser.add_argument("--output", 
                       help="Output file path (default: {name}_isa.json)")
    
    args = parser.parse_args()
    
    # Parse instructions and directives
    instructions = [instr.strip() for instr in args.instructions.split(",")]
    directives = None
    if args.directives:
        directives = [directive.strip() for directive in args.directives.split(",")]
    
    # Generate ISA scaffold
    generator = ISAScaffoldGenerator()
    isa_definition = generator.generate_isa_scaffold(
        name=args.name,
        instructions=instructions,
        directives=directives,
        word_size=args.word_size,
        instruction_size=args.instruction_size
    )
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = f"{args.name.lower()}_isa.json"
    
    # Save ISA definition
    generator.save_isa_definition(isa_definition, output_path)
    generator.print_usage_instructions(args.name, output_path)


if __name__ == "__main__":
    main() 