"""
Tests for Symbol Table
"""

import pytest
from isa_xform.core.symbol_table import SymbolTable, Symbol, SymbolType, SymbolScope
from isa_xform.utils.error_handling import SymbolError


class TestSymbolTable:
    """Test cases for SymbolTable"""
    
    def setup_method(self):
        """Setup for each test"""
        self.symbol_table = SymbolTable()
    
    def test_define_symbol(self):
        """Test defining a symbol"""
        symbol = self.symbol_table.define_symbol(
            name="start",
            value=0x1000,
            symbol_type=SymbolType.LABEL,
            scope=SymbolScope.LOCAL,
            line=1,
            column=1,
            file="test.s"
        )
        
        assert isinstance(symbol, Symbol)
        assert symbol.name == "start"
        assert symbol.value == 0x1000
        assert symbol.type == SymbolType.LABEL
        assert symbol.scope == SymbolScope.LOCAL
        assert symbol.defined == True
        assert symbol.line == 1
        assert symbol.column == 1
        assert symbol.file == "test.s"
        
        # Check that symbol is in the table
        assert "start" in self.symbol_table.symbols
        assert self.symbol_table.symbols["start"] is symbol
    
    def test_define_duplicate_symbol(self):
        """Test defining a duplicate symbol"""
        # Define symbol first time
        self.symbol_table.define_symbol("start", 0x1000, SymbolType.LABEL)
        
        # Try to define it again
        with pytest.raises(SymbolError, match="Symbol 'start' already defined"):
            self.symbol_table.define_symbol("start", 0x2000, SymbolType.LABEL)
    
    def test_define_symbol_over_forward_reference(self):
        """Test defining a symbol that was previously forward referenced"""
        # First, reference the symbol (creates forward reference)
        symbol = self.symbol_table.reference_symbol("start", 0x1000)
        assert not symbol.defined
        assert len(symbol.forward_references) == 1
        
        # Now define it
        defined_symbol = self.symbol_table.define_symbol("start", 0x2000, SymbolType.LABEL)
        assert defined_symbol.defined
        assert defined_symbol.value == 0x2000
        assert defined_symbol is symbol  # Same object
    
    def test_reference_symbol(self):
        """Test referencing a symbol"""
        symbol = self.symbol_table.reference_symbol("start", 0x1000, 1, 1, "test.s")
        
        assert isinstance(symbol, Symbol)
        assert symbol.name == "start"
        assert symbol.referenced == True
        assert symbol.defined == False
        assert len(symbol.forward_references) == 1
        assert symbol.forward_references[0] == 0x1000
        assert symbol.line == 1
        assert symbol.column == 1
        assert symbol.file == "test.s"
    
    def test_reference_existing_symbol(self):
        """Test referencing an existing symbol"""
        # Define symbol first
        self.symbol_table.define_symbol("start", 0x1000, SymbolType.LABEL)
        
        # Reference it
        symbol = self.symbol_table.reference_symbol("start", 0x2000)
        
        assert symbol.defined == True
        assert symbol.referenced == True
        assert len(symbol.forward_references) == 0  # No forward reference needed
    
    def test_get_symbol(self):
        """Test getting a symbol"""
        # Define a symbol
        defined_symbol = self.symbol_table.define_symbol("start", 0x1000, SymbolType.LABEL)
        
        # Get it
        retrieved_symbol = self.symbol_table.get_symbol("start")
        assert retrieved_symbol is defined_symbol
        
        # Get non-existent symbol
        assert self.symbol_table.get_symbol("nonexistent") is None
    
    def test_resolve_symbol(self):
        """Test resolving a symbol to its value"""
        # Define a symbol
        self.symbol_table.define_symbol("start", 0x1000, SymbolType.LABEL)
        
        # Resolve it
        value = self.symbol_table.resolve_symbol("start")
        assert value == 0x1000
        
        # Resolve undefined symbol
        assert self.symbol_table.resolve_symbol("undefined") is None
        
        # Resolve forward reference
        self.symbol_table.reference_symbol("forward", 0x2000)
        assert self.symbol_table.resolve_symbol("forward") is None
    
    def test_define_label(self):
        """Test defining a label"""
        self.symbol_table.set_current_address(0x1000)
        symbol = self.symbol_table.define_label("start", 1, 1, "test.s")
        
        assert symbol.name == "start"
        assert symbol.value == 0x1000
        assert symbol.type == SymbolType.LABEL
        assert symbol.scope == SymbolScope.LOCAL
        assert symbol.defined == True
        assert symbol.line == 1
        assert symbol.column == 1
        assert symbol.file == "test.s"
    
    def test_define_constant(self):
        """Test defining a constant"""
        symbol = self.symbol_table.define_constant("MAX_SIZE", 1024, 1, 1, "test.s")
        
        assert symbol.name == "MAX_SIZE"
        assert symbol.value == 1024
        assert symbol.type == SymbolType.CONSTANT
        assert symbol.scope == SymbolScope.LOCAL
        assert symbol.defined == True
        assert symbol.line == 1
        assert symbol.column == 1
        assert symbol.file == "test.s"
    
    def test_define_external(self):
        """Test defining an external symbol"""
        symbol = self.symbol_table.define_external("printf", 1, 1, "test.s")
        
        assert symbol.name == "printf"
        assert symbol.value is None
        assert symbol.type == SymbolType.EXTERNAL
        assert symbol.scope == SymbolScope.EXTERNAL
        assert symbol.defined == True
        assert symbol.line == 1
        assert symbol.column == 1
        assert symbol.file == "test.s"
    
    def test_address_management(self):
        """Test address management"""
        assert self.symbol_table.get_current_address() == 0
        
        self.symbol_table.set_current_address(0x1000)
        assert self.symbol_table.get_current_address() == 0x1000
        
        self.symbol_table.advance_address(4)
        assert self.symbol_table.get_current_address() == 0x1004
    
    def test_reset(self):
        """Test resetting the symbol table"""
        # Define some symbols
        self.symbol_table.define_symbol("start", 0x1000, SymbolType.LABEL)
        self.symbol_table.reference_symbol("forward", 0x2000)
        
        # Reset
        self.symbol_table.reset()
        
        # Symbols should still exist but states should be reset
        assert "start" in self.symbol_table.symbols
        assert "forward" in self.symbol_table.symbols
        
        start_symbol = self.symbol_table.symbols["start"]
        assert start_symbol.defined == True  # Still defined
        assert start_symbol.referenced == False  # Reset
        
        forward_symbol = self.symbol_table.symbols["forward"]
        assert forward_symbol.forward_references == []  # Reset
        
        assert self.symbol_table.current_address == 0
        assert self.symbol_table.pass_number == 2
    
    def test_get_undefined_symbols(self):
        """Test getting undefined symbols"""
        # Define some symbols
        self.symbol_table.define_symbol("defined", 0x1000, SymbolType.LABEL)
        self.symbol_table.reference_symbol("undefined", 0x2000)
        
        undefined = self.symbol_table.get_undefined_symbols()
        assert len(undefined) == 1
        assert undefined[0].name == "undefined"
    
    def test_get_unreferenced_symbols(self):
        """Test getting unreferenced symbols"""
        # Define some symbols
        self.symbol_table.define_symbol("unreferenced", 0x1000, SymbolType.LABEL)
        self.symbol_table.define_symbol("referenced", 0x2000, SymbolType.LABEL)
        self.symbol_table.reference_symbol("referenced", 0x3000)
        
        unreferenced = self.symbol_table.get_unreferenced_symbols()
        assert len(unreferenced) == 1
        assert unreferenced[0].name == "unreferenced"
    
    def test_get_forward_references(self):
        """Test getting symbols with forward references"""
        # Create some forward references
        self.symbol_table.reference_symbol("forward1", 0x1000)
        self.symbol_table.reference_symbol("forward2", 0x2000)
        self.symbol_table.define_symbol("defined", 0x3000, SymbolType.LABEL)
        
        forward_refs = self.symbol_table.get_forward_references()
        assert len(forward_refs) == 2
        assert any(s.name == "forward1" for s in forward_refs)
        assert any(s.name == "forward2" for s in forward_refs)
    
    def test_validate(self):
        """Test symbol table validation"""
        # Create some invalid state
        self.symbol_table.reference_symbol("undefined", 0x1000)  # Referenced but not defined
        
        errors = self.symbol_table.validate()
        assert len(errors) == 1
        assert "Undefined symbol 'undefined' is referenced" in errors[0]
    
    def test_get_symbols_by_type(self):
        """Test getting symbols by type"""
        self.symbol_table.define_symbol("label1", 0x1000, SymbolType.LABEL)
        self.symbol_table.define_symbol("label2", 0x2000, SymbolType.LABEL)
        self.symbol_table.define_symbol("const1", 42, SymbolType.CONSTANT)
        
        labels = self.symbol_table.get_symbols_by_type(SymbolType.LABEL)
        assert len(labels) == 2
        assert all(s.type == SymbolType.LABEL for s in labels)
        
        constants = self.symbol_table.get_symbols_by_type(SymbolType.CONSTANT)
        assert len(constants) == 1
        assert constants[0].name == "const1"
    
    def test_get_symbols_by_scope(self):
        """Test getting symbols by scope"""
        self.symbol_table.define_symbol("local1", 0x1000, SymbolType.LABEL, SymbolScope.LOCAL)
        self.symbol_table.define_symbol("global1", 0x2000, SymbolType.LABEL, SymbolScope.GLOBAL)
        self.symbol_table.define_symbol("external1", None, SymbolType.EXTERNAL, SymbolScope.EXTERNAL)
        
        local_symbols = self.symbol_table.get_symbols_by_scope(SymbolScope.LOCAL)
        assert len(local_symbols) == 1
        assert local_symbols[0].name == "local1"
        
        global_symbols = self.symbol_table.get_symbols_by_scope(SymbolScope.GLOBAL)
        assert len(global_symbols) == 1
        assert global_symbols[0].name == "global1"
        
        external_symbols = self.symbol_table.get_symbols_by_scope(SymbolScope.EXTERNAL)
        assert len(external_symbols) == 1
        assert external_symbols[0].name == "external1"
    
    def test_export_symbols(self):
        """Test exporting symbols"""
        self.symbol_table.define_symbol("local", 0x1000, SymbolType.LABEL, SymbolScope.LOCAL)
        self.symbol_table.define_symbol("global", 0x2000, SymbolType.LABEL, SymbolScope.GLOBAL)
        self.symbol_table.define_symbol("constant", 42, SymbolType.CONSTANT, SymbolScope.GLOBAL)
        
        exported = self.symbol_table.export_symbols()
        
        assert "local" not in exported  # Local symbols not exported
        assert "global" in exported
        assert "constant" in exported
        
        assert exported["global"]["value"] == 0x2000
        assert exported["global"]["type"] == "label"
        assert exported["constant"]["value"] == 42
        assert exported["constant"]["type"] == "constant"
    
    def test_import_symbols(self):
        """Test importing symbols"""
        symbol_data = {
            "printf": {"value": 0x1000, "type": "external", "size": None},
            "malloc": {"value": 0x2000, "type": "external", "size": None}
        }
        
        self.symbol_table.import_symbols(symbol_data)
        
        assert "printf" in self.symbol_table.symbols
        assert "malloc" in self.symbol_table.symbols
        
        printf_symbol = self.symbol_table.symbols["printf"]
        assert printf_symbol.type == SymbolType.EXTERNAL
        assert printf_symbol.scope == SymbolScope.EXTERNAL
        assert printf_symbol.value == 0x1000
        assert printf_symbol.defined == True
    
    def test_clear(self):
        """Test clearing the symbol table"""
        # Add some symbols
        self.symbol_table.define_symbol("start", 0x1000, SymbolType.LABEL)
        self.symbol_table.reference_symbol("forward", 0x2000)
        self.symbol_table.set_current_address(0x3000)
        
        # Clear
        self.symbol_table.clear()
        
        assert len(self.symbol_table.symbols) == 0
        assert self.symbol_table.current_address == 0
        assert self.symbol_table.pass_number == 1
        assert len(self.symbol_table.errors) == 0
        assert len(self.symbol_table.warnings) == 0
    
    def test_get_statistics(self):
        """Test getting symbol table statistics"""
        # Add various symbols
        self.symbol_table.define_symbol("defined1", 0x1000, SymbolType.LABEL)
        self.symbol_table.define_symbol("defined2", 0x2000, SymbolType.CONSTANT)
        self.symbol_table.reference_symbol("undefined", 0x3000)
        self.symbol_table.reference_symbol("defined1", 0x4000)  # Reference defined symbol
        
        stats = self.symbol_table.get_statistics()
        
        assert stats["total_symbols"] == 3
        assert stats["defined_symbols"] == 2
        assert stats["undefined_symbols"] == 1
        assert stats["referenced_symbols"] == 2
        assert stats["unreferenced_symbols"] == 1
        assert stats["forward_references"] == 1  # Only undefined symbol has forward references
        assert stats["label_symbols"] == 2  # defined1 and undefined are both labels
        assert stats["constant_symbols"] == 1


