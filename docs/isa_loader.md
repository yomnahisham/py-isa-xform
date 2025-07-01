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
- **Professional Quality**: Production-ready code suitable for educational and research use

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

### `ISALoader`

The main class responsible for loading and managing ISA definitions.

**Constructor:**
```python
def __init__(self)
```

**Key Methods:**

#### `load_isa(isa_name: str) -> ISADefinition`

Loads an ISA definition by name from built-in or local files.

**Parameters:**
- `isa_name`: Name of the ISA (e.g., "zx16", "simple_risc")

**Returns:**
- `ISADefinition`: Loaded ISA definition object

**Raises:**
- `ISALoadError`: If the ISA cannot be loaded

**Example:**
```python
from isa_xform.core.isa_loader import ISALoader

# Create loader
loader = ISALoader()

# Load ZX16 ISA
isa_def = loader.load_isa("zx16")
print(f"Loaded ISA: {isa_def.name}")
print(f"Version: {isa_def.version}")
print(f"Description: {isa_def.description}")
```

#### `load_isa_from_file(file_path: Union[str, Path]) -> ISADefinition`

Loads an ISA definition from a specific file path.

**Parameters:**
- `file_path`: Path to the ISA definition JSON file

**Returns:**
- `ISADefinition`: Loaded ISA definition object

**Raises:**
- `ISALoadError`: If the file cannot be loaded or is invalid

**Example:**
```python
# Load custom ISA from file
isa_def = loader.load_isa_from_file("custom_isa.json")
```

#### `list_available_isas() -> List[str]`

Lists all available ISA definitions.

**Returns:**
- `List[str]`: List of available ISA names

**Example:**
```python
# List available ISAs
available_isas = loader.list_available_isas()
print("Available ISAs:", available_isas)
# Output: ['zx16', 'simple_risc', 'riscv_rv32i', 'modular_example', 'crazy_isa']
```

### `ISADefinition`

Represents a complete instruction set architecture definition.

**Attributes:**
- `name`: The name of the ISA (string)
- `version`: ISA version (string)
- `description`: Human-readable description of the ISA (string)
- `word_size`: Size of a word in bits (integer)
- `instruction_size`: Size of instructions in bits (integer)
- `endianness`: Byte order ("little" or "big") (string)
- `registers`: Dictionary mapping register categories to lists of `Register` objects
- `instructions`: List of `Instruction` objects
- `assembly_syntax`: `AssemblySyntax` object defining syntax rules
- `address_space`: `AddressSpace` object defining memory layout

**Example:**
```python
# Access ISA properties
print(f"ISA: {isa_def.name}")
print(f"Version: {isa_def.version}")
print(f"Word size: {isa_def.word_size} bits")
print(f"Instruction size: {isa_def.instruction_size} bits")
print(f"Endianness: {isa_def.endianness}")
print(f"Instructions: {len(isa_def.instructions)}")
```

### `Instruction`

Represents a single instruction in the ISA.

**Attributes:**
- `mnemonic`: Instruction mnemonic (string)
- `format`: Instruction format (string, e.g., "R-type", "I-type")
- `description`: Human-readable instruction description (string)
- `syntax`: Assembly syntax string (e.g., "ADD rd, rs2")
- `semantics`: Instruction semantics description (string)
- `encoding`: Dictionary containing field-based encoding specification

**Example:**
```python
# Access ZX16 ADD instruction
add_instruction = next(instr for instr in isa_def.instructions if instr.mnemonic == "ADD")
print(f"Instruction: {add_instruction.mnemonic}")
print(f"Format: {add_instruction.format}")
print(f"Syntax: {add_instruction.syntax}")
print(f"Semantics: {add_instruction.semantics}")
print(f"Description: {add_instruction.description}")
```

### `Register`

Represents a processor register.

**Attributes:**
- `name`: Register name (string)
- `size`: Register size in bits (integer)
- `alias`: List of register aliases (List[string])
- `description`: Human-readable description (string)

**Example:**
```python
# Access ZX16 registers
for category, registers in isa_def.registers.items():
    print(f"Register category: {category}")
    for register in registers:
        print(f"  Register: {register.name}")
        print(f"    Size: {register.size} bits")
        print(f"    Aliases: {register.alias}")
        print(f"    Description: {register.description}")
```

