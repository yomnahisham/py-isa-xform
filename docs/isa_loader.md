# ISA Loader Documentation

## Overview

The `isa_loader` module is a fundamental component of the py-isa-xform toolkit responsible for loading, parsing, and validating Instruction Set Architecture (ISA) definitions. This module provides a unified interface for working with both built-in and user-supplied ISA definition files, supporting a flexible JSON-based specification format that enables the creation of custom instruction set architectures.

## Design Philosophy

The ISA loader is designed with the following principles:

- **Flexibility**: Support for any instruction set architecture through declarative JSON specifications
- **Validation**: Comprehensive validation of ISA definitions for correctness and completeness
- **Performance**: Efficient loading and caching of ISA definitions
- **Extensibility**: Easy addition of new ISA features and validation rules
- **Reliability**: Robust error handling and detailed error reporting

## Architecture

### Loading Pipeline

The ISA loader follows a structured pipeline for processing ISA definitions:

```
JSON File → JSON Parser → Structure Validation → ISA Definition Object → Caching
     ↓           ↓              ↓                      ↓                    ↓
  Raw JSON   Parsed Data    Rule Checking         Validated ISA        Available
  Input      Structure      & Validation          Object               for Use
```

### Component Structure

1. **File Loader**: Handles file I/O and JSON parsing
2. **Structure Validator**: Validates JSON structure and required fields
3. **Content Validator**: Validates ISA content and relationships
4. **Object Builder**: Creates ISA definition objects from validated data
5. **Cache Manager**: Manages loaded ISA definitions for performance

## Core Classes

### `ISADefinition`

Represents a complete instruction set architecture definition.

**Attributes:**
- `name`: The name of the ISA (string)
- `description`: Human-readable description of the ISA (string)
- `word_size`: Size of a word in bits (integer)
- `endianness`: Byte order ("little" or "big") (string)
- `instructions`: Dictionary mapping instruction names to `Instruction` objects
- `registers`: Dictionary mapping register names to `Register` objects
- `addressing_modes`: Dictionary mapping mode names to `AddressingMode` objects

**Example:**
```python
from isa_xform.core.isa_loader import load_isa_definition

# Load ISA definition
isa_def = load_isa_definition("simple_risc.json")

# Access ISA properties
print(f"ISA: {isa_def.name}")
print(f"Word size: {isa_def.word_size} bits")
print(f"Endianness: {isa_def.endianness}")
print(f"Instructions: {len(isa_def.instructions)}")
print(f"Registers: {len(isa_def.registers)}")
```

### `Instruction`

Represents a single instruction in the ISA.

**Attributes:**
- `name`: Instruction mnemonic (string)
- `opcode`: Numeric opcode value (integer)
- `format`: Instruction format identifier (string)
- `operands`: List of operand specifications (`Operand` objects)
- `encoding`: Bit field encoding specification (dictionary)
- `description`: Human-readable instruction description (string)

**Example:**
```python
# Access instruction information
add_instruction = isa_def.instructions["add"]
print(f"Instruction: {add_instruction.name}")
print(f"Opcode: {add_instruction.opcode}")
print(f"Format: {add_instruction.format}")
print(f"Operands: {len(add_instruction.operands)}")
print(f"Description: {add_instruction.description}")
```

### `Operand`

Represents an instruction operand.

**Attributes:**
- `name`: Operand name (string)
- `type`: Operand type ("register", "immediate", "address") (string)
- `bits`: Number of bits allocated to this operand (integer)
- `position`: Bit position in the instruction (integer)
- `addressing_mode`: Associated addressing mode (string)

**Example:**
```python
# Access operand information
for operand in add_instruction.operands:
    print(f"Operand: {operand.name}")
    print(f"  Type: {operand.type}")
    print(f"  Bits: {operand.bits}")
    print(f"  Position: {operand.position}")
    print(f"  Addressing mode: {operand.addressing_mode}")
```

### `Register`

Represents a processor register.

**Attributes:**
- `name`: Register name (string)
- `bits`: Register size in bits (integer)
- `description`: Human-readable description (string)

**Example:**
```python
# Access register information
for reg_name, register in isa_def.registers.items():
    print(f"Register: {reg_name}")
    print(f"  Size: {register.bits} bits")
    print(f"  Description: {register.description}")
```

### `AddressingMode`

Represents an addressing mode.

**Attributes:**
- `name`: Addressing mode name (string)
- `description`: Human-readable description (string)
- `format`: Format specification (string)