class TestSymbol:
    """Test cases for Symbol"""
    
    def test_symbol_creation(self):
        """Test creating a Symbol"""
        symbol = Symbol(
            name="start",
            type=SymbolType.LABEL,
            scope=SymbolScope.LOCAL,
            value=0x1000,
            size=16,
            line=1,
            column=1,
            file="test.s",
            defined=True,
            referenced=True
        )
        
        assert symbol.name == "start"
        assert symbol.type == SymbolType.LABEL
        assert symbol.scope == SymbolScope.LOCAL
        assert symbol.value == 0x1000
        assert symbol.size == 16
        assert symbol.line == 1
        assert symbol.column == 1
        assert symbol.file == "test.s"
        assert symbol.defined == True
        assert symbol.referenced == True
        assert symbol.forward_references == []
    
    def test_symbol_defaults(self):
        """Test Symbol with default values"""
        symbol = Symbol("start", SymbolType.LABEL, SymbolScope.LOCAL, 0x1000)
        
        assert symbol.name == "start"
        assert symbol.type == SymbolType.LABEL
        assert symbol.scope == SymbolScope.LOCAL
        assert symbol.value == 0x1000
        assert symbol.size is None
        assert symbol.line is None
        assert symbol.column is None
        assert symbol.file is None
        assert symbol.defined == False
        assert symbol.referenced == False
        assert symbol.forward_references == [] 