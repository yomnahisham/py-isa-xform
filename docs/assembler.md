# Assembler Documentation

The Assembler component converts assembly language source code into machine code. It supports two-pass assembly for forward reference resolution and is fully configurable based on the ISA definition.

## Overview

The assembler takes parsed Abstract Syntax Tree (AST) nodes from the parser and generates binary machine code. It handles instruction encoding, symbol resolution, directive processing, and address management.

## Key Features

- **Two-pass assembly**: Resolves forward references and computes final addresses
- **Single-pass assembly**: For simple cases without forward references
- **ISA-agnostic design**: Works with any custom ISA definition
- **Comprehensive error reporting**: Detailed error messages with location information
- **Symbol table integration**: Full symbol resolution and management
- **Directive support**: Handles standard and custom assembly directives

## Core Classes

### Assembler

The main assembler class that orchestrates the assembly process.

```python
from isa_xform.core.assembler import Assembler
from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.symbol_table import SymbolTable

# Load ISA definition
loader = ISALoader()
isa_definition = loader.load_isa("simple_risc")

# Create assembler with symbol table
symbol_table = SymbolTable()
assembler = Assembler(isa_definition, symbol_table)

# Assemble AST nodes
result = assembler.assemble(nodes, two_pass=True)
```

#### Constructor Parameters

- `isa_definition`: ISADefinition object containing the target architecture specification
- `symbol_table`: Optional SymbolTable instance (creates new one if not provided)

#### Methods

##### `assemble(nodes, two_pass=True)`

Assembles a list of AST nodes into machine code.

**Parameters:**
- `nodes`: List of ASTNode objects from the parser
- `two_pass`: Boolean indicating whether to use two-pass assembly (default: True)

**Returns:**
- `AssembledCode` object containing machine code and symbol table

##### `_first_pass(nodes)`

First pass: collects symbols and calculates addresses.

**Parameters:**
- `nodes`: List of AST nodes to process

##### `_second_pass(nodes)`

Second pass: generates actual machine code.

**Parameters:**
- `nodes`: List of AST nodes to process

**Returns:**
- `bytearray` containing the generated machine code

### AssemblyContext

Maintains state during the assembly process.

**Attributes:**
- `current_address`: Current memory address being assembled
- `current_section`: Current section name (e.g., "text", "data")
- `pass_number`: Current assembly pass (1 or 2)
- `origin_set`: Whether .org directive has been used
- `symbols_defined`: Dictionary of defined symbols

### AssembledCode

Result object containing the assembled output.

**Attributes:**
- `machine_code`: bytearray containing the binary machine code
- `symbol_table`: SymbolTable with all resolved symbols
- `entry_point`: Optional entry point address
- `sections`: Optional dictionary mapping section names to (start_addr, size) tuples

## Instruction Encoding

The assembler supports flexible instruction encoding based on the ISA definition:

### Field-Based Encoding

Modern ISA definitions use field-based encoding:

```json
{
  "encoding": {
    "fields": [
      {"name": "opcode", "bits": "31:28", "value": "1010"},
      {"name": "rd", "bits": "27:24", "type": "register"},
      {"name": "rs1", "bits": "23:20", "type": "register"},
      {"name": "immediate", "bits": "19:0", "type": "immediate", "signed": true}
    ]
  }
}
```

### Legacy Encoding

Simple opcode-based encoding for compatibility:

```json
{
  "opcode": "1010",
  "format": "R-type"
}
```

## Operand Resolution

The assembler resolves different operand types based on the ISA definition:

### Register Operands

- Resolves register names to numeric indices
- Supports register aliases defined in the ISA
- Handles ISA-specific register prefixes
- Case-sensitive or case-insensitive based on ISA settings

### Immediate Operands

- Parses decimal, hexadecimal, and binary numbers
- Validates immediate values fit within specified bit widths
- Handles signed and unsigned immediates
- Supports ISA-specific immediate prefixes

### Address Operands

- Resolves labels to memory addresses
- Handles forward references through two-pass assembly
- Supports relative and absolute addressing
- Validates addresses are within valid ranges

## Directive Processing

The assembler handles standard assembly directives:

### Memory Directives

- `.org address`: Sets the origin address
- `.word value1, value2, ...`: Defines word-sized data
- `.byte value1, value2, ...`: Defines byte-sized data
- `.space size`: Reserves space with zero fill
- `.align boundary`: Aligns to specified boundary

