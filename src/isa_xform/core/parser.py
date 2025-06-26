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
        self.comment_char = ';'
        self.case_sensitive = False
        
        # Setup syntax from ISA if available
        if isa_definition:
            self._setup_syntax_from_isa()
    
    def _setup_syntax_from_isa(self):
        """Setup parser syntax from ISA definition"""
        # These attributes are not part of ISADefinition, so we use defaults
        pass
    
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
        # Remove comments
        if self.comment_char in line:
            comment_pos = line.find(self.comment_char)
            comment_text = line[comment_pos:].strip()
            line = line[:comment_pos].strip()
            
            # If line is empty after removing comment, return comment node
            if not line:
                return CommentNode(comment_text, line_num, 1, file)
        
        # Skip empty lines
        if not line:
            return None
        
        # Check for label (ends with :)
        if line.endswith(':'):
            label_name = line[:-1].strip()
            return LabelNode(label_name, line_num, 1, file)
        
        # Check for label followed by instruction (contains :)
        if ':' in line:
            colon_pos = line.find(':')
            label_name = line[:colon_pos].strip()
            instruction_part = line[colon_pos + 1:].strip()
            
            # Create label node
            label_node = LabelNode(label_name, line_num, 1, file)
            
            # If there's an instruction after the label, parse it
            if instruction_part:
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