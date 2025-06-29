from enum import Enum
import argparse
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Any, Union
from .isa_loader import ISADefinition, Instruction, Directive
from .parser import Parser, ASTNode, LabelNode, InstructionNode, DirectiveNode, CommentNode, OperandNode
from .symbol_table import SymbolTable
from pathlib import Path

class Assembler:
    def __init__(self, parser: Parser, symbol_table: SymbolTable, isa_definition: ISADefinition):
        self.isa_definition = isa_definition
        self.parser = parser
        self.symbol_table = symbol_table

    def find_instruction(self, mnemonic: str):
        for instruction in self.isa_definition.instructions:
            if instruction.mnemonic == mnemonic:
                return instruction
        return None
    
    def parse_immediate(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f"Expected a string for immediate but got a {type(value)}")
        value = value.strip().lower()

        if value.startswith('0x'):
            return int(value, 16)
        if value.startswith(value, '0b'):
            return int(value, 2)
        else:
            return int(value, 10)

    def assemble(self, nodes: List[ASTNode]) -> bytearray:
        """Assemble the provided AST nodes into machine code."""
        machine_code = bytearray()

        for node in nodes:
            if isinstance(node, LabelNode):
                # Handle label definition
                name = node.name
                line = node.line
                column = node.column
                file = node.file
                self.symbol_table.define_label(name, line, column, file)
            elif isinstance(node, InstructionNode):
                # Generate machine code for instruction
                i = 0
                mnemonic = node.mnemonic
                operands = node.operands
                line = node.line
                column = node.column
                file = node.file

                instruction = self.find_instruction(mnemonic)
                encoding_spec = instruction.encoding
                instruction_word = 0

                for field_name, field_spec in encoding_spec.items():
                    if "value" in field_spec:
                        field_value = int(field_spec["value"], 2)
                    else:
                        if i <= len(self.isa_definition.registers):
                            field_value = self.isa_definition.registers[i] # TO BE IMPROVED W/ FUNCTION TO GET THE 'CORRECT' OPERAND VALUE
                            i += 1
                        else:
                            # Error
                            return
                    bit_range = field_spec["bits"]
                    index = bit_range.split(':')
                    index = index[1]
                    instruction_word += field_value << index

                instruction_bytes = instruction_word.to_bytes(self.isa_definition.word_size, byteorder=self.isa_definition.endianness)
                machine_code.extend(instruction_bytes)

            elif isinstance(node, DirectiveNode):
                directive_name = self.isa_definition.directives.get(node.name)
                if not directive_name:
                    raise ValueError(f"Unknown directive {directive_name}")
                
                action = directive_name.action

                if action == "allocate_bytes":
                    word_size = self.isa_definition.word_size // 8 # Convert bits to bytes

                    for argument in node.arguments:
                        value = self.parse_immediate(argument)
                        machine_code.extend(value.to_bytes(word_size, byteorder=self.isa_definition.endianness))
                        self.symbol_table.advance_address(word_size)

                elif action == "allocate_space":
                    size = self.parse_immediate(node.arguments[0])
                    machine_code.extend(b'\x00' * size)
                    self.symbol_table.advance_address(size)
                
                elif action == "allocate_string":
                    text = node.arguments[0].strip('"')
                    encoded_text = text.encode('ascii')
                    machine_code.extend(encoded_text)
                    self.symbol_table.advance_address(len(encoded_text))
                    if node.name.endswith('z'):
                        machine_code.extend(b'\x00')
                        self.symbol_table.advance_address(1)
                
                elif action == "set_section":
                    pass

                elif action == "align_counter":
                    pass

                elif action == "define_constant":
                    pass


            elif isinstance(node, CommentNode):
                continue

        return machine_code