### `AssemblySyntax`

Represents assembly syntax configuration.

**Attributes:**
- `comment_char`: Primary comment character (string)
- `comment_chars`: List of all comment characters (List[string])
- `label_suffix`: Label suffix character (string)
- `register_prefix`: Register prefix (string)
- `immediate_prefix`: Immediate prefix (string)
- `hex_prefix`: Hexadecimal prefix (string)
- `binary_prefix`: Binary prefix (string)
- `case_sensitive`: Whether syntax is case sensitive (boolean)
- `operand_separators`: List of operand separator characters (List[string])

**Example:**
```python
# Access assembly syntax
syntax = isa_def.assembly_syntax
print(f"Comment char: {syntax.comment_char}")
print(f"Register prefix: {syntax.register_prefix}")
print(f"Immediate prefix: {syntax.immediate_prefix}")
print(f"Case sensitive: {syntax.case_sensitive}")
```

### `AddressSpace`

Represents address space configuration.

**Attributes:**
- `default_code_start`: Default code section start address (integer)
- `default_data_start`: Default data section start address (integer)
- `default_stack_start`: Default stack start address (integer)
- `memory_layout`: Dictionary defining memory layout (Dict)
- `alignment_requirements`: Dictionary defining alignment requirements (Dict)

## ZX16 ISA Definition Example

### Complete ZX16 Definition Structure

```json
{
  "name": "ZX16",
  "version": "1.0",
  "description": "ZX16 16-bit RISC-V inspired ISA",
  "instruction_size": 16,
  "word_size": 16,
  "endianness": "little",
  "address_space": {
    "size": 65536,
    "default_code_start": 32
  },
  "registers": {
    "general_purpose": [
      {
        "name": "x0",
        "size": 16,
        "alias": ["t0"],
        "description": "Temporary (caller-saved)"
      },
      {
        "name": "x6",
        "size": 16,
        "alias": ["a0"],
        "description": "Argument 0/Return value"
      },
      {
        "name": "x7",
        "size": 16,
        "alias": ["a1"],
        "description": "Argument 1"
      }
    ]
  },
  "instructions": [
    {
      "mnemonic": "ADD",
      "format": "R-type",
      "description": "Add registers (two-operand)",
      "syntax": "ADD rd, rs2",
      "semantics": "rd = rd + rs2",
      "encoding": {
        "fields": [
          {"name": "funct4", "bits": "15:12", "value": "0000"},
          {"name": "rs2", "bits": "11:9", "type": "register"},
          {"name": "rd", "bits": "8:6", "type": "register"},
          {"name": "func3", "bits": "5:3", "value": "000"},
          {"name": "opcode", "bits": "2:0", "value": "000"}
        ]
      }
    }
  ],
  "assembly_syntax": {
    "comment_char": ";",
    "register_prefix": "",
    "immediate_prefix": "",
    "case_sensitive": false,
    "operand_separators": [",", " "]
  }
}
```

### Loading and Using ZX16

```python
from isa_xform.core.isa_loader import ISALoader

# Create loader
loader = ISALoader()

# Load ZX16 ISA
isa_def = loader.load_isa("zx16")

# Access ZX16 properties
print(f"ISA: {isa_def.name} v{isa_def.version}")
print(f"Description: {isa_def.description}")
print(f"Word size: {isa_def.word_size} bits")
print(f"Instruction size: {isa_def.instruction_size} bits")

# Access ZX16 registers
registers = isa_def.registers["general_purpose"]
print(f"Number of registers: {len(registers)}")
for reg in registers:
    print(f"  {reg.name} ({', '.join(reg.alias)}): {reg.description}")

# Access ZX16 instructions
print(f"Number of instructions: {len(isa_def.instructions)}")
for instr in isa_def.instructions[:5]:  # Show first 5 instructions
    print(f"  {instr.mnemonic}: {instr.description}")
```

## Error Handling

### Error Types

The ISA loader provides comprehensive error handling:

- **ISALoadError**: General ISA loading errors
- **ISAValidationError**: ISA definition validation errors
- **FileNotFoundError**: ISA definition file not found
- **JSONDecodeError**: Malformed JSON in ISA definition

