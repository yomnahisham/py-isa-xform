import struct
from typing import List, Optional, Dict, Any, Tuple, Union
from dataclasses import dataclass
from .isa_loader import ISADefinition, Instruction
from .symbol_table import SymbolTable
from ..utils.error_handling import DisassemblerError, ErrorLocation
from ..utils.bit_utils import (
    extract_bits, set_bits, sign_extend, parse_bit_range, 
    create_mask, bytes_to_int, int_to_bytes
)

import json

class RegisterFile:
    def __init__(self, isa_json, zero_locked=True):
        """
        Initializes register file from ISA definition.
        
        Parameters:
            isa_json (dict): The ISA definition loaded from JSON
            zero_locked (bool): If True, x0 is hardwired to 0
        """
        self.registers = {}
        self.alias_map = {}
        self.zero_locked = zero_locked

        # Load general-purpose registers
        general_regs = isa_json.get("registers", {}).get("general_purpose", [])

        for reg in general_regs:
            name = reg["name"]  # like "x0"
            self.registers[name] = 0  # initialize to 0

            # Map aliases to canonical name
            for alias in reg.get("alias", []):
                self.alias_map[alias] = name

    def _canonical(self, name):
        return self.alias_map.get(name, name)

    def get(self, name):
        canonical = self._canonical(name)
        return self.registers.get(canonical, 0)

    def set(self, name, value):
        canonical = self._canonical(name)
        if self.zero_locked and canonical == "x0":
            return  # prevent writing to x0
        self.registers[canonical] = value & 0xFFFFFFFF  # force 32-bit

    def dump(self):
        """Prints all register values for debugging."""
        for name in sorted(self.registers):
            print(f"{name}: 0x{self.registers[name]:08X}")


def read_asm_file(filepath):
    """
    Reads an assembly (.asm) file line by line.

    Parameters:
        filepath (str): Path to the .asm file

    Returns:
        List[str]: A list of non-empty, non-comment lines
    """
    instructions = []

    try:
        with open(filepath, 'r') as file:
            for line in file:
                # Remove leading/trailing whitespace
                clean_line = line.strip()
                
                # Skip empty lines and full-line comments
                if not clean_line or clean_line.startswith('#') or clean_line.startswith('//'):
                    continue

                # Optionally strip inline comments
                if '#' in clean_line:
                    clean_line = clean_line.split('#')[0].strip()
                elif '//' in clean_line:
                    clean_line = clean_line.split('//')[0].strip()

                if clean_line:  # If anything left after stripping
                    instructions.append(clean_line)

    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}")

    return instructions

import re

def parse_operands(instruction_line, syntax):
    """
    Extract operands from an instruction line using its syntax definition.

    Returns:
        Dict[str, str | int] mapping field name to operand
    """
    # Extract the expected operand field names from syntax
    syntax_fields = syntax.split(maxsplit=1)[1]  # skip mnemonic
    field_names = re.split(r'[,\s()]+', syntax_fields.strip())
    field_names = [f for f in field_names if f]  # remove empty strings

    # Extract actual operands from the line after the mnemonic
    operand_text = instruction_line.split(maxsplit=1)[1].strip()
    
    # Replace parentheses with spaces to separate offset and base register
    operand_text_cleaned = operand_text.replace('(', ' ').replace(')', ' ')
    operand_values = operand_text_cleaned.replace(',', ' ').split()
    
    if len(field_names) != len(operand_values):
        raise ValueError(f"Operand count mismatch in: '{instruction_line}'")

    fields = {}
    for name, value in zip(field_names, operand_values):
        value = value.strip()
        if value.startswith("x") or value.isalpha():
            fields[name] = value  # Register
        else:
            try:
                fields[name] = int(value, 0)  # Support hex/bin/dec
            except ValueError:
                raise ValueError(f"Invalid operand: '{value}'")

    return fields


def simulate_asm_file(filepath):
    """
    Simulates execution of an assembly (.asm) file.
    Currently just reads and iterates over each instruction line.

    Parameters:
        filepath (str): Path to the .asm file
    """

    from .isa_loader import ISALoader  # or adjust based on where it is

    isa_def = ISALoader().load(open(isa_json_path))  # this returns ISADefinition

    # Create register file
    rf = RegisterFile(isa_def)

    #read instructions into list
    instructions = read_asm_file(filepath)

    for line in instructions:
        # Skip empty lines or comments (optional)
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        # Extract mnemonic (first word)
        parts = line.split()
        if parts:
            mnemonic = parts[0]

        #Search in isa definition 
        matching_instr = next(
            (instr for instr in isa_def.instructions if instr.mnemonic.upper() == mnemonic),
            None
        )

        if matching_instr:
            semantics = matching_instr.semantics
        else:
            print(f"Warning: Unknown instruction '{mnemonic}'")

        try:
            # Extract operand fields from line and syntax
            fields = parse_operands(line, matching_instr.syntax)

            # Execute the instruction semantics
            operate(matching_instr.semantics, fields, rf)

        except Exception as e:
            print(f"Error processing instruction: {line}\n{e}")
            continue

        pass


def operate(semantics: str, fields: dict, register_file):
    """
    Interprets and executes a semantic expression from the ISA using register names.

    Parameters:
        semantics (str): A string like "$rd = $rs1 + $rs2"
        fields (dict): Maps field names (e.g., 'rd', 'rs1') to register names (e.g., 'x1', 'x2')
        register_file (RegisterFile): The simulated register file
    """
    # Step 1: Replace placeholders like $rd, $rs1 with actual register accesses
    expr = semantics

    for field_name, reg_name in fields.items():
        # $rd → register_file.get("x1") in RHS, or → "x1" if it's LHS
        if f"${field_name}" in expr:
            expr = expr.replace(
                f"${field_name}", f'register_file.get("{reg_name}")'
            )

    # Step 2: Detect the destination register (LHS)
    # Assume simple assignment: "$rd = $rs1 + $rs2"
    if '=' in semantics:
        lhs, rhs = semantics.split('=', 1)
        lhs = lhs.strip().replace('$', '')
        dest_reg_name = fields.get(lhs)

        # Step 3: Evaluate the RHS
        value = eval(rhs.strip(), {}, {'register_file': register_file})

        # Step 4: Set the destination register
        register_file.set(dest_reg_name, value)

        # Optional debug:
        # print(f"[DEBUG] {dest_reg_name} = {value}")