**Example:**
```python
# Access addressing mode information
for mode_name, mode in isa_def.addressing_modes.items():
    print(f"Addressing mode: {mode_name}")
    print(f"  Description: {mode.description}")
    print(f"  Format: {mode.format}")
```

## Core Functions

### `load_isa_definition(file_path: str) -> ISADefinition`

Loads an ISA definition from a JSON file.

**Parameters:**
- `file_path`: Path to the JSON file containing the ISA definition

**Returns:**
- `ISADefinition`: Loaded ISA definition object

**Raises:**
- `FileNotFoundError`: If the specified file does not exist
- `JSONDecodeError`: If the JSON file is malformed
- `ValidationError`: If the ISA definition is invalid

**Example:**
```python
from isa_xform.core.isa_loader import load_isa_definition

try:
    # Load ISA definition
    isa_def = load_isa_definition("my_custom_isa.json")
    print(f"Successfully loaded ISA: {isa_def.name}")
except FileNotFoundError:
    print("ISA definition file not found")
except ValidationError as e:
    print(f"ISA validation failed: {e}")
```

### `validate_isa_definition(isa_def: ISADefinition) -> bool`

Validates an ISA definition for completeness and correctness.

**Parameters:**
- `isa_def`: The ISA definition to validate

**Returns:**
- `bool`: True if valid, False otherwise

**Raises:**
- `ValidationError`: If validation fails with detailed error information

**Example:**
```python
from isa_xform.core.isa_loader import validate_isa_definition

try:
    is_valid = validate_isa_definition(isa_def)
    if is_valid:
        print("ISA definition is valid")
    else:
        print("ISA definition has validation issues")
except ValidationError as e:
    print(f"Validation error: {e}")
```

## ISA Definition Format

### JSON Structure

ISA definitions use a structured JSON format:

```json
{
    "name": "SimpleRISC",
    "description": "A simple RISC-style instruction set for educational purposes",
    "word_size": 32,
    "endianness": "little",
    "registers": {
        "r0": {
            "name": "r0",
            "bits": 32,
            "description": "Zero register (always contains 0)"
        },
        "r1": {
            "name": "r1",
            "bits": 32,
            "description": "General purpose register 1"
        }
    },
    "instructions": {
        "add": {
            "name": "add",
            "opcode": 0,
            "format": "R",
            "operands": [
                {
                    "name": "rd",
                    "type": "register",
                    "bits": 4,
                    "position": 0,
                    "addressing_mode": "register"
                },
                {
                    "name": "rs1",
                    "type": "register",
                    "bits": 4,
                    "position": 4,
                    "addressing_mode": "register"
                },
                {
                    "name": "rs2",
                    "type": "register",
                    "bits": 4,
                    "position": 8,
                    "addressing_mode": "register"
                }
            ],
            "encoding": {
                "opcode": 0,
                "funct": 0
            },
            "description": "Add two registers and store result in destination register"
        }
    },
    "addressing_modes": {
        "register": {
            "name": "register",
            "description": "Register addressing mode",
            "format": "R"
        },
        "immediate": {
            "name": "immediate",
            "description": "Immediate addressing mode",
            "format": "I"
        }
    }
}
```

### Required Fields

The following fields are required in an ISA definition:

- **name**: Unique identifier for the ISA
- **word_size**: Size of a word in bits (typically 16, 32, or 64)
- **endianness**: Byte order ("little" or "big")
- **registers**: Dictionary of register definitions
- **instructions**: Dictionary of instruction definitions
- **addressing_modes**: Dictionary of addressing mode definitions

### Optional Fields

- **description**: Human-readable description of the ISA
- **version**: Version information for the ISA definition
- **author**: Author or organization that created the ISA
- **license**: License information for the ISA definition

## Validation Rules

### Structure Validation

The loader validates the JSON structure:

1. **Required Fields**: All required fields must be present
2. **Data Types**: Fields must have the correct data types
3. **Nested Structure**: Nested objects must have the correct structure
4. **Array Contents**: Arrays must contain valid objects

### Content Validation

The loader validates ISA content:

1. **Register Validation**:
   - Register names must be unique
   - Register sizes must be positive integers
   - Register sizes must not exceed word size

2. **Instruction Validation**:
   - Instruction names must be unique
   - Opcodes must be non-negative integers
   - Operand counts must match instruction definitions
   - Operand types must be valid

3. **Addressing Mode Validation**:
   - Addressing mode names must be unique
   - Referenced addressing modes must exist

