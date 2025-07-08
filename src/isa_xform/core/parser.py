"""
Parser for assembly language
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Any, Union
from .isa_loader import ISADefinition
from .operand_parser import OperandParser


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
            self.operand_parser = OperandParser(isa_definition)
        else:
            self.operand_parser = None
    
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
        
        # Check for directive (starts with .) - check this BEFORE labels
        if line.startswith('.'):
            parts = line.split(None, 1)  # Split on whitespace, max 1 split
            directive_name = parts[0]
            arguments = self._parse_directive_arguments(parts[1]) if len(parts) > 1 else []
            return DirectiveNode(directive_name, arguments, line_num, 1, file)
        
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
                    arguments = self._parse_directive_arguments(parts[1]) if len(parts) > 1 else []
                    directive_node = DirectiveNode(directive_name, arguments, line_num, 1, file)
                    return [label_node, directive_node]
                else:
                    # Parse as instruction
                    instruction_node = self._parse_instruction_part(instruction_part, line_num, file)
                    if instruction_node:
                        return [label_node, instruction_node]
            
            return label_node
        
        # Must be an instruction
        return self._parse_instruction_part(line, line_num, file)
    
    def _parse_instruction_part(self, line: str, line_num: int, file: Optional[str]) -> Optional[InstructionNode]:
        """Parse instruction part of a line (ISA-driven operand types, with operand count check)"""
        parts = line.split(None, 1)  # Split on whitespace, max 1 split
        if len(parts) < 1:
            return None
        
        mnemonic = parts[0]
        operands = []
        expected_types = []
        expected_count = None
        # Modular: get expected operand types and count from ISA definition
        if self.isa_definition and hasattr(self.isa_definition, 'instructions'):
            instr = None
            for i in self.isa_definition.instructions:
                if hasattr(i, 'mnemonic') and i.mnemonic.upper() == mnemonic.upper():
                    instr = i
                    break
            if instr and hasattr(instr, 'syntax'):
                syntax_parts = instr.syntax.split()
                if len(syntax_parts) > 1:
                    operand_str = ' '.join(syntax_parts[1:])
                    expected_types = [s.strip() for s in operand_str.split(',')]
                    expected_count = len(expected_types)
                else:
                    expected_count = 0
        
        if len(parts) > 1:
            operand_str = parts[1]
            operand_parts = [part.strip() for part in operand_str.split(',')]
            # Modular: check operand count
            if expected_count is not None and len(operand_parts) != expected_count:
                raise ValueError(f"[ISA ERROR] Instruction '{mnemonic}' expects {expected_count} operands as per ISA definition, but got {len(operand_parts)} at line {line_num} in {file or '<input>'}.")
            for idx, operand_part in enumerate(operand_parts):
                if operand_part:
                    expected_type = expected_types[idx] if idx < len(expected_types) and expected_types[idx] is not None else ""
                    operand = self._parse_operand_modular_typed(operand_part, line_num, file, expected_type)
                    if operand:
                        operands.append(operand)
        else:
            # Modular: check for zero-operand instructions
            if expected_count is not None and expected_count != 0:
                raise ValueError(f"[ISA ERROR] Instruction '{mnemonic}' expects {expected_count} operands as per ISA definition, but got 0 at line {line_num} in {file or '<input>'}.")
        
        return InstructionNode(mnemonic, operands, line_num, 1, file)

    def _parse_operand_modular_typed(self, operand_str: str, line_num: int, file: Optional[str], expected_type: str = "") -> Optional[OperandNode]:
        """Parse a single operand using the modular OperandParser, with robust fallback logic."""
        if not self.operand_parser:
            return self._parse_operand(operand_str, line_num, file)
        
        parsed = None
        if expected_type:
            # Map ISA syntax names to OperandParser types
            type_map = {
                'rd': 'register', 'rs1': 'register', 'rs2': 'register',
                'imm': 'immediate', 'immediate': 'immediate', 'offset': 'immediate',
                'address': 'address', 'label': 'label',
            }
            parse_type = type_map.get(expected_type.lower(), None)
            
            # Try parsing with expected type first
            if parse_type == 'register':
                parsed = self.operand_parser._parse_register(operand_str, line_num, 1)
            elif parse_type == 'immediate':
                parsed = self.operand_parser._parse_immediate(operand_str, line_num, 1)
            elif parse_type == 'address':
                parsed = self.operand_parser._parse_address(operand_str, line_num, 1)
            elif parse_type == 'label':
                parsed = self.operand_parser._parse_label(operand_str, line_num, 1)
            
            # If parsing failed (value is None or has validation errors), try fallback
            if not parsed or parsed.value is None or parsed.validation_errors:
                # Fallback: try parsing as register if it looks like a register name
                if self.operand_parser._is_register_name(operand_str):
                    parsed = self.operand_parser._parse_register(operand_str, line_num, 1)
                    if parsed.value is not None:
                        return OperandNode(parsed.value.name, 'register', line_num, 1, file)
                # Fallback: try parsing as immediate if it looks like a number
                if self.operand_parser._is_immediate_value(operand_str):
                    parsed = self.operand_parser._parse_immediate(operand_str, line_num, 1)
                    if parsed.value is not None:
                        return OperandNode(str(parsed.value), 'immediate', line_num, 1, file)
                # Fallback: try parsing as label if it looks like a label
                if self.operand_parser._is_label_name(operand_str):
                    parsed = self.operand_parser._parse_label(operand_str, line_num, 1)
                    if parsed.value is not None:
                        return OperandNode(parsed.value, 'label', line_num, 1, file)
        
        # If no expected type or parsing failed, use auto-detection
        if not parsed or parsed.value is None:
            parsed = self.operand_parser.parse_operand(operand_str, line_num, 1)
        
        # Map ParsedOperand to OperandNode
        if parsed.type == 'register' and parsed.value is not None:
            return OperandNode(parsed.value.name, 'register', line_num, 1, file)
        elif parsed.type == 'immediate' and parsed.value is not None:
            return OperandNode(str(parsed.value), 'immediate', line_num, 1, file)
        elif parsed.type == 'label' and parsed.value is not None:
            return OperandNode(parsed.value, 'label', line_num, 1, file)
        elif parsed.type == 'address' and parsed.value is not None:
            return OperandNode(str(parsed.value), 'address', line_num, 1, file)
        elif parsed.type == 'mem':
            # Not directly supported by OperandParser, fallback to legacy
            return self._parse_operand(operand_str, line_num, file)
        else:
            # Fallback to legacy
            return self._parse_operand(operand_str, line_num, file)
    
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
                # Check main name
                if hasattr(reg, 'name') and reg.name.upper() == name.upper():
                    return True
                # Check aliases
                if hasattr(reg, 'alias') and reg.alias:
                    for alias in reg.alias:
                        if alias.upper() == name.upper():
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

    def _parse_directive_arguments(self, args_str: str) -> List[str]:
        """Parse directive arguments, properly handling quoted strings"""
        if not args_str.strip():
            return []
        
        arguments = []
        current_arg = ""
        in_quotes = False
        quote_char = None
        i = 0
        
        while i < len(args_str):
            char = args_str[i]
            
            if not in_quotes:
                if char in ['"', "'"]:
                    # Start of quoted string
                    in_quotes = True
                    quote_char = char
                    current_arg += char
                elif char == ',':
                    # End of argument
                    if current_arg.strip():
                        arguments.append(current_arg.strip())
                    current_arg = ""
                else:
                    current_arg += char
            else:
                # Inside quoted string
                if char == quote_char:
                    # End of quoted string
                    in_quotes = False
                    quote_char = None
                    current_arg += char
                elif char == '\\' and i + 1 < len(args_str):
                    # Escaped character
                    current_arg += char + args_str[i + 1]
                    i += 1
                else:
                    current_arg += char
            
            i += 1
        
        # Add the last argument
        if current_arg.strip():
            arguments.append(current_arg.strip())
        
        return arguments 