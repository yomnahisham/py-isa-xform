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

#### `define_symbol(name: str, value: Any, symbol_type: SymbolType = SymbolType.LABEL, scope: SymbolScope = SymbolScope.LOCAL, size: Optional[int] = None, line: Optional[int] = None, column: Optional[int] = None, file: Optional[str] = None) -> Symbol`

Defines a new symbol in the symbol table.

**Parameters:**
- `name`: Symbol name (string)
- `value`: Symbol value (address, constant, etc.)
- `symbol_type`: Type of symbol (SymbolType.LABEL, SymbolType.CONSTANT, etc.)
- `scope`: Symbol scope (SymbolScope.LOCAL, SymbolScope.GLOBAL, SymbolScope.EXTERNAL)
- `size`: Size in bytes (for variables)
- `line`: Line number where defined
- `column`: Column number where defined
- `file`: File where defined

**Returns:**
- `Symbol`: The defined symbol object

**Raises:**
- `SymbolError`: If symbol is already defined

**Example:**
```python
from isa_xform.core.symbol_table import SymbolTable, SymbolType, SymbolScope

symbol_table = SymbolTable()

# Define labels
symbol_table.define_symbol("main", 0x1000, SymbolType.LABEL, SymbolScope.GLOBAL, line=10)
symbol_table.define_symbol("start_loop", 0x1010, SymbolType.LABEL, SymbolScope.LOCAL, line=15)

# Define constants
symbol_table.define_symbol("MAX_COUNT", 100, SymbolType.CONSTANT, SymbolScope.GLOBAL, line=5)
symbol_table.define_symbol("BUFFER_SIZE", 1024, SymbolType.CONSTANT, SymbolScope.GLOBAL, line=6)

# Define data symbols
symbol_table.define_symbol("data_buffer", 0x2000, SymbolType.LABEL, SymbolScope.GLOBAL, size=1024, line=20)
```

#### `reference_symbol(name: str, address: int, line: Optional[int] = None, column: Optional[int] = None, file: Optional[str] = None) -> Symbol`

References a symbol (may be forward reference).

**Parameters:**
- `name`: Symbol name
- `address`: Address where symbol is referenced
- `line`: Line number of reference
- `column`: Column number of reference
- `file`: File of reference

**Returns:**
- `Symbol`: The referenced symbol object

**Raises:**
- `SymbolError`: If symbol cannot be resolved

**Example:**
```python
# Reference a symbol (may be forward reference)
symbol = symbol_table.reference_symbol("undefined_label", 0x1020, line=25)
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
    print(f"Symbol {symbol.name} = {symbol.value} ({symbol.type.value})")
    print(f"Defined: {symbol.defined}")
    print(f"Referenced: {symbol.referenced}")
```

#### `resolve_symbol(name: str) -> Optional[Any]`

Resolves a symbol to its value.

**Parameters:**
- `name`: Symbol name

**Returns:**
- Symbol value if found and defined, None otherwise

**Example:**
```python
# Resolve symbol value
value = symbol_table.resolve_symbol("MAX_COUNT")
if value is not None:
    print(f"MAX_COUNT = {value}")
```

#### `define_label(name: str, line: Optional[int] = None, column: Optional[int] = None, file: Optional[str] = None) -> Symbol`

Defines a label at the current address.

**Parameters:**
- `name`: Label name
- `line`: Line number where defined
- `column`: Column number where defined
- `file`: File where defined

**Returns:**
- `Symbol`: The defined label symbol

**Example:**
```python
# Define a label at current address
symbol_table.set_current_address(0x1000)
label = symbol_table.define_label("main", line=10)
print(f"Label {label.name} at address 0x{label.value:X}")
```

#### `define_constant(name: str, value: Any, line: Optional[int] = None, column: Optional[int] = None, file: Optional[str] = None) -> Symbol`

Defines a constant symbol.

**Parameters:**
- `name`: Constant name
- `value`: Constant value
- `line`: Line number where defined
- `column`: Column number where defined
- `file`: File where defined

**Returns:**
- `Symbol`: The defined constant symbol

**Example:**
```python
# Define constants
const = symbol_table.define_constant("PI", 3.14159, line=5)
const2 = symbol_table.define_constant("MAX_SIZE", 1024, line=6)
```

#### `reset()`

Resets the symbol table for a new pass.

**Example:**
```python
# Reset for second pass
symbol_table.reset()
```

#### `validate() -> List[str]`

Validates the symbol table and returns any errors.

**Returns:**
- List of error messages

**Example:**
```python
# Validate symbol table
errors = symbol_table.validate()
if errors:
    print("Symbol table errors:")
    for error in errors:
        print(f"  - {error}")
```

#### `get_statistics() -> Dict[str, int]`

Gets statistics about the symbol table.

**Returns:**
- Dictionary with statistics

**Example:**
```python
# Get statistics
stats = symbol_table.get_statistics()
print(f"Total symbols: {stats['total_symbols']}")
print(f"Defined symbols: {stats['defined_symbols']}")
print(f"Undefined symbols: {stats['undefined_symbols']}")
```

### `Symbol`