4. **Encoding Validation**:
   - Bit field positions must not overlap
   - Total bit usage must not exceed instruction size
   - Encoding values must be within valid ranges

## Error Handling

### Error Types

The ISA loader handles several types of errors:

1. **File Errors**: Missing files, permission issues, or invalid file formats
2. **JSON Errors**: Malformed JSON syntax or structure
3. **Validation Errors**: Invalid ISA content or relationships
4. **System Errors**: Memory or resource limitations

### Error Reporting

Errors include detailed information:

```python
# Example error messages
ValidationError: Missing required field 'instructions' in ISA definition
ValidationError: Invalid opcode value in instruction 'add': must be non-negative
ValidationError: Duplicate register name 'r1' in register definitions
ValidationError: Unknown addressing mode 'invalid_mode' referenced in instruction 'add'
```

### Error Recovery

The loader implements graceful error recovery:

- **Partial Loading**: Load valid portions of ISA definitions when possible
- **Error Collection**: Collect multiple errors for comprehensive reporting
- **Default Values**: Use sensible defaults for optional fields when appropriate

## Performance Considerations

### Caching

The ISA loader implements caching for performance:

```python
# ISA definitions are cached after loading
isa_def1 = load_isa_definition("simple_risc.json")  # Load from file
isa_def2 = load_isa_definition("simple_risc.json")  # Load from cache
assert isa_def1 is isa_def2  # Same object instance
```

### Memory Efficiency

- **Lazy Loading**: Load ISA definitions only when needed
- **Object Reuse**: Reuse objects where possible
- **Efficient Storage**: Use memory-efficient data structures

### Processing Speed

- **Early Validation**: Validate critical fields early in the process
- **Optimized Parsing**: Use efficient JSON parsing libraries
- **Parallel Processing**: Support for parallel validation of large ISAs

## Usage Examples

### Basic ISA Loading

```python
from isa_xform.core.isa_loader import load_isa_definition

# Load built-in ISA
isa_def = load_isa_definition("simple_risc.json")

# Access ISA information
print(f"ISA Name: {isa_def.name}")
print(f"Word Size: {isa_def.word_size} bits")
print(f"Endianness: {isa_def.endianness}")
print(f"Number of Instructions: {len(isa_def.instructions)}")
print(f"Number of Registers: {len(isa_def.registers)}")
```

### Instruction Analysis

```python
# Analyze instructions
for inst_name, instruction in isa_def.instructions.items():
    print(f"\nInstruction: {inst_name}")
    print(f"  Opcode: {instruction.opcode}")
    print(f"  Format: {instruction.format}")
    print(f"  Description: {instruction.description}")
    
    print("  Operands:")
    for operand in instruction.operands:
        print(f"    {operand.name}: {operand.type} ({operand.bits} bits)")
```

### Register Analysis

```python
# Analyze registers
print("Registers:")
for reg_name, register in isa_def.registers.items():
    print(f"  {reg_name}: {register.bits} bits - {register.description}")
```

### Custom ISA Creation

```python
# Create a custom ISA definition
custom_isa = {
    "name": "MyCustomISA",
    "description": "A custom instruction set for my project",
    "word_size": 16,
    "endianness": "little",
    "registers": {
        "r0": {"name": "r0", "bits": 16, "description": "General purpose register 0"},
        "r1": {"name": "r1", "bits": 16, "description": "General purpose register 1"}
    },
    "instructions": {
        "add": {
            "name": "add",
            "opcode": 0,
            "format": "R",
            "operands": [
                {"name": "rd", "type": "register", "bits": 3, "position": 0, "addressing_mode": "register"},
                {"name": "rs", "type": "register", "bits": 3, "position": 3, "addressing_mode": "register"}
            ],
            "encoding": {"opcode": 0},
            "description": "Add two registers"
        }
    },
    "addressing_modes": {
        "register": {"name": "register", "description": "Register addressing", "format": "R"}
    }
}

# Save to file and load
import json
with open("my_custom_isa.json", "w") as f:
    json.dump(custom_isa, f, indent=2)

# Load the custom ISA
loaded_isa = load_isa_definition("my_custom_isa.json")
```

## Conclusion

The ISA loader module provides a robust, flexible, and efficient foundation for working with instruction set architecture definitions in py-isa-xform. Its comprehensive validation, error handling, and extensible design make it suitable for both educational use and professional development workflows.

The module's clean architecture and integration capabilities ensure seamless operation with other components while providing the flexibility needed for custom ISA features and validation rules. The comprehensive error handling and validation systems ensure reliable operation across a wide range of use cases. 