# Error Handling Documentation

The Error Handling module provides comprehensive error management for the ISA transformation toolkit. It includes custom exception classes, error context tracking, and sophisticated error reporting capabilities.

## Overview

The error handling system provides:
- Custom exception hierarchies for different error types
- Detailed error context with location information
- Error collection and batch reporting
- Suggestions and resolution hints
- Integration with all toolkit components

## Core Exception Classes

### Base Exception: ISAError

All toolkit exceptions inherit from `ISAError`:

```python
from isa_xform.utils.error_handling import ISAError, ErrorLocation

# Create error with location context
location = ErrorLocation(line=15, column=20, file="main.s", context="LDI $r1, #256")
error = ISAError("Invalid immediate value", location, suggestion="Use value 0-255")
```

**Attributes:**
- `message`: Error description
- `location`: Optional ErrorLocation with file/line/column
- `suggestion`: Optional resolution hint

### Specific Exception Types

#### ISALoadError
Raised when ISA definition loading fails:
```python
ISALoadError("ISA file not found: custom.json")
```

#### ISAValidationError
Raised when ISA definition is invalid:
```python
ISAValidationError("Missing required field 'word_size'", field="word_size")
```

#### ParseError
Raised during assembly parsing:
```python
ParseError("Expected register", location, expected="register", found="123")
```

#### SymbolError
Raised for symbol resolution issues:
```python
SymbolError("Undefined symbol", symbol="main", location)
```

#### AssemblerError
Raised during assembly process:
```python
AssemblerError("Immediate doesn't fit in 8-bit field")
```

#### DisassemblerError
Raised during disassembly:
```python
DisassemblerError("Invalid instruction encoding")
```

#### BitUtilsError
Raised for bit manipulation errors:
```python
BitUtilsError("Bit width must be positive")
```

#### ConfigurationError
Raised for configuration issues:
```python
ConfigurationError("Invalid endianness setting")
```

## Error Context

### ErrorLocation

Provides detailed context for errors:

```python
from isa_xform.utils.error_handling import ErrorLocation

location = ErrorLocation(
    line=15,
    column=20,
    file="program.s",
    context="LDI $r1, #256  # Load immediate"
)
```

**Attributes:**
- `line`: Line number (1-indexed)
- `column`: Column number (1-indexed)
- `file`: Source file name (optional)
- `context`: Source line text (optional)

## Error Reporter

### ErrorReporter Class

Collects and manages multiple errors and warnings:

```python
from isa_xform.utils.error_handling import ErrorReporter

# Create reporter with error limit
reporter = ErrorReporter(max_errors=100)

# Add errors and warnings
reporter.add_error(ISAError("First error"))
reporter.add_warning("Deprecated syntax", location)

# Check status
if reporter.has_errors():
    print(reporter.format_errors())
    reporter.raise_if_errors()
```

**Key Methods:**
- `add_error(error)`: Add an error to collection
- `add_warning(message, location=None)`: Add warning
- `has_errors()`, `has_warnings()`: Check if any exist
- `format_errors()`, `format_warnings()`: Format for display
- `format_summary()`: Get summary statistics
- `raise_if_errors()`: Raise first error if any exist
- `clear()`: Clear all errors and warnings

## Usage Patterns

### Basic Error Handling

```python
from isa_xform.utils.error_handling import ErrorReporter, AssemblerError

def assemble_file(filename):
    reporter = ErrorReporter()
    
    try:
        # Assembly operations
        result = assembler.assemble(nodes)
        return result
    except AssemblerError as e:
        reporter.add_error(e)
        print(reporter.format_errors())
        return None
```

### Batch Error Collection

```python
def validate_multiple_files(filenames):
    reporter = ErrorReporter()
    
    for filename in filenames:
        try:
            validate_file(filename)
        except ISAError as e:
            reporter.add_error(e)
    
    if reporter.has_errors():
        print(f"Validation failed: {reporter.format_summary()}")
        print(reporter.format_errors())
```

### Context-Rich Errors

```python
def parse_instruction(line_text, line_num, filename):
    try:
        # Parsing logic
        return parse_line(line_text)
    except Exception as e:
        location = ErrorLocation(
            line=line_num,
            column=find_error_column(line_text),
            file=filename,
            context=line_text.strip()
        )
        raise ParseError(
            f"Failed to parse instruction: {e}",
            location,
            suggestion="Check instruction syntax in ISA documentation"
        )
```