Represents a single symbol in the symbol table.

**Attributes:**
- `name`: Symbol name (string)
- `type`: Type of symbol (SymbolType enum)
- `scope`: Symbol scope (SymbolScope enum)
- `value`: Symbol value (Any)
- `size`: Size in bytes (Optional[int])
- `line`: Line number where defined (Optional[int])
- `column`: Column number where defined (Optional[int])
- `file`: File where defined (Optional[str])
- `defined`: Whether the symbol is fully defined (bool)
- `referenced`: Whether the symbol has been referenced (bool)
- `forward_references`: List of addresses where symbol is forward referenced (List[int])

**Example:**
```python
# Create symbol object
symbol = Symbol(
    name="main",
    type=SymbolType.LABEL,
    scope=SymbolScope.GLOBAL,
    value=0x1000,
    line=10,
    defined=True
)

# Access symbol properties
print(f"Name: {symbol.name}")
print(f"Type: {symbol.type.value}")
print(f"Scope: {symbol.scope.value}")
print(f"Value: 0x{symbol.value:X}")
print(f"Defined: {symbol.defined}")
print(f"Referenced: {symbol.referenced}")
```

### `SymbolType` Enum

Defines the types of symbols:

- `LABEL`: Memory address labels
- `CONSTANT`: Fixed value constants
- `REGISTER`: Register references
- `EXTERNAL`: External symbols
- `LOCAL`: Local scope symbols
- `GLOBAL`: Global scope symbols

### `SymbolScope` Enum

Defines the scoping of symbols:

- `LOCAL`: Local scope (function/block level)
- `GLOBAL`: Global scope (file level)
- `EXTERNAL`: External scope (linker level)

## Symbol Types

### Labels

Labels represent memory addresses in the assembly program.

**Characteristics:**
- **Type**: `SymbolType.LABEL`
- **Scope**: Usually `SymbolScope.GLOBAL` or `SymbolScope.LOCAL`
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
- **Type**: `SymbolType.CONSTANT`
- **Scope**: Usually `SymbolScope.GLOBAL`
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

### External Symbols

External symbols represent symbols defined in other modules.

**Characteristics:**
- **Type**: `SymbolType.EXTERNAL`
- **Scope**: `SymbolScope.EXTERNAL`
- **Value**: Usually None (resolved by linker)
- **Usage**: Referenced across multiple files

**Example:**
```assembly
# External symbol declaration
.extern printf
.extern malloc

# Usage
call printf    # Call external function
call malloc    # Call external function
```

## Forward Reference Handling

The symbol table supports forward references, allowing symbols to be used before they are defined.

### Forward Reference Process

1. **First Pass**: Collect all symbol definitions and note forward references
2. **Second Pass**: Resolve all forward references with final addresses

**Example:**
```python
# First pass - forward reference
symbol_table.set_current_address(0x1000)
symbol = symbol_table.reference_symbol("loop", 0x1000)  # Forward reference
symbol_table.advance_address(2)

# Later in first pass - symbol definition
symbol_table.set_current_address(0x1004)
symbol_table.define_label("loop")  # Now defined

# Second pass - resolve forward references
symbol_table.reset()
symbol_table.resolve_forward_references()
```

## Error Handling

The symbol table provides comprehensive error detection:

### Common Errors

1. **Duplicate Definition**: Symbol defined multiple times
2. **Undefined Symbol**: Symbol referenced but never defined
3. **Invalid Scope**: Symbol used outside its scope
4. **Type Mismatch**: Symbol used with wrong type

### Error Reporting

```python
# Check for errors
errors = symbol_table.validate()
if errors:
    print("Symbol table errors:")
    for error in errors:
        print(f"  - {error}")

# Get undefined symbols
undefined = symbol_table.get_undefined_symbols()
if undefined:
    print("Undefined symbols:")
    for symbol in undefined:
        print(f"  - {symbol.name}")

# Get unreferenced symbols
unreferenced = symbol_table.get_unreferenced_symbols()
if unreferenced:
    print("Unreferenced symbols:")
    for symbol in unreferenced:
        print(f"  - {symbol.name}")
```

## Integration with Assembler

The symbol table integrates seamlessly with the assembler:

```python
from isa_xform.core.symbol_table import SymbolTable
from isa_xform.core.assembler import Assembler

# Create symbol table and assembler
symbol_table = SymbolTable()
assembler = Assembler(isa_definition, symbol_table)

# Assemble code with symbol resolution
machine_code = assembler.assemble(assembly_code)
```

## Best Practices

1. **Define Before Use**: Define symbols before referencing them when possible
2. **Use Descriptive Names**: Use clear, descriptive symbol names
3. **Check for Errors**: Always validate the symbol table after assembly
4. **Handle Forward References**: Be aware of forward reference limitations
5. **Use Appropriate Scopes**: Use the correct scope for each symbol type

## Performance Considerations

1. **Symbol Lookup**: O(1) average case for symbol lookups
2. **Memory Usage**: Efficient storage with minimal overhead
3. **Validation**: Fast validation with early error detection
4. **Forward References**: Efficient tracking and resolution 