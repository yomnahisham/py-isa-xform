"""
Parser for assembly language
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Any, Union
from .isa_loader import ISADefinition


class TokenType(Enum):
    """Types of tokens in assembly language"""
    LABEL = "label"
    INSTRUCTION = "instruction"
    REGISTER = "register"
    IMMEDIATE = "immediate"
    ADDRESS = "address"
    DIRECTIVE = "directive"
    COMMENT = "comment"
    WHITESPACE = "whitespace"
    COMMA = "comma"
    LPAREN = "lparen"
    RPAREN = "rparen"
    PLUS = "plus"
    MINUS = "minus"
    COLON = "colon"
    HASH = "hash"
    DOLLAR = "dollar"
    STRING = "string"
    UNKNOWN = "unknown"
    NEWLINE = "newline"


@dataclass
class Token:
    """Represents a token in assembly code"""
    type: TokenType
    value: str
    line: int
    column: int
    file: Optional[str] = None


@dataclass
class ASTNode:
    pass


@dataclass
class LabelNode(ASTNode):
    name: str
    line: int
    column: int
    file: Optional[str] = None


@dataclass
class InstructionNode(ASTNode):
    mnemonic: str
    operands: List['OperandNode'] = field(default_factory=list)
    line: int = 0
    column: int = 0
    file: Optional[str] = None


@dataclass
class OperandNode(ASTNode):
    value: Any  # "register", "immediate", "address", "label"
    type: str
    line: int = 0
    column: int = 0
    file: Optional[str] = None


@dataclass
class DirectiveNode(ASTNode):
    name: str
    arguments: List[str] = field(default_factory=list)
    line: int = 0
    column: int = 0
    file: Optional[str] = None


@dataclass
class CommentNode(ASTNode):
    text: str
    line: int = 0
    column: int = 0
    file: Optional[str] = None


class Parser:
    """Parser for assembly language"""
    
    def __init__(self, isa_definition: Optional[ISADefinition] = None):
        self.isa_definition = isa_definition
        
        # Default syntax rules (can be overridden by ISA definition)
        self.comment_char = ';'
        self.comment_chars = [';']  # Support multiple comment characters
        self.label_suffix = ':'
        self.register_prefix = '$'
        self.immediate_prefix = '#'
        self.hex_prefix = '0x'
        self.binary_prefix = '0b'
        self.case_sensitive = False
        
        # Setup syntax from ISA if available
        if isa_definition:
            self._setup_syntax_from_isa()
    
    def _setup_syntax_from_isa(self):
        """Setup parser syntax from ISA definition"""
        if self.isa_definition and hasattr(self.isa_definition, 'assembly_syntax'):
            syntax = self.isa_definition.assembly_syntax
            self.comment_char = syntax.comment_char
            self.comment_chars = syntax.comment_chars
            self.label_suffix = syntax.label_suffix
            self.register_prefix = syntax.register_prefix
            self.immediate_prefix = syntax.immediate_prefix
            self.hex_prefix = syntax.hex_prefix
            self.binary_prefix = syntax.binary_prefix
            self.case_sensitive = syntax.case_sensitive
    
    def parse(self, text: str, file: Optional[str] = None) -> List[ASTNode]:
        """Parse assembly text into AST nodes"""
        nodes = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip empty lines
            if not line.strip():
                continue
            
            # Parse each line
            result = self._parse_line(line.strip(), line_num, file)
            if result:
                if isinstance(result, list):
                    nodes.extend(result)
                else:
                    nodes.append(result)
        
        return nodes
    
    def _parse_line(self, line: str, line_num: int, file: Optional[str]) -> Optional[Union[ASTNode, List[ASTNode]]]:
        """Parse a single line"""
        # Remove comments - check for any comment character
        comment_pos = -1
        comment_char_found = None
        
        # Find the earliest comment character in the line
        for comment_char in self.comment_chars:
            pos = line.find(comment_char)
            if pos != -1 and (comment_pos == -1 or pos < comment_pos):
                comment_pos = pos
                comment_char_found = comment_char
        
        # If a comment was found, handle it
        if comment_pos != -1:
            comment_text = line[comment_pos:].strip()
            line = line[:comment_pos].strip()
            
            # If line is empty after removing comment, return comment node
            if not line:
                return CommentNode(comment_text, line_num, 1, file)
        
        # Skip empty lines
        if not line:
            return None
        
        # Check for label (ends with label_suffix)
        if line.endswith(self.label_suffix):
            label_name = line[:-len(self.label_suffix)].strip()
            return LabelNode(label_name, line_num, 1, file)
        
        # Check for label followed by instruction (contains label_suffix)
        if self.label_suffix in line:
            suffix_pos = line.find(self.label_suffix)
            label_name = line[:suffix_pos].strip()
            instruction_part = line[suffix_pos + len(self.label_suffix):].strip()
            
            # Create label node
            label_node = LabelNode(label_name, line_num, 1, file)
            
            # If there's an instruction after the label, parse it
            if instruction_part:
                # Check if it's a directive (starts with .)
                if instruction_part.startswith('.'):
                    # Parse as directive
                    parts = instruction_part.split(None, 1)  # Split on whitespace, max 1 split
                    directive_name = parts[0]
                    arguments = parts[1].split(',') if len(parts) > 1 else []
                    arguments = [arg.strip() for arg in arguments if arg.strip()]
                    directive_node = DirectiveNode(directive_name, arguments, line_num, 1, file)
                    return [label_node, directive_node]
                else:
                    # Parse as instruction
                    instruction_node = self._parse_instruction_part(instruction_part, line_num, file)
                    if instruction_node:
                        return [label_node, instruction_node]
            
            return label_node
        
        # Check for directive (starts with .)
        if line.startswith('.'):
            parts = line.split(None, 1)  # Split on whitespace, max 1 split
            directive_name = parts[0]
            arguments = parts[1].split(',') if len(parts) > 1 else []
            arguments = [arg.strip() for arg in arguments if arg.strip()]
            return DirectiveNode(directive_name, arguments, line_num, 1, file)
        
        # Must be an instruction
        return self._parse_instruction_part(line, line_num, file)
    
    def _parse_instruction_part(self, line: str, line_num: int, file: Optional[str]) -> Optional[InstructionNode]:
        """Parse instruction part of a line"""
        parts = line.split(None, 1)  # Split on whitespace, max 1 split
        if len(parts) < 1:
            return None
        
        mnemonic = parts[0]
        operands = []
        
        if len(parts) > 1:
            operand_str = parts[1]
            operand_parts = [part.strip() for part in operand_str.split(',')]
            
            for operand_part in operand_parts:
                if operand_part:
                    operand = self._parse_operand(operand_part, line_num, file)
                    if operand:
                        operands.append(operand)
        
        return InstructionNode(mnemonic, operands, line_num, 1, file)
    
    def _parse_operand(self, operand_str: str, line_num: int, file: Optional[str]) -> Optional[OperandNode]:
        """Parse a single operand"""
        operand_str = operand_str.strip()
        
        if not operand_str:
            return None
        
        # Handle offset($reg) or offset(Rreg)
        if '(' in operand_str and operand_str.endswith(')'):
            offset_part, reg_part = operand_str.split('(', 1)
            offset = offset_part.strip()
            reg = reg_part[:-1].strip()  # Remove closing )
            # Parse offset as immediate
            if self._is_number(offset):
                offset_node = OperandNode(offset, "immediate", line_num, 1, file)
            else:
                offset_node = OperandNode(offset, "label", line_num, 1, file)
            # Parse register
            if reg.startswith('$'):
                reg = reg[1:]
            reg_node = OperandNode(reg, "register", line_num, 1, file)
            # Return as a memory operand node
            return OperandNode((offset_node, reg_node), "mem", line_num, 1, file)
        
        # Immediate value (starts with #)
        if operand_str.startswith('#'):
            value = operand_str[1:]  # Remove #
            return OperandNode(value, "immediate", line_num, 1, file)
        
        # Register (starts with $ or is a register name)
        if operand_str.startswith('$'):
            value = operand_str[1:]  # Remove $
            return OperandNode(value, "register", line_num, 1, file)
        
        # Check if it's a register name (if we have ISA definition)
        if self.isa_definition and self._is_register(operand_str):
            return OperandNode(operand_str, "register", line_num, 1, file)
        
        # Check if it's a number
        if self._is_number(operand_str):
            return OperandNode(operand_str, "immediate", line_num, 1, file)
        
        # Must be a label
        return OperandNode(operand_str, "label", line_num, 1, file)
    
    def _is_register(self, name: str) -> bool:
        """Check if name is a register"""
        if not self.isa_definition or not hasattr(self.isa_definition, 'registers'):
            return False
        
        for reg_list in self.isa_definition.registers.values():
            for reg in reg_list:
                if hasattr(reg, 'name') and reg.name.upper() == name.upper():
                    return True
        return False
    
    def _is_instruction(self, name: str) -> bool:
        """Check if name is an instruction"""
        if not self.isa_definition or not hasattr(self.isa_definition, 'instructions'):
            return False
        
        for instr in self.isa_definition.instructions:
            if hasattr(instr, 'mnemonic') and instr.mnemonic.upper() == name.upper():
                return True
        return False
    
    def _is_number(self, text: str) -> bool:
        """Check if text is a number"""
        if not text:
            return False
        
        # Handle hex
        if text.startswith('0x'):
            try:
                int(text, 16)
                return True
            except ValueError:
                return False
        
        # Handle binary
        if text.startswith('0b'):
            try:
                int(text, 2)
                return True
            except ValueError:
                return False
        
        # Handle decimal
        try:
            int(text, 10)
            return True
        except ValueError:
            return False 