## Error Message Formatting

### Standard Format

Errors include comprehensive information:

```
Error: Immediate value 256 doesn't fit in 8-bit unsigned field at line 15, column 20 in main.s
  Context: LDI $r1, #256
  Suggestion: Use a value between 0 and 255, or use a different instruction
```

### Summary Format

For multiple errors:

```
Validation Summary: 3 errors, 2 warnings

Errors:
  1. Missing required field 'word_size' at line 5, column 1 in isa.json
  2. Invalid instruction format at line 12, column 8 in isa.json
  3. Undefined register 'R99' at line 20, column 15 in isa.json

Warnings:
  1. Deprecated directive '.old_syntax' at line 8, column 1 in program.s
  2. Unused symbol 'debug_flag' at line 25, column 1 in program.s
```

## Integration with Components

### Parser Integration

```python
from isa_xform.core.parser import Parser
from isa_xform.utils.error_handling import ErrorReporter, ParseError

parser = Parser(isa_definition)
reporter = ErrorReporter()

try:
    nodes = parser.parse(source_code, filename)
except ParseError as e:
    reporter.add_error(e)
```

### Assembler Integration

```python
from isa_xform.core.assembler import Assembler
from isa_xform.utils.error_handling import AssemblerError

try:
    result = assembler.assemble(nodes)
except AssemblerError as e:
    # Error includes detailed context
    print(f"Assembly failed: {e}")
```

### ISA Loader Integration

```python
from isa_xform.core.isa_loader import ISALoader
from isa_xform.utils.error_handling import ISALoadError

try:
    isa_def = loader.load_isa("custom_isa")
except ISALoadError as e:
    print(f"Failed to load ISA: {e}")
```

## Best Practices

### Error Creation

1. **Always provide context**: Include file, line, and column when available
2. **Add helpful suggestions**: Guide users toward solutions
3. **Use appropriate error types**: Choose the most specific exception class
4. **Include relevant data**: Add symbol names, field names, etc.

### Error Handling

1. **Collect errors when possible**: Don't stop at first error
2. **Provide summaries**: Give overview before detailed errors
3. **Format consistently**: Use standard formatting methods
4. **Log appropriately**: Different verbosity levels for different audiences

### Error Prevention

1. **Validate early**: Check inputs at component boundaries
2. **Provide clear documentation**: Reduce user errors
3. **Use type hints**: Help catch errors during development
4. **Test error paths**: Ensure error handling works correctly

## Advanced Features

### Custom Error Types

Create domain-specific errors:

```python
class CustomISAError(ISAError):
    def __init__(self, message, instruction_type=None, **kwargs):
        self.instruction_type = instruction_type
        super().__init__(message, **kwargs)
    
    def _format_message(self):
        msg = super()._format_message()
        if self.instruction_type:
            msg += f" (instruction type: {self.instruction_type})"
        return msg
```

### Error Recovery

Implement graceful degradation:

```python
def robust_assembly(nodes):
    reporter = ErrorReporter()
    assembled_nodes = []
    
    for node in nodes:
        try:
            result = assemble_node(node)
            assembled_nodes.append(result)
        except AssemblerError as e:
            reporter.add_error(e)
            # Continue with remaining nodes
    
    return assembled_nodes, reporter
```

### Performance Considerations

- Error objects are lightweight
- String formatting is deferred until needed
- Error collection has configurable limits
- Context information is optional to save memory

## Testing Error Handling

### Unit Tests

```python
def test_error_creation():
    location = ErrorLocation(10, 5, "test.s")
    error = ISAError("Test error", location, "Test suggestion")
    
    assert "Test error" in str(error)
    assert "line 10" in str(error)
    assert "Test suggestion" in str(error)

def test_error_reporter():
    reporter = ErrorReporter(max_errors=2)
    
    reporter.add_error(ISAError("Error 1"))
    reporter.add_error(ISAError("Error 2"))
    reporter.add_error(ISAError("Error 3"))  # Should be truncated
    
    assert len(reporter.get_errors()) == 3  # Includes truncation message
```

### Integration Tests

Test error handling across component boundaries to ensure consistent behavior and proper error propagation. 