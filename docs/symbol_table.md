# Symbol Table Documentation

## Overview

The `symbol_table` module is a critical component of the py-isa-xform toolkit that manages symbols, labels, constants, and memory references during the assembly process. This module provides the infrastructure for address resolution, forward reference handling, and symbol validation, enabling the creation of complex assembly programs with proper symbol management.

## Design Philosophy

The symbol table is designed with the following principles:

- **Completeness**: Track all symbols and their relationships in the assembly program
- **Efficiency**: Fast symbol lookup and resolution for large programs
- **Flexibility**: Support for different symbol types and scoping rules
- **Reliability**: Robust error detection and validation
- **Extensibility**: Easy addition of new symbol types and resolution strategies

## Architecture

### Symbol Management Flow

The symbol table follows a structured approach to symbol management:

```
Symbol Definition → Symbol Storage → Reference Resolution → Address Assignment
       ↓                ↓                ↓                    ↓
   Label/Constant    Symbol Table    Forward Reference    Final Address
   Declaration       Lookup          Tracking             Resolution
```

### Component Structure

1. **Symbol Storage**: Efficient storage and retrieval of symbol information
2. **Reference Tracking**: Management of forward and backward references
3. **Address Resolution**: Assignment of memory addresses to symbols
4. **Validation System**: Comprehensive error checking and validation
5. **Statistics Collection**: Usage statistics and reporting

## Core Classes

### `SymbolTable`

The main class for managing symbols and their relationships.

**Constructor:**
```python
def __init__(self)
```

**Key Methods:**

#### `add_symbol(name: str, value: int, symbol_type: str = "label") -> None`

Adds a symbol to the symbol table.

**Parameters:**
- `name`: Symbol name (string)
- `value`: Symbol value, typically a memory address (integer)
- `symbol_type`: Type of symbol ("label", "constant", "data") (default: "label")

**Raises:**
- `SymbolError`: If symbol already exists or validation fails

**Example:**
```python
from isa_xform.core.symbol_table import SymbolTable

symbol_table = SymbolTable()

# Add labels
symbol_table.add_symbol("main", 0x1000, "label")
symbol_table.add_symbol("start_loop", 0x1010, "label")

# Add constants
symbol_table.add_symbol("MAX_COUNT", 100, "constant")
symbol_table.add_symbol("BUFFER_SIZE", 1024, "constant")

# Add data symbols
symbol_table.add_symbol("data_buffer", 0x2000, "data")
```

#### `get_symbol(name: str) -> Optional[Symbol]`

Retrieves a symbol from the symbol table.

**Parameters:**
- `name`: Symbol name to look up

**Returns:**
- `Symbol`: Symbol object if found, None otherwise

**Example:**
```python
# Get symbol information
symbol = symbol_table.get_symbol("main")
if symbol:
    print(f"Symbol {symbol.name} = {symbol.value} ({symbol.symbol_type})")
```

#### `has_symbol(name: str) -> bool`

Checks if a symbol exists in the symbol table.

**Parameters:**
- `name`: Symbol name to check

**Returns:**
- `bool`: True if symbol exists, False otherwise

**Example:**
```python
# Check symbol existence
if symbol_table.has_symbol("undefined_label"):
    print("Symbol exists")
else:
    print("Symbol not found")
```

#### `resolve_symbols(nodes: List[ASTNode]) -> None`

Resolves forward references in a list of AST nodes.

**Parameters:**
- `nodes`: List of AST nodes to process

**Raises:**
- `SymbolError`: If unresolved symbols remain

**Example:**
```python
# Resolve symbols in parsed assembly
nodes = parser.parse(assembly_code)
symbol_table.resolve_symbols(nodes)
```

### `Symbol`

Represents a single symbol in the symbol table.

**Attributes:**
- `name`: Symbol name (string)
- `value`: Symbol value, typically a memory address (integer)
- `symbol_type`: Type of symbol ("label", "constant", "data")
- `defined`: Whether the symbol is fully defined (boolean)

**Example:**
```python
# Create symbol object
symbol = Symbol("main", 0x1000, "label", True)

# Access symbol properties
print(f"Name: {symbol.name}")
print(f"Value: 0x{symbol.value:X}")
print(f"Type: {symbol.symbol_type}")
print(f"Defined: {symbol.defined}")
```

## Symbol Types

### Labels

Labels represent memory addresses in the assembly program.

**Characteristics:**
- **Scope**: Global or local (depending on assembly syntax)
- **Value**: Memory address where the label is defined
- **Usage**: Referenced by instructions and other labels

**Example:**
```assembly
main:           # Label at address 0x1000
    add r1, r2, r3
    jmp loop    # Reference to loop label

loop:           # Label at address 0x1004
    sub r1, r1, #1
    jnz loop    # Self-reference
```

### Constants

Constants represent fixed values used throughout the program.

**Characteristics:**
- **Scope**: Global (accessible throughout the program)
- **Value**: Fixed numeric value
- **Usage**: Referenced by instructions and directives

**Example:**
```assembly
# Constants defined in symbol table
MAX_COUNT = 100
BUFFER_SIZE = 1024

# Usage in assembly
addi r1, r0, MAX_COUNT    # Load constant value
addi r2, r0, BUFFER_SIZE  # Load buffer size
```

### Data Symbols

Data symbols represent memory locations for data storage.

**Characteristics:**
- **Scope**: Global or local
- **Value**: Memory address where data is stored
- **Usage**: Referenced by load/store instructions