### String Directives

- `.ascii "string"`: Defines ASCII string without null terminator
- `.asciiz "string"`: Defines ASCII string with null terminator

### Symbol Directives

- `.global symbol`: Marks symbol as global
- `.equ symbol, value`: Defines symbolic constant

### Section Directives

- `.section name`: Switches to named section

### Custom Directives

The assembler supports ISA-specific custom directives defined in the ISA specification.

## Error Handling

The assembler provides comprehensive error reporting:

### Error Types

- **AssemblerError**: General assembly errors
- **ParseError**: Malformed assembly syntax
- **SymbolError**: Undefined or duplicate symbols
- **BitUtilsError**: Bit manipulation errors

### Error Context

All errors include:
- Source file name and line/column numbers
- Context of the problematic code
- Suggestions for resolution where applicable
- Related symbol information

### Example Error Output

```
Error: Immediate value 256 doesn't fit in 8-bit unsigned field at line 15, column 20 in main.s
  Context: LDI $r1, #256
  Suggestion: Use a value between 0 and 255, or use a different instruction
```

## Configuration

The assembler adapts to ISA-specific configurations:

### Assembly Syntax

- Comment characters
- Label suffixes
- Register and immediate prefixes
- Number format prefixes
- Case sensitivity

### Instruction Formats

- Variable instruction sizes
- Different encoding schemes
- Custom operand types
- ISA-specific addressing modes

### Memory Layout

- Configurable default addresses
- Section-specific memory regions
- Alignment requirements
- Endianness handling

## Usage Examples

### Basic Assembly

```python
from isa_xform.core.assembler import Assembler
from isa_xform.core.parser import Parser
from isa_xform.core.isa_loader import ISALoader

# Load ISA and create components
loader = ISALoader()
isa_def = loader.load_isa("simple_risc")
parser = Parser(isa_def)
assembler = Assembler(isa_def)

# Parse and assemble
source_code = """
start:
    ADD $r1, $r2, $r3
    JMP end
end:
    NOP
"""

nodes = parser.parse(source_code)
result = assembler.assemble(nodes)

# Access results
machine_code = result.machine_code
symbols = result.symbol_table.symbols
```

### Custom ISA Assembly

```python
# Load custom ISA with different syntax
custom_isa = loader.load_isa_from_file("custom_isa.json")
assembler = Assembler(custom_isa)

# Assembly code using custom syntax
custom_source = """
# Custom ISA with % register prefix and @ immediate prefix
main:
    LOAD %R1, @42
    STORE %R1, offset(%R2)
"""

nodes = parser.parse(custom_source)
result = assembler.assemble(nodes)
```

### Error Handling

```python
from isa_xform.utils.error_handling import ErrorReporter, AssemblerError

error_reporter = ErrorReporter()

try:
    result = assembler.assemble(nodes)
except AssemblerError as e:
    error_reporter.add_error(e)
    print(error_reporter.format_errors())
```

## Performance Considerations

### Two-Pass vs Single-Pass

- **Two-pass**: Required for forward references, slower but more flexible
- **Single-pass**: Faster for simple code without forward references

### Memory Usage

- Symbol table size grows with number of symbols
- Machine code buffer size depends on program size
- AST nodes are processed sequentially to minimize memory usage

### Optimization Tips

- Use single-pass assembly when possible
- Pre-sort symbols to improve lookup performance
- Use appropriate data structures for large programs

## Integration

The assembler integrates with other components:

- **Parser**: Consumes AST nodes from the parser
- **ISA Loader**: Uses ISA definitions for instruction encoding
- **Symbol Table**: Manages symbol resolution and storage
- **Error Handling**: Provides detailed error reporting
- **Bit Utils**: Uses bit manipulation utilities for encoding

## Extensibility

The assembler is designed for extensibility:

### Custom Directives

Add support for new directives by extending the directive handler mapping:

```python
assembler.directive_handlers['.custom'] = custom_directive_handler
```

### Custom Instruction Formats

Support new instruction formats by extending the encoding logic:

```python
def custom_encoding_handler(instruction, operands):
    # Custom encoding logic
    return encoded_instruction
```

### Custom Operand Types

Add support for new operand types by extending operand resolution:

```python
def resolve_custom_operand(operand, field_type, bit_width):
    # Custom operand resolution logic
    return resolved_value
``` 