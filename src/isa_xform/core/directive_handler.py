"""
Modular Directive Handler: Handles ISA-specific directives
"""

from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from .isa_loader import ISADefinition, Directive
from .symbol_table import SymbolTable
from ..utils.error_handling import AssemblerError, ErrorLocation


@dataclass
class DirectiveContext:
    """Context for directive processing"""
    current_address: int
    current_section: str
    symbol_table: SymbolTable
    isa_definition: ISADefinition
    pass_number: int = 1


@dataclass
class DirectiveResult:
    """Result of directive processing"""
    bytes_generated: Optional[bytes] = None
    address_change: int = 0
    section_change: Optional[str] = None
    symbols_defined: Dict[str, int] = None
    
    def __post_init__(self):
        if self.symbols_defined is None:
            self.symbols_defined = {}


class DirectiveHandler:
    """Modular directive handler that adapts to ISA definitions"""
    
    def __init__(self, isa_definition: ISADefinition):
        self.isa_definition = isa_definition
        self.directives = isa_definition.directives
        self.syntax = isa_definition.assembly_syntax
        
        # Build directive handlers
        self._build_handlers()
    
    def _build_handlers(self):
        """Build directive handler mapping"""
        self.handlers = {}
        
        # Register built-in handlers
        self._register_builtin_handlers()
        
        # Register ISA-specific handlers
        self._register_isa_handlers()
    
    def _register_builtin_handlers(self):
        """Register built-in directive handlers"""
        self.handlers.update({
            '.org': self._handle_org,
            '.word': self._handle_word,
            '.byte': self._handle_byte,
            '.space': self._handle_space,
            '.ascii': self._handle_ascii,
            '.asciiz': self._handle_asciiz,
            '.section': self._handle_section,
            '.global': self._handle_global,
            '.equ': self._handle_equ,
            '.align': self._handle_align,
            '.data': self._handle_data,
            '.text': self._handle_text,
            '.bss': self._handle_bss,
        })
    
    def _register_isa_handlers(self):
        """Register ISA-specific directive handlers"""
        for directive_name, directive_def in self.directives.items():
            if directive_def.handler:
                # Try to get handler method
                handler_method = getattr(self, f"_handle_{directive_def.handler}", None)
                if handler_method:
                    self.handlers[directive_name] = handler_method
                else:
                    # Use generic handler
                    self.handlers[directive_name] = self._handle_generic
    
    def handle_directive(self, directive_name: str, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle a directive with given arguments"""
        # Normalize directive name
        directive_name = directive_name.lower()
        
        # Find handler
        handler = self.handlers.get(directive_name)
        if not handler:
            raise AssemblerError(f"Unknown directive: {directive_name}")
        
        try:
            return handler(arguments, context)
        except Exception as e:
            raise AssemblerError(f"Error processing directive {directive_name}: {e}")
    
    def _handle_org(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .org directive"""
        if not arguments:
            raise AssemblerError(".org requires an address argument")
        
        try:
            address = self._parse_address(arguments[0])
            return DirectiveResult(address_change=address - context.current_address)
        except ValueError:
            raise AssemblerError(f"Invalid address in .org directive: {arguments[0]}")
    
    def _handle_word(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .word directive"""
        if not arguments:
            raise AssemblerError(".word requires at least one value")
        
        values = []
        for arg in arguments:
            try:
                value = self._parse_number(arg)
                values.append(value)
            except ValueError:
                raise AssemblerError(f"Invalid value in .word directive: {arg}")
        
        # Convert to bytes
        word_size = self.isa_definition.word_size // 8
        endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
        
        bytes_data = bytearray()
        for value in values:
            bytes_data.extend(value.to_bytes(word_size, endianness))
        
        return DirectiveResult(bytes_generated=bytes_data)
    
    def _handle_byte(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .byte directive"""
        if not arguments:
            raise AssemblerError(".byte requires at least one value")
        
        values = []
        for arg in arguments:
            try:
                value = self._parse_number(arg)
                if not (0 <= value <= 255):
                    raise ValueError(f"Byte value out of range: {value}")
                values.append(value)
            except ValueError as e:
                raise AssemblerError(f"Invalid value in .byte directive: {arg}")
        
        return DirectiveResult(bytes_generated=bytes(values))
    
    def _handle_space(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .space directive"""
        if not arguments:
            raise AssemblerError(".space requires a size argument")
        
        try:
            size = self._parse_number(arguments[0])
            if size < 0:
                raise ValueError("Space size cannot be negative")
            return DirectiveResult(bytes_generated=b'\x00' * size)
        except ValueError:
            raise AssemblerError(f"Invalid size in .space directive: {arguments[0]}")
    
    def _handle_ascii(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .ascii directive"""
        if not arguments:
            raise AssemblerError(".ascii requires a string argument")
        
        # Join arguments and handle quotes
        string_arg = ' '.join(arguments)
        if string_arg.startswith('"') and string_arg.endswith('"'):
            string_arg = string_arg[1:-1]
        
        return DirectiveResult(bytes_generated=string_arg.encode('ascii'))
    
    def _handle_asciiz(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .asciiz directive"""
        result = self._handle_ascii(arguments, context)
        if result.bytes_generated:
            # Add null terminator
            result.bytes_generated += b'\x00'
        return result
    
    def _handle_section(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .section directive"""
        if not arguments:
            raise AssemblerError(".section requires a section name")
        
        section_name = arguments[0]
        return DirectiveResult(section_change=section_name)
    
    def _handle_global(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .global directive"""
        if not arguments:
            raise AssemblerError(".global requires at least one symbol name")
        
        # Mark symbols as global (handled by symbol table)
        for symbol_name in arguments:
            context.symbol_table.mark_global(symbol_name)
        
        return DirectiveResult()
    
    def _handle_equ(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .equ directive"""
        if len(arguments) < 2:
            raise AssemblerError(".equ requires a symbol name and value")
        
        symbol_name = arguments[0]
        try:
            value = self._parse_number(arguments[1])
            context.symbol_table.define_constant(symbol_name, value)
            return DirectiveResult(symbols_defined={symbol_name: value})
        except ValueError:
            raise AssemblerError(f"Invalid value in .equ directive: {arguments[1]}")
    
    def _handle_align(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .align directive"""
        if not arguments:
            raise AssemblerError(".align requires an alignment value")
        
        try:
            alignment = self._parse_number(arguments[0])
            if alignment <= 0:
                raise ValueError("Alignment must be positive")
            
            # Calculate padding needed
            current_offset = context.current_address % alignment
            if current_offset != 0:
                padding = alignment - current_offset
                return DirectiveResult(bytes_generated=b'\x00' * padding)
            
            return DirectiveResult()
        except ValueError:
            raise AssemblerError(f"Invalid alignment value: {arguments[0]}")
    
    def _handle_data(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .data directive"""
        return DirectiveResult(section_change="data")
    
    def _handle_text(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .text directive"""
        return DirectiveResult(section_change="text")
    
    def _handle_bss(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .bss directive"""
        return DirectiveResult(section_change="bss")
    
    def _handle_fill(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Handle .fill directive - Fill N items, M bytes each, with value"""
        if len(arguments) < 3:
            raise AssemblerError(".fill requires three arguments: count, size, value")
        
        try:
            count = self._parse_number(arguments[0])
            size = self._parse_number(arguments[1])
            value = self._parse_number(arguments[2])
            
            if count < 0:
                raise ValueError("Count cannot be negative")
            if size <= 0:
                raise ValueError("Size must be positive")
            if value < 0 or value >= (1 << (size * 8)):
                raise ValueError(f"Value {value} does not fit in {size} bytes")
            
            # Generate the fill data
            endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
            bytes_data = bytearray()
            for _ in range(count):
                bytes_data.extend(value.to_bytes(size, endianness))
            
            return DirectiveResult(bytes_generated=bytes_data)
        except ValueError as e:
            raise AssemblerError(f"Invalid argument in .fill directive: {e}")
    
    def _handle_generic(self, arguments: List[str], context: DirectiveContext) -> DirectiveResult:
        """Generic handler for ISA-specific directives"""
        # This could be extended to support custom directive implementations
        # For now, just return empty result
        return DirectiveResult()
    
    def _parse_number(self, text: str) -> int:
        """Parse number in various formats"""
        text = text.strip()
        
        if text.startswith(self.syntax.hex_prefix):
            return int(text[len(self.syntax.hex_prefix):], 16)
        elif text.startswith(self.syntax.binary_prefix):
            return int(text[len(self.syntax.binary_prefix):], 2)
        else:
            return int(text, 10)
    
    def _parse_address(self, text: str) -> int:
        """Parse address value"""
        return self._parse_number(text)
    
    def get_supported_directives(self) -> List[str]:
        """Get list of supported directive names"""
        return list(self.handlers.keys())
    
    def validate_directive(self, directive_name: str, arguments: List[str]) -> List[str]:
        """Validate directive arguments and return list of errors"""
        errors = []
        
        # Check if directive exists
        if directive_name not in self.handlers:
            errors.append(f"Unknown directive: {directive_name}")
            return errors
        
        # Get directive definition if available
        directive_def = self.directives.get(directive_name)
        if directive_def:
            # Validate argument count
            expected_count = len(directive_def.argument_types)
            if len(arguments) != expected_count:
                errors.append(f"Directive {directive_name} expects {expected_count} arguments, got {len(arguments)}")
            
            # Validate argument types
            for i, (arg, expected_type) in enumerate(zip(arguments, directive_def.argument_types)):
                if not self._validate_argument_type(arg, expected_type):
                    errors.append(f"Argument {i+1} of {directive_name} should be {expected_type}, got: {arg}")
        
        return errors
    
    def _validate_argument_type(self, argument: str, expected_type: str) -> bool:
        """Validate that argument matches expected type"""
        try:
            if expected_type == "number":
                self._parse_number(argument)
                return True
            elif expected_type == "string":
                return True  # All arguments are strings initially
            elif expected_type == "address":
                self._parse_address(argument)
                return True
            elif expected_type == "symbol":
                return bool(argument and argument.replace('_', '').isalnum())
            else:
                return True  # Unknown type, assume valid
        except ValueError:
            return False 