**Example:**
```assembly
.data
    counter: .word 0      # Data symbol at address 0x2000
    buffer: .space 1024   # Data symbol at address 0x2004

.text
    lw r1, counter        # Load from data symbol
    sw r2, buffer         # Store to data symbol
```

## Address Resolution

### Forward Reference Handling

The symbol table handles forward references through a two-pass approach:

1. **First Pass**: Collect all symbol definitions and their addresses
2. **Second Pass**: Resolve all forward references using collected addresses

**Example:**
```assembly
# First pass: Define labels
main:           # Address 0x1000
    jmp loop    # Forward reference to loop
    add r1, r2, r3

loop:           # Address 0x1004
    sub r1, r1, #1
    jnz loop    # Backward reference
```

### Address Assignment

Addresses are assigned based on the assembly process:

```python
# Address assignment example
current_address = 0x1000

for node in nodes:
    if isinstance(node, LabelNode):
        # Assign current address to label
        symbol_table.add_symbol(node.name, current_address, "label")
    elif isinstance(node, InstructionNode):
        # Increment address by instruction size
        current_address += instruction_size
    elif isinstance(node, DirectiveNode):
        # Handle data directives
        if node.name == ".word":
            current_address += 4  # 32-bit word
        elif node.name == ".byte":
            current_address += 1  # 8-bit byte
```

## Error Handling

### Error Types

The symbol table handles several types of errors:

1. **Duplicate Symbol Errors**: Multiple definitions of the same symbol
2. **Undefined Symbol Errors**: References to non-existent symbols
3. **Circular Reference Errors**: Circular dependencies between symbols
4. **Scope Errors**: Invalid symbol scope or visibility

### Error Reporting

Errors include detailed information:

```python
# Example error messages
SymbolError: Duplicate symbol definition 'main' at line 10
SymbolError: Undefined symbol 'undefined_label' referenced at line 15
SymbolError: Circular reference detected in symbol 'loop'
```

### Validation

The symbol table provides comprehensive validation:

```python
# Validate symbol table state
def validate_symbol_table(symbol_table):
    errors = []
    
    # Check for undefined symbols
    for symbol in symbol_table.symbols.values():
        if not symbol.defined:
            errors.append(f"Undefined symbol: {symbol.name}")
    
    # Check for duplicate symbols
    # Check for circular references
    # Check for invalid addresses
    
    return errors
```

## Performance Considerations

### Memory Efficiency

- **Hash-based lookup**: O(1) average case symbol lookup
- **Minimal object overhead**: Efficient symbol object representation
- **Lazy resolution**: Resolve references only when needed

### Processing Speed

- **Single-pass resolution**: Resolve references in one pass when possible
- **Caching**: Cache resolved addresses for repeated access
- **Early termination**: Stop processing on critical errors

## Usage Examples

### Basic Symbol Management

```python
from isa_xform.core.symbol_table import SymbolTable

# Create symbol table
symbol_table = SymbolTable()

# Add symbols
symbol_table.add_symbol("main", 0x1000, "label")
symbol_table.add_symbol("MAX_COUNT", 100, "constant")
symbol_table.add_symbol("data_buffer", 0x2000, "data")

# Check symbols
assert symbol_table.has_symbol("main")
assert symbol_table.get_symbol("MAX_COUNT").value == 100
```

### Assembly Integration

```python
# Integrate with parser and assembler
nodes = parser.parse(assembly_code)
symbol_table = SymbolTable()

# First pass: collect symbols
current_address = 0x1000
for node in nodes:
    if isinstance(node, LabelNode):
        symbol_table.add_symbol(node.name, current_address, "label")
    elif isinstance(node, InstructionNode):
        current_address += 4  # Assume 4-byte instructions
    elif isinstance(node, DirectiveNode):
        if node.name == ".word":
            current_address += 4

# Second pass: resolve references
symbol_table.resolve_symbols(nodes)
```

### Error Handling

```python
try:
    symbol_table.add_symbol("main", 0x1000, "label")
    symbol_table.add_symbol("main", 0x2000, "label")  # Duplicate!
except SymbolError as e:
    print(f"Symbol error: {e}")
```

## Integration with Other Components

### Parser Integration

The symbol table works closely with the parser:

```python
# Extract symbols from parsed AST
for node in nodes:
    if isinstance(node, LabelNode):
        symbol_table.add_symbol(node.name, current_address, "label")
    elif isinstance(node, DirectiveNode):
        if node.name == ".equ":
            # Handle constant definitions
            name, value = node.arguments[0], int(node.arguments[1])
            symbol_table.add_symbol(name, value, "constant")
```

### Assembler Integration

The symbol table provides address resolution for the assembler:

```python
# Resolve symbol references in instructions
for node in nodes:
    if isinstance(node, InstructionNode):
        for i, operand in enumerate(node.operands):
            if operand in symbol_table.symbols:
                # Replace symbol with address
                symbol = symbol_table.get_symbol(operand)
                node.operands[i] = str(symbol.value)
```

## Conclusion

The symbol table module provides a robust, efficient, and extensible foundation for symbol management in py-isa-xform. Its comprehensive feature set, including forward reference handling, address resolution, and error validation, makes it suitable for both simple educational programs and complex assembly applications.

The module's clean architecture and integration capabilities ensure seamless operation with other components while providing the flexibility needed for custom symbol types and resolution strategies. The comprehensive error handling and validation systems ensure reliable operation across a wide range of use cases. 