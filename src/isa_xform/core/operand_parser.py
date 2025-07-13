"""
Modular Operand Parser: Handles operand parsing for different ISA syntax patterns
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from .isa_loader import ISADefinition, OperandPattern, Register
from ..utils.error_handling import ParseError, ErrorLocation


@dataclass
class ParsedOperand:
    """Represents a parsed operand"""
    type: str
    value: Any
    original_text: str
    line: int
    column: int
    validation_errors: List[str] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []


class OperandParser:
    """Modular operand parser that adapts to ISA syntax rules"""
    
    def __init__(self, isa_definition: ISADefinition):
        self.isa_definition = isa_definition
        self.syntax = isa_definition.assembly_syntax
        self.registers = isa_definition.registers
        
        # Get JSON configuration for formatting
        self.reg_config = getattr(isa_definition, 'register_formatting', {})
        self.op_config = getattr(isa_definition, 'operand_formatting', {})
        
        # Get prefixes from JSON config with fallback to assembly_syntax
        self.register_prefix = self.reg_config.get('prefix', getattr(self.syntax, 'register_prefix', 'x'))
        self.immediate_prefix = self.op_config.get('immediate_prefix', getattr(self.syntax, 'immediate_prefix', '#'))
        self.hex_prefix = self.op_config.get('hex_prefix', getattr(self.syntax, 'hex_prefix', '0x'))
        self.binary_prefix = self.op_config.get('binary_prefix', getattr(self.syntax, 'binary_prefix', '0b'))
        
        # Build register lookup tables
        self._build_register_lookup()
        
        # Build operand pattern matchers
        self._build_pattern_matchers()
    
    def _build_register_lookup(self):
        """Build fast register lookup tables"""
        self.register_by_name = {}
        self.register_by_alias = {}
        
        for category, reg_list in self.registers.items():
            for register in reg_list:
                # Store by name
                name_key = register.name.upper() if not self.syntax.case_sensitive else register.name
                self.register_by_name[name_key] = register
                
                # Store by aliases
                for alias in register.alias:
                    alias_key = alias.upper() if not self.syntax.case_sensitive else alias
                    self.register_by_alias[alias_key] = register
    
    def _build_pattern_matchers(self):
        """Build regex patterns for operand matching"""
        self.pattern_matchers = {}
        
        # Build patterns from ISA definition
        for pattern_name, pattern_def in self.isa_definition.operand_patterns.items():
            try:
                regex = re.compile(pattern_def.pattern, re.IGNORECASE if not self.syntax.case_sensitive else 0)
                self.pattern_matchers[pattern_name] = (regex, pattern_def)
            except re.error as e:
                # Skip invalid patterns with warning
                continue
        
        # Build default patterns if not defined in ISA
        self._build_default_patterns()
    
    def _build_default_patterns(self):
        """Build default operand patterns if not defined in ISA"""
        if not self.pattern_matchers:
            # Default register pattern
            register_pattern = r'^' + re.escape(self.register_prefix) + r'([a-zA-Z0-9_]+)$'
            self.pattern_matchers['register'] = (re.compile(register_pattern), OperandPattern(
                name='register',
                type='register',
                pattern=register_pattern,
                description='Register operand'
            ))
            
            # Default immediate pattern
            immediate_pattern = r'^' + re.escape(self.immediate_prefix) + r'([+-]?(?:0x[0-9a-fA-F]+|0b[01]+|\d+))$'
            self.pattern_matchers['immediate'] = (re.compile(immediate_pattern), OperandPattern(
                name='immediate',
                type='immediate',
                pattern=immediate_pattern,
                description='Immediate value'
            ))
            
            # Default label pattern
            label_pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
            self.pattern_matchers['label'] = (re.compile(label_pattern), OperandPattern(
                name='label',
                type='label',
                pattern=label_pattern,
                description='Label reference'
            ))
    
    def parse_operand(self, operand_text: str, line: int, column: int) -> ParsedOperand:
        """Parse a single operand according to ISA syntax rules"""
        operand_text = operand_text.strip()
        
        # Try to match against defined patterns
        for pattern_name, (regex, pattern_def) in self.pattern_matchers.items():
            if regex.match(operand_text):
                return self._parse_by_pattern(operand_text, pattern_def, line, column)
        
        # Try default parsing strategies
        return self._parse_with_defaults(operand_text, line, column)
    
    def _parse_by_pattern(self, operand_text: str, pattern_def: OperandPattern, line: int, column: int) -> ParsedOperand:
        """Parse operand using a specific pattern definition"""
        try:
            if pattern_def.type == 'register':
                return self._parse_register(operand_text, line, column)
            elif pattern_def.type == 'immediate':
                return self._parse_immediate(operand_text, line, column)
            elif pattern_def.type == 'address':
                return self._parse_address(operand_text, line, column)
            elif pattern_def.type == 'label':
                return self._parse_label(operand_text, line, column)
            else:
                # Generic pattern match
                return ParsedOperand(
                    type=pattern_def.type,
                    value=operand_text,
                    original_text=operand_text,
                    line=line,
                    column=column
                )
        except Exception as e:
            return ParsedOperand(
                type=pattern_def.type,
                value=operand_text,
                original_text=operand_text,
                line=line,
                column=column,
                validation_errors=[str(e)]
            )
    
    def _parse_with_defaults(self, operand_text: str, line: int, column: int) -> ParsedOperand:
        """Parse operand using default strategies when no pattern matches"""
        # Try register parsing (without prefix)
        if self._is_register_name(operand_text):
            return self._parse_register(operand_text, line, column)
        
        # Try immediate parsing (without prefix)
        if self._is_immediate_value(operand_text):
            return self._parse_immediate(operand_text, line, column)
        
        # Try label parsing
        if self._is_label_name(operand_text):
            return self._parse_label(operand_text, line, column)
        
        # Unknown operand type
        return ParsedOperand(
            type='unknown',
            value=operand_text,
            original_text=operand_text,
            line=line,
            column=column,
            validation_errors=[f"Unknown operand format: {operand_text}"]
        )
    
    def _parse_register(self, operand_text: str, line: int, column: int) -> ParsedOperand:
        """Parse register operand"""
        # Remove prefix if present
        if operand_text.startswith(self.register_prefix):
            operand_text = operand_text[len(self.register_prefix):]
        
        # Look up register
        register = self._find_register(operand_text)
        if not register:
            return ParsedOperand(
                type='register',
                value=None,
                original_text=operand_text,
                line=line,
                column=column,
                validation_errors=[f"Unknown register: {operand_text}"]
            )
        
        return ParsedOperand(
            type='register',
            value=register,
            original_text=operand_text,
            line=line,
            column=column
        )
    
    def _parse_immediate(self, operand_text: str, line: int, column: int) -> ParsedOperand:
        """Parse immediate value operand"""
        # Remove prefix if present
        if operand_text.startswith(self.immediate_prefix):
            operand_text = operand_text[len(self.immediate_prefix):]
        
        try:
            value = self._parse_number(operand_text)
            return ParsedOperand(
                type='immediate',
                value=value,
                original_text=operand_text,
                line=line,
                column=column
            )
        except ValueError as e:
            return ParsedOperand(
                type='immediate',
                value=None,
                original_text=operand_text,
                line=line,
                column=column,
                validation_errors=[f"Invalid immediate value: {operand_text}"]
            )
    
    def _parse_address(self, operand_text: str, line: int, column: int) -> ParsedOperand:
        """Parse address operand"""
        try:
            value = self._parse_number(operand_text)
            return ParsedOperand(
                type='address',
                value=value,
                original_text=operand_text,
                line=line,
                column=column
            )
        except ValueError as e:
            return ParsedOperand(
                type='address',
                value=None,
                original_text=operand_text,
                line=line,
                column=column,
                validation_errors=[f"Invalid address: {operand_text}"]
            )
    
    def _parse_label(self, operand_text: str, line: int, column: int) -> ParsedOperand:
        """Parse label operand"""
        return ParsedOperand(
            type='label',
            value=operand_text,
            original_text=operand_text,
            line=line,
            column=column
        )
    
    def _find_register(self, name: str) -> Optional[Register]:
        """Find register by name or alias using JSON configuration"""
        # Get alternatives from JSON config
        alternatives = self.reg_config.get('alternatives', {})
        
        # Normalize name for case-insensitive comparison
        if not self.syntax.case_sensitive:
            name = name.upper()
        
        # Check direct name match
        for category, reg_list in self.registers.items():
            for register in reg_list:
                reg_name = register.name.upper() if not self.syntax.case_sensitive else register.name
                if reg_name == name:
                    return register
                
                # Check aliases
                for alias in register.alias:
                    alias_name = alias.upper() if not self.syntax.case_sensitive else alias
                    if alias_name == name:
                        return register
                
                # Check alternatives from JSON config
                if register.name in alternatives:
                    for alt_name in alternatives[register.name]:
                        alt_name_normalized = alt_name.upper() if not self.syntax.case_sensitive else alt_name
                        if alt_name_normalized == name:
                            return register
        
        return None
    
    def _is_register_name(self, text: str) -> bool:
        """Check if text looks like a register name"""
        # Remove prefix if present
        if text.startswith(self.register_prefix):
            text = text[len(self.register_prefix):]
        
        return self._find_register(text) is not None
    
    def _is_immediate_value(self, text: str) -> bool:
        """Check if text looks like an immediate value"""
        # Remove prefix if present
        if text.startswith(self.immediate_prefix):
            text = text[len(self.immediate_prefix):]
        
        try:
            self._parse_number(text)
            return True
        except ValueError:
            return False
    
    def _is_label_name(self, text: str) -> bool:
        """Check if text looks like a label name"""
        # Simple label pattern: starts with letter/underscore, contains alphanumeric/underscore
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', text))
    
    def _parse_number(self, text: str) -> int:
        """Parse number in various formats"""
        text = text.strip()
        
        if text.startswith(self.hex_prefix):
            return int(text[len(self.hex_prefix):], 16)
        elif text.startswith(self.binary_prefix):
            return int(text[len(self.binary_prefix):], 2)
        else:
            return int(text, 10)
    
    def parse_operands(self, operand_text: str, line: int, column: int) -> List[ParsedOperand]:
        """Parse multiple operands from a comma-separated string"""
        operands = []
        current_pos = 0
        
        # Split by separators, respecting quotes and parentheses
        parts = self._split_operands(operand_text)
        
        for i, part in enumerate(parts):
            if part.strip():
                operand = self.parse_operand(part.strip(), line, column + current_pos)
                operands.append(operand)
            current_pos += len(part) + 1  # +1 for separator
        
        return operands
    
    def _split_operands(self, text: str) -> List[str]:
        """Split operand text by separators, respecting nested structures"""
        separators = self.syntax.operand_separators
        if not separators:
            separators = [',']
        
        # Use the first separator as primary
        primary_sep = separators[0]
        
        # Simple split for now - could be enhanced to handle nested structures
        return [part.strip() for part in text.split(primary_sep)] 