### Error Context

All errors include:
- Detailed error messages with specific issues
- File path and line information where applicable
- Suggestions for resolution
- Validation context for complex errors

### Example Error Handling

```python
from isa_xform.core.isa_loader import ISALoader
from isa_xform.utils.error_handling import ISALoadError

loader = ISALoader()

try:
    # Load ISA definition
    isa_def = loader.load_isa("zx16")
    print(f"Successfully loaded {isa_def.name}")
except ISALoadError as e:
    print(f"Failed to load ISA: {e}")
except FileNotFoundError:
    print("ISA definition file not found")
```

## Built-in ISA Definitions

The project includes several built-in ISA definitions:

### ZX16
- **Description**: 16-bit RISC-V inspired instruction set
- **Features**: 8 registers, 16-bit instructions, comprehensive instruction set
- **Use Case**: Primary demonstration ISA with complete toolchain support

### Simple RISC
- **Description**: Basic RISC-style instruction set for educational purposes
- **Features**: Simple instruction formats, basic operations
- **Use Case**: Learning and educational demonstrations

### RISC-V RV32I
- **Description**: Base integer instruction set for RISC-V 32-bit processors
- **Features**: Standard RISC-V instruction set, 32-bit operations
- **Use Case**: RISC-V compatibility and reference implementation

### Modular Example
- **Description**: Demonstrates modular ISA design patterns
- **Features**: Modular instruction encoding, extensible design
- **Use Case**: Advanced ISA design examples

### Crazy ISA
- **Description**: Experimental instruction set for testing edge cases
- **Features**: Unusual instruction formats, complex encoding
- **Use Case**: Testing and validation of toolchain robustness

## Performance Considerations

### Caching

The ISA loader implements efficient caching:

```python
# ISA definitions are cached after first load
isa_def1 = loader.load_isa("zx16")  # Loads from file
isa_def2 = loader.load_isa("zx16")  # Loads from cache
assert isa_def1 is isa_def2  # Same object instance
```

### Memory Usage

- ISA definitions are loaded once and cached
- Efficient JSON parsing with minimal memory overhead
- Register and instruction lookups use optimized data structures

### Loading Performance

- Fast file I/O with error handling
- Efficient JSON parsing
- Optimized object creation and validation

## Integration with Other Components

### Assembler Integration

The ISA loader works seamlessly with the assembler:

```python
from isa_xform.core.assembler import Assembler

# Load ISA and create assembler
isa_def = loader.load_isa("zx16")
assembler = Assembler(isa_def)
```

### Parser Integration

The ISA loader provides ISA definitions for the parser:

```python
from isa_xform.core.parser import Parser

# Load ISA and create parser
isa_def = loader.load_isa("zx16")
parser = Parser(isa_def)
```

### Disassembler Integration

The ISA loader supports disassembler creation:

```python
from isa_xform.core.disassembler import Disassembler

# Load ISA and create disassembler
isa_def = loader.load_isa("zx16")
disassembler = Disassembler(isa_def)
```

## Best Practices

### ISA Definition Structure

Organize ISA definitions with clear structure:

```json
{
  "name": "CustomISA",
  "version": "1.0",
  "description": "Clear description of the ISA",
  "instruction_size": 16,
  "word_size": 16,
  "endianness": "little",
  "registers": {
    "general_purpose": [...]
  },
  "instructions": [...],
  "assembly_syntax": {...},
  "address_space": {...}
}
```

### Register Definitions

Define registers with clear aliases and descriptions:

```json
{
  "name": "x6",
  "size": 16,
  "alias": ["a0"],
  "description": "Argument 0/Return value"
}
```

### Instruction Definitions

Define instructions with complete information:

```json
{
  "mnemonic": "ADD",
  "format": "R-type",
  "description": "Add registers (two-operand)",
  "syntax": "ADD rd, rs2",
  "semantics": "rd = rd + rs2",
  "encoding": {
    "fields": [...]
  }
}
```

This ISA loader provides professional-grade ISA definition management with comprehensive validation, efficient caching, and seamless integration with other components, making it suitable for educational, research, and development applications. 