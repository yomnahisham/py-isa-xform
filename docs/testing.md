# Testing Guide

## Overview

This document explains how to test the py-isa-xform toolkit, including running the test suite and writing basic tests.

## Running Tests

### Prerequisites

- Python 3.8 or higher
- pytest (install with `pip install pytest`)
- All project dependencies installed

### Basic Test Execution

#### Run All Tests
```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run all tests with minimal output
python -m pytest tests/

# Run all tests and show coverage
python -m pytest tests/ --cov=src/isa_xform
```

#### Run Specific Test Files
```bash
# Run parser tests only
python -m pytest tests/test_parser.py -v

# Run ISA loader tests only
python -m pytest tests/test_isa_loader.py -v

# Run symbol table tests only
python -m pytest tests/test_symbol_table.py -v
```

#### Run Specific Test Classes or Methods
```bash
# Run specific test class
python -m pytest tests/test_parser.py::TestParser -v

# Run specific test method
python -m pytest tests/test_parser.py::TestParser::test_parse_basic_instructions -v
```

### Test Filtering and Debugging

```bash
# Run only tests matching a pattern
python -m pytest tests/ -k "parser" -v

# Run with detailed output for debugging
python -m pytest tests/ -s -v

# Run with short traceback
python -m pytest tests/ --tb=short
```

## Writing Tests

### Test Structure

```python
def test_function_name():
    """Test description explaining what is being tested."""
    # Arrange: Set up test data and conditions
    input_data = "test input"
    expected_output = "expected result"
    
    # Act: Execute the function being tested
    actual_output = function_under_test(input_data)
    
    # Assert: Verify the results
    assert actual_output == expected_output
```

### Test Class Structure

```python
class TestComponentName:
    """Test class for ComponentName functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.test_data = "test data"
        self.component = ComponentName()
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = self.component.process(self.test_data)
        assert result is not None
    
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            self.component.process(None)
```

### Using Fixtures

```python
@pytest.fixture
def sample_isa_definition():
    """Provide a sample ISA definition for testing."""
    return {
        "name": "TestISA",
        "word_size": 32,
        "endianness": "little",
        "registers": {"r0": {"name": "r0", "bits": 32, "description": "Register 0"}},
        "instructions": {},
        "addressing_modes": {}
    }

def test_isa_loading(sample_isa_definition):
    """Test ISA loading with sample data."""
    isa_def = load_isa_definition_from_dict(sample_isa_definition)
    assert isa_def.name == "TestISA"
```

## Test Categories

### Unit Tests

Test individual functions and methods in isolation.

```python
def test_add_symbol_basic():
    """Test basic symbol addition."""
    symbol_table = SymbolTable()
    symbol_table.add_symbol("test", 0x1000, "label")
    assert symbol_table.has_symbol("test")
    assert symbol_table.get_symbol("test").value == 0x1000
```

### Integration Tests

Test that multiple components work together correctly.

```python
def test_parser_symbol_table_integration():
    """Test integration between parser and symbol table."""
    isa_def = load_isa_definition("simple_risc.json")
    parser = Parser(isa_def)
    symbol_table = SymbolTable()
    
    assembly_code = """
    main:
        add r1, r2, r3
    """
    nodes = parser.parse(assembly_code)
    
    for node in nodes:
        if isinstance(node, LabelNode):
            symbol_table.add_symbol(node.name, 0x1000, "label")
    
    assert symbol_table.has_symbol("main")
```

## Troubleshooting

### Common Issues

```bash
# Get detailed error information
python -m pytest tests/ -v -s --tb=long

# Install package in development mode
pip install -e .

# Run tests with timing information
python -m pytest tests/ --durations=10
```

### Debugging Tests

```python
def test_debug_example():
    """Example of debugging a test."""
    # Add debug prints
    print("Debug: Starting test")
    
    # Test code here
    result = function_under_test()
    
    print(f"Debug: Result = {result}")
    assert result == expected_value
```