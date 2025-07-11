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
        # Templates will be generated dynamically based on instruction_size
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
    # Little endian word
    for i in range(word_size // 8):
        result.append((value >> (i * 8)) & 0xFF)
    context.current_address += word_size // 8
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
            },
            ".ascii": {
                "description": "Define ASCII string data",
                "action": "define_ascii",
                "implementation": """# Define ASCII directive implementation
result = bytearray()
for arg in args:
    # Remove quotes and convert to bytes
    if arg.startswith('"') and arg.endswith('"'):
        arg = arg[1:-1]
    result.extend(arg.encode('ascii'))
    context.current_address += len(arg)
assembler.context.current_address = context.current_address
assembler.symbol_table.set_current_address(context.current_address)""",
                "argument_types": ["string"],
                "syntax": '.ascii "string"',
                "examples": ['.ascii "Hello"', '.ascii "World"']
            },
            ".asciiz": {
                "description": "Define null-terminated ASCII string data",
                "action": "define_asciiz",
                "implementation": """# Define ASCIIZ directive implementation
result = bytearray()
for arg in args:
    # Remove quotes and convert to bytes
    if arg.startswith('"') and arg.endswith('"'):
        arg = arg[1:-1]
    result.extend(arg.encode('ascii'))
    result.append(0)  # Null terminator
    context.current_address += len(arg) + 1
assembler.context.current_address = context.current_address
assembler.symbol_table.set_current_address(context.current_address)""",
                "argument_types": ["string"],
                "syntax": '.asciiz "string"',
                "examples": ['.asciiz "Hello"', '.asciiz "World"']
            },
            ".align": {
                "description": "Align to boundary",
                "action": "align",
                "implementation": """# Align directive implementation
if args:
    alignment = int(args[0], 0)
    padding = (alignment - (context.current_address % alignment)) % alignment
    result = bytearray([0] * padding)
    context.current_address += padding
    assembler.context.current_address = context.current_address
    assembler.symbol_table.set_current_address(context.current_address)""",
                "argument_types": ["number"],
                "syntax": ".align boundary",
                "examples": [".align 4", ".align 8"]
            }
        }
    
    def get_instruction_templates(self, instruction_size: int, word_size: int) -> Dict[str, Any]:
        """Generate instruction templates based on instruction size"""
        if instruction_size == 32:
            # 32-bit RISC-V style templates
            return {
                "R-type": {
                    "description": "Register-to-register operation",
                    "syntax": "{mnemonic} rd, rs1, rs2",
                    "semantics": "rd = rs1 {operation} rs2",
                    "encoding": {
                        "fields": [
                            {"name": "funct7", "bits": "31:25", "value": "0000000"},
                            {"name": "rs2", "bits": "24:20", "type": "register"},
                            {"name": "rs1", "bits": "19:15", "type": "register"},
                            {"name": "funct3", "bits": "14:12", "value": "000"},
                            {"name": "rd", "bits": "11:7", "type": "register"},
                            {"name": "opcode", "bits": "6:0", "value": "0110011"}
                        ]
                    },
                    "implementation_template": """# {mnemonic} instruction implementation
rs1_val = read_register(operands['rs1'])
rs2_val = read_register(operands['rs2'])
result = (rs1_val {operation} rs2_val) & {word_mask}
write_register(operands['rd'], result)
# Set flags
set_flag('Z', result == 0)
set_flag('N', (result & 0x80000000) != 0)"""
                },
                "I-type": {
                    "description": "Register-immediate operation",
                    "syntax": "{mnemonic} rd, rs1, imm",
                    "semantics": "rd = rs1 {operation} sign_extend(imm)",
                    "encoding": {
                        "fields": [
                            {"name": "imm", "bits": "31:20", "type": "immediate", "signed": True},
                            {"name": "rs1", "bits": "19:15", "type": "register"},
                            {"name": "funct3", "bits": "14:12", "value": "000"},
                            {"name": "rd", "bits": "11:7", "type": "register"},
                            {"name": "opcode", "bits": "6:0", "value": "0010011"}
                        ]
                    },
                    "implementation_template": """# {mnemonic} instruction implementation
rs1_val = read_register(operands['rs1'])
imm_val = operands['imm']
# Sign extend 12-bit immediate
if imm_val & 0x800:
    imm_val = imm_val | 0xFFFFF000
result = (rs1_val {operation} imm_val) & {word_mask}
write_register(operands['rd'], result)
# Set flags
set_flag('Z', result == 0)
set_flag('N', (result & 0x80000000) != 0)"""
                },
                "LI-type": {
                    "description": "Load immediate operation",
                    "syntax": "{mnemonic} rd, imm",
                    "semantics": "rd = sign_extend(imm)",
                    "encoding": {
                        "fields": [
                            {"name": "imm", "bits": "31:20", "type": "immediate", "signed": True},
                            {"name": "rd", "bits": "11:7", "type": "register"},
                            {"name": "opcode", "bits": "6:0", "value": "0010011"}
                        ]
                    },
                    "implementation_template": """# {mnemonic} instruction implementation
imm_val = operands['imm']
# Sign extend 12-bit immediate
if imm_val & 0x800:
    imm_val = imm_val | 0xFFFFF000
write_register(operands['rd'], imm_val & {word_mask})"""
                },
                "J-type": {
                    "description": "Jump instruction",
                    "syntax": "{mnemonic} label",
                    "semantics": "PC = label",
                    "encoding": {
                        "fields": [
                            {"name": "imm", "bits": "31:12", "type": "immediate", "signed": True},
                            {"name": "rd", "bits": "11:7", "type": "register"},
                            {"name": "opcode", "bits": "6:0", "value": "1101111"}
                        ]
                    },
                    "implementation_template": """# {mnemonic} instruction implementation
target_addr = operands['imm']
# Set PC to target address
context.pc = target_addr & {word_mask}"""
                },
                "B-type": {
                    "description": "Branch instruction",
                    "syntax": "{mnemonic} rs1, rs2, label",
                    "semantics": "if (rs1 {condition} rs2) PC = label",
                    "encoding": {
                        "fields": [
                            {"name": "imm", "bits": "31:25,11:8", "type": "immediate", "signed": True},
                            {"name": "rs2", "bits": "24:20", "type": "register"},
                            {"name": "rs1", "bits": "19:15", "type": "register"},
                            {"name": "funct3", "bits": "14:12", "value": "000"},
                            {"name": "opcode", "bits": "6:0", "value": "1100011"}
                        ]
                    },
                    "implementation_template": """# {mnemonic} instruction implementation
rs1_val = read_register(operands['rs1'])
rs2_val = read_register(operands['rs2'])
target_addr = operands['imm']
if rs1_val {condition} rs2_val:
    context.pc = target_addr & {word_mask}"""
                },
                "S-type": {
                    "description": "Store instruction",
                    "syntax": "{mnemonic} rs2, offset(rs1)",
                    "semantics": "memory[rs1 + offset] = rs2",
                    "encoding": {
                        "fields": [
                            {"name": "imm", "bits": "31:25,11:7", "type": "immediate", "signed": True},
                            {"name": "rs2", "bits": "24:20", "type": "register"},
                            {"name": "rs1", "bits": "19:15", "type": "register"},
                            {"name": "funct3", "bits": "14:12", "value": "010"},
                            {"name": "opcode", "bits": "6:0", "value": "0100011"}
                        ]
                    },
                    "implementation_template": """# {mnemonic} instruction implementation
rs1_val = read_register(operands['rs1'])
rs2_val = read_register(operands['rs2'])
offset = operands['imm']
addr = (rs1_val + offset) & {word_mask}
# Store to memory
write_memory(addr, rs2_val)"""
                },
                "L-type": {
                    "description": "Load instruction",
                    "syntax": "{mnemonic} rd, offset(rs1)",
                    "semantics": "rd = memory[rs1 + offset]",
                    "encoding": {
                        "fields": [
                            {"name": "imm", "bits": "31:20", "type": "immediate", "signed": True},
                            {"name": "rs1", "bits": "19:15", "type": "register"},
                            {"name": "funct3", "bits": "14:12", "value": "010"},
                            {"name": "rd", "bits": "11:7", "type": "register"},
                            {"name": "opcode", "bits": "6:0", "value": "0000011"}
                        ]
                    },
                    "implementation_template": """# {mnemonic} instruction implementation
rs1_val = read_register(operands['rs1'])
offset = operands['imm']
addr = (rs1_val + offset) & {word_mask}
# Load from memory
value = read_memory(addr)
write_register(operands['rd'], value)"""
                },
                "SYS-type": {
                    "description": "System call instruction",
                    "syntax": "{mnemonic} svc",
                    "semantics": "Trap to service number",
                    "encoding": {
                        "fields": [
                            {"name": "imm", "bits": "31:20", "type": "immediate", "signed": False},
                            {"name": "rs1", "bits": "19:15", "type": "register"},
                            {"name": "funct3", "bits": "14:12", "value": "000"},
                            {"name": "rd", "bits": "11:7", "type": "register"},
                            {"name": "opcode", "bits": "6:0", "value": "1110011"}
                        ]
                    },
                    "implementation_template": """# {mnemonic} instruction implementation
svc = operands['imm']
# Handle system call based on service number
# This is a placeholder - actual implementation would depend on system services
# For now, just store the service number in a special register or flag
set_flag('SVC', svc)
# Could also trigger an interrupt or system call handler here"""
                }
            }
        else:
            # 16-bit templates (original)
            return {
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
result = (rd_val {operation} rs2_val) & {word_mask}
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
result = (rd_val {operation} imm_val) & {word_mask}
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
write_register(operands['rd'], imm_val & {word_mask})"""
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
context.pc = target_addr & {word_mask}"""
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
                }
            }
    
    def generate_isa_scaffold(self, name: str, instructions: List[str], directives: List[str] = [],
                             word_size: int = 16, instruction_size: int = 16, register_names: List[str] = []) -> Dict[str, Any]:
        """Generate a complete ISA scaffold"""
        if directives is None:
            directives = []
        if register_names is None:
            register_names = [f"r{i}" for i in range(8)]
        word_mask = (1 << word_size) - 1
        # Generate register definitions
        registers = []
        if not register_names:
            register_names = [f"r{i}" for i in range(8)]
        for reg in register_names:
            registers.append({"name": reg, "alias": [], "description": f"General-purpose register {reg}", "size": word_size})
        
        # Generate instruction definitions
        generated_instructions = []
        opcode_counter = 0
        rtype_opcodes = ["0000", "0001", "0010", "0011", "0100", "0101", "0110", "0111", "1000", "1001", "1010", "1011", "1100", "1101", "1110", "1111"]
        rtype_used = 0
        
        for instr in instructions:
            instr_upper = instr.upper()
            
            # Determine instruction type and generate appropriate template
            if instr_upper in ["ADD", "SUB", "AND", "OR", "XOR", "SLT", "SLTU"]:
                template = self.get_instruction_templates(instruction_size, word_size)["R-type"]
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
                    "format": "R-type",
                    "description": template["description"],
                    "syntax": template["syntax"].format(mnemonic=instr_upper),
                    "semantics": template["semantics"].format(operation=operation),
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper, operation=operation, word_mask=word_mask)
                }
                instruction_def["encoding"]["fields"][0]["value"] = opcode
                
            elif instr_upper in ["ADDI", "ANDI", "ORI", "XORI"]:
                template = self.get_instruction_templates(instruction_size, word_size)["I-type"]
                operation_map = {
                    "ADDI": "+",
                    "ANDI": "&",
                    "ORI": "|",
                    "XORI": "^"
                }
                operation = operation_map[instr_upper]
                
                instruction_def = {
                    "mnemonic": instr_upper,
                    "format": "I-type",
                    "description": template["description"],
                    "syntax": template["syntax"].format(mnemonic=instr_upper),
                    "semantics": template["semantics"].format(operation=operation),
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper, operation=operation, word_mask=word_mask)
                }
                
            elif instr_upper == "LI":
                template = self.get_instruction_templates(instruction_size, word_size)["LI-type"]
                instruction_def = {
                    "mnemonic": instr_upper,
                    "format": "I-type",
                    "description": template["description"],
                    "syntax": template["syntax"].format(mnemonic=instr_upper),
                    "semantics": template["semantics"],
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper, word_mask=word_mask)
                }
                
            elif instr_upper in ["J", "JAL"]:
                template = self.get_instruction_templates(instruction_size, word_size)["J-type"]
                instruction_def = {
                    "mnemonic": instr_upper,
                    "format": "J-type",
                    "description": template["description"],
                    "syntax": template["syntax"].format(mnemonic=instr_upper),
                    "semantics": template["semantics"],
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper, word_mask=word_mask)
                }
                
            elif instr_upper in ["BEQ", "BNE", "BLT", "BGE", "BLTU", "BGEU"]:
                template = self.get_instruction_templates(instruction_size, word_size)["B-type"]
                condition_map = {
                    "BEQ": "==",
                    "BNE": "!=",
                    "BLT": "<",
                    "BGE": ">=",
                    "BLTU": "<",
                    "BGEU": ">="
                }
                condition = condition_map[instr_upper]
                instruction_def = {
                    "mnemonic": instr_upper,
                    "format": "B-type",
                    "description": template["description"],
                    "syntax": template["syntax"].format(mnemonic=instr_upper),
                    "semantics": template["semantics"].format(condition=condition),
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper, condition=condition, word_mask=word_mask)
                }
                
            elif instr_upper in ["LW", "SW"]:
                if instr_upper == "LW":
                    template = self.get_instruction_templates(instruction_size, word_size)["L-type"]
                    format_type = "I-type"
                else:
                    template = self.get_instruction_templates(instruction_size, word_size)["S-type"]
                    format_type = "S-type"
                instruction_def = {
                    "mnemonic": instr_upper,
                    "format": format_type,
                    "description": template["description"],
                    "syntax": template["syntax"].format(mnemonic=instr_upper),
                    "semantics": template["semantics"],
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper, word_mask=word_mask)
                }
                
            elif instr_upper in ["ECALL", "EBREAK"]:
                template = self.get_instruction_templates(instruction_size, word_size)["SYS-type"]
                instruction_def = {
                    "mnemonic": instr_upper,
                    "format": "I-type",
                    "description": template["description"],
                    "syntax": template["syntax"].format(mnemonic=instr_upper),
                    "semantics": template["semantics"],
                    "encoding": template["encoding"].copy(),
                    "implementation": template["implementation_template"].format(mnemonic=instr_upper, word_mask=word_mask)
                }
                
            elif instr_upper == "JALR":
                # Use I-type template for JALR with custom implementation
                template = self.get_instruction_templates(instruction_size, word_size)["I-type"]
                instruction_def = {
                    "mnemonic": instr_upper,
                    "format": "I-type",
                    "description": "Jump and link register",
                    "syntax": "JALR rd, rs1",
                    "semantics": "rd = PC + 4; PC = rs1",
                    "encoding": template["encoding"].copy(),
                    "implementation": f"""# {instr_upper} instruction implementation
rs1_val = read_register(operands['rs1'])
return_addr = context.pc + 4
write_register(operands['rd'], return_addr)
context.pc = rs1_val & {word_mask}"""
                }
                
            else:
                # Generic instruction template - adapt to instruction size
                if instruction_size == 32:
                    instruction_def = {
                        "mnemonic": instr_upper,
                        "format": "R-type",
                        "description": f"Custom {instr_upper} instruction",
                        "syntax": f"{instr_upper} rd, rs1, rs2",
                        "semantics": f"rd = rs1 + rs2  # Custom operation",
                        "encoding": {
                            "fields": [
                                {"name": "funct7", "bits": "31:25", "value": f"{opcode_counter:07b}"},
                                {"name": "rs2", "bits": "24:20", "type": "register"},
                                {"name": "rs1", "bits": "19:15", "type": "register"},
                                {"name": "funct3", "bits": "14:12", "value": "000"},
                                {"name": "rd", "bits": "11:7", "type": "register"},
                                {"name": "opcode", "bits": "6:0", "value": "0110011"}
                            ]
                        },
                        "implementation": f"""# {instr_upper} instruction implementation
rs1_val = read_register(operands['rs1'])
rs2_val = read_register(operands['rs2'])
result = (rs1_val + rs2_val) & {word_mask}  # Custom operation
write_register(operands['rd'], result)
# Set flags
set_flag('Z', result == 0)
set_flag('N', (result & 0x80000000) != 0)"""
                    }
                else:
                    instruction_def = {
                        "mnemonic": instr_upper,
                        "format": "R-type",
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
result = (rd_val + rs2_val) & {word_mask}  # Custom operation
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
                "general_purpose": registers,
                "special": [
                    {"name": "pc", "description": "Program counter", "size": word_size},
                    {"name": "flags", "description": "Status flags", "size": 8}
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
                    "mnemonic": "NOP",
                    "expansion": "ADD r0, r0",
                    "syntax": "NOP",
                    "description": "No operation"
                },
                {
                    "mnemonic": "MV",
                    "expansion": "ADD rd, rs, r0",
                    "syntax": "MV rd, rs",
                    "description": "Move register"
                },
                {
                    "mnemonic": "NOT",
                    "expansion": "XOR rd, rs, -1",
                    "syntax": "NOT rd, rs",
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
    parser.add_argument("--register-count", type=int, default=8, help="Number of general-purpose registers (default: 8)")
    parser.add_argument("--registers", help="Comma-separated list of register names (overrides --register-count)")
    parser.add_argument("--output", 
                       help="Output file path (default: {name}_isa.json)")
    
    args = parser.parse_args()
    
    # Parse instructions and directives
    instructions = [instr.strip() for instr in args.instructions.split(",")]
    if args.directives:
        directives = [directive.strip() for directive in args.directives.split(",")]
    else:
        directives = []

    # Parse registers
    if args.registers:
        register_names = [r.strip() for r in args.registers.split(",") if r.strip()]
        register_count = len(register_names)
    else:
        register_count = args.register_count
        register_names = [f"r{i}" for i in range(register_count)]

    # Generate ISA scaffold
    generator = ISAScaffoldGenerator()
    isa_definition = generator.generate_isa_scaffold(
        name=args.name,
        instructions=instructions,
        directives=directives,
        word_size=args.word_size,
        instruction_size=args.instruction_size,
        register_names=register_names
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