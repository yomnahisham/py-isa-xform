"""
Symbol Table: Manages labels, constants, and memory references
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from ..utils.error_handling import SymbolError, ErrorLocation


class SymbolType(Enum):
    """Types of symbols"""
    LABEL = "label"
    CONSTANT = "constant"
    REGISTER = "register"
    EXTERNAL = "external"
    LOCAL = "local"
    GLOBAL = "global"


class SymbolScope(Enum):
    """Symbol scopes"""
    LOCAL = "local"
    GLOBAL = "global"
    EXTERNAL = "external"


@dataclass
class Symbol:
    """Represents a symbol in the symbol table"""
    name: str
    type: SymbolType
    scope: SymbolScope
    value: Any
    size: Optional[int] = None
    line: Optional[int] = None
    column: Optional[int] = None
    file: Optional[str] = None
    defined: bool = False
    referenced: bool = False
    forward_references: List[int] = field(default_factory=list)


class SymbolTable:
    """Manages symbols for assembly code"""
    
    def __init__(self):
        self.symbols: Dict[str, Symbol] = {}
        self.current_address = 0
        self.pass_number = 1
        self.errors: List[SymbolError] = []
        self.warnings: List[str] = []
    
    def reset(self):
        """Reset the symbol table for a new pass"""
        self.current_address = 0
        self.pass_number += 1
        self.errors.clear()
        self.warnings.clear()
        
        # Reset symbol states but keep definitions
        for symbol in self.symbols.values():
            symbol.referenced = False
            symbol.forward_references.clear()
    
    def define_symbol(self, name: str, value: Any, symbol_type: SymbolType = SymbolType.LABEL,
                     scope: SymbolScope = SymbolScope.LOCAL, size: Optional[int] = None,
                     line: Optional[int] = None, column: Optional[int] = None,
                     file: Optional[str] = None) -> Symbol:
        """
        Define a new symbol
        
        Args:
            name: Symbol name
            value: Symbol value (address, constant, etc)
            symbol_type: Type of symbol
            scope: Symbol scope
            size: Size in bytes (for variables)
            line: Line number where defined
            column: Column number where defined
            file: File where defined
        
        Returns:
            The defined symbol
        
        Raises:
            SymbolError: If symbol is already defined
        """
        if name in self.symbols:
            existing = self.symbols[name]
            if existing.defined:
                raise SymbolError(
                    f"Symbol '{name}' already defined",
                    name,
                    ErrorLocation(line or 0, column or 0, file)
                )
            else:
                # Update existing forward reference
                existing.value = value
                existing.type = symbol_type
                existing.scope = scope
                existing.size = size
                existing.line = line
                existing.column = column
                existing.file = file
                existing.defined = True
                return existing
        
        symbol = Symbol(
            name=name,
            type=symbol_type,
            scope=scope,
            value=value,
            size=size,
            line=line,
            column=column,
            file=file,
            defined=True
        )
        
        self.symbols[name] = symbol
        return symbol
    
    def reference_symbol(self, name: str, address: int, line: Optional[int] = None,
                        column: Optional[int] = None, file: Optional[str] = None) -> Symbol:
        """
        Reference a symbol (may be forward reference)
        
        Args:
            name: Symbol name
            address: Address where symbol is referenced
            line: Line number of reference
            column: Column number of reference
            file: File of reference
        
        Returns:
            The referenced symbol
        
        Raises:
            SymbolError: If symbol cannot be resolved
        """
        if name in self.symbols:
            symbol = self.symbols[name]
            symbol.referenced = True
            
            if not symbol.defined:
                # Forward reference
                symbol.forward_references.append(address)
                if self.pass_number == 1:
                    self.warnings.append(f"Forward reference to '{name}' at address {address}")
            
            return symbol
        else:
            # Create undefined symbol for forward reference
            symbol = Symbol(
                name=name,
                type=SymbolType.LABEL,
                scope=SymbolScope.LOCAL,
                value=None,
                line=line,
                column=column,
                file=file,
                defined=False
            )
            symbol.forward_references.append(address)
            symbol.referenced = True
            
            self.symbols[name] = symbol
            
            if self.pass_number == 1:
                self.warnings.append(f"Forward reference to undefined symbol '{name}' at address {address}")
            
            return symbol
    
    def get_symbol(self, name: str) -> Optional[Symbol]:
        """
        Get a symbol by name
        
        Args:
            name: Symbol name
        
        Returns:
            Symbol if found, None otherwise
        """
        return self.symbols.get(name)
    
    def resolve_symbol(self, name: str) -> Optional[Any]:
        """
        Resolve a symbol to its value
        
        Args:
            name: Symbol name
        
        Returns:
            Symbol value if found and defined, None otherwise
        """
        symbol = self.symbols.get(name)
        if symbol and symbol.defined:
            return symbol.value
        return None
    
    def set_current_address(self, address: int):
        """Set the current assembly address"""
        self.current_address = address
    
    def get_current_address(self) -> int:
        """Get the current assembly address"""
        return self.current_address
    
    def advance_address(self, bytes_to_advance: int):
        """Advance the current address by the specified number of bytes"""
        self.current_address += bytes_to_advance
    
    def define_label(self, name: str, line: Optional[int] = None, column: Optional[int] = None,
                    file: Optional[str] = None) -> Symbol:
        """
        Define a label at the current address
        
        Args:
            name: Label name
            line: Line number
            column: Column number
            file: File name
        
        Returns:
            The defined label symbol
        """
        return self.define_symbol(
            name=name,
            value=self.current_address,
            symbol_type=SymbolType.LABEL,
            scope=SymbolScope.LOCAL,
            line=line,
            column=column,
            file=file
        )
    
    def define_constant(self, name: str, value: Any, line: Optional[int] = None,
                       column: Optional[int] = None, file: Optional[str] = None) -> Symbol:
        """
        Define a constant
        
        Args:
            name: Constant name
            value: Constant value
            line: Line number
            column: Column number
            file: File name
        
        Returns:
            The defined constant symbol
        """
        return self.define_symbol(
            name=name,
            value=value,
            symbol_type=SymbolType.CONSTANT,
            scope=SymbolScope.LOCAL,
            line=line,
            column=column,
            file=file
        )
    
    def define_external(self, name: str, line: Optional[int] = None, column: Optional[int] = None,
                       file: Optional[str] = None) -> Symbol:
        """
        Declare an external symbol
        
        Args:
            name: External symbol name
            line: Line number
            column: Column number
            file: File name
        
        Returns:
            The external symbol
        """
        return self.define_symbol(
            name=name,
            value=None,
            symbol_type=SymbolType.EXTERNAL,
            scope=SymbolScope.EXTERNAL,
            line=line,
            column=column,
            file=file
        )
    
    def get_undefined_symbols(self) -> List[Symbol]:
        """Get all undefined symbols"""
        return [symbol for symbol in self.symbols.values() if not symbol.defined]
    
    def get_unreferenced_symbols(self) -> List[Symbol]:
        """Get all defined but unreferenced symbols"""
        return [symbol for symbol in self.symbols.values() if symbol.defined and not symbol.referenced]
    
    def get_forward_references(self) -> List[Symbol]:
        """Get all symbols with forward references"""
        return [symbol for symbol in self.symbols.values() if symbol.forward_references]
    
    def resolve_forward_references(self):
        """Resolve all forward references (called after first pass)"""
        for symbol in self.symbols.values():
            if symbol.forward_references and symbol.defined:
                # Forward references are resolved by updating the symbol value
                # This is typically done by the assembler during the second pass
                pass
    
    def validate(self) -> List[str]:
        """
        Validate the symbol table
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for undefined symbols
        undefined = self.get_undefined_symbols()
        for symbol in undefined:
            if symbol.referenced:
                errors.append(f"Undefined symbol '{symbol.name}' is referenced")
        
        # Check for unreferenced symbols (warning)
        unreferenced = self.get_unreferenced_symbols()
        for symbol in unreferenced:
            if symbol.type == SymbolType.LABEL:
                self.warnings.append(f"Label '{symbol.name}' is defined but never referenced")
        
        return errors
    
    def get_symbols_by_type(self, symbol_type: SymbolType) -> List[Symbol]:
        """Get all symbols of a specific type"""
        return [symbol for symbol in self.symbols.values() if symbol.type == symbol_type]
    
    def get_symbols_by_scope(self, scope: SymbolScope) -> List[Symbol]:
        """Get all symbols of a specific scope"""
        return [symbol for symbol in self.symbols.values() if symbol.scope == scope]
    
    def export_symbols(self) -> Dict[str, Any]:
        """Export symbols for linking"""
        export_data = {}
        for name, symbol in self.symbols.items():
            if symbol.defined and symbol.scope == SymbolScope.GLOBAL:
                export_data[name] = {
                    'value': symbol.value,
                    'type': symbol.type.value,
                    'size': symbol.size
                }
        return export_data
    
    def import_symbols(self, symbol_data: Dict[str, Any]):
        """Import symbols from another module"""
        for name, data in symbol_data.items():
            if name not in self.symbols:
                symbol = Symbol(
                    name=name,
                    type=SymbolType(data['type']),
                    scope=SymbolScope.EXTERNAL,
                    value=data['value'],
                    size=data.get('size'),
                    defined=True
                )
                self.symbols[name] = symbol
    
    def clear(self):
        """Clear all symbols"""
        self.symbols.clear()
        self.current_address = 0
        self.pass_number = 1
        self.errors.clear()
        self.warnings.clear()
    
    def get_statistics(self) -> Dict[str, int]:
        """Get symbol table statistics"""
        stats = {
            'total_symbols': len(self.symbols),
            'defined_symbols': len([s for s in self.symbols.values() if s.defined]),
            'undefined_symbols': len([s for s in self.symbols.values() if not s.defined]),
            'referenced_symbols': len([s for s in self.symbols.values() if s.referenced]),
            'unreferenced_symbols': len([s for s in self.symbols.values() if not s.referenced]),
            'forward_references': len([s for s in self.symbols.values() if s.forward_references])
        }
        
        # Count by type
        for symbol_type in SymbolType:
            stats[f'{symbol_type.value}_symbols'] = len(self.get_symbols_by_type(symbol_type))
        
        return stats 