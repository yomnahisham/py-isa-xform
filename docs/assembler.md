# Assembler Documentation

The Assembler component converts assembly language source code into machine code. It supports two-pass assembly for forward reference resolution, pseudo-instruction expansion, and comprehensive validation based on the ISA definition.

## Overview

The assembler takes parsed Abstract Syntax Tree (AST) nodes from the parser and generates binary machine code. It handles instruction encoding, symbol resolution, directive processing, address management, and pseudo-instruction expansion.

## Key Features

- **Two-pass assembly**: Resolves forward references and computes final addresses
- **Single-pass assembly**: For simple cases without forward references
- **ISA-agnostic design**: Works with any custom ISA definition
- **Comprehensive error reporting**: Detailed error messages with location information
- **Symbol table integration**: Full symbol resolution and management
- **Directive support**: Handles standard and custom assembly directives
- **Pseudo-instruction expansion**: Automatic handling of high-level assembly constructs
- **Immediate validation**: Proper handling of immediate value constraints
- **Register validation**: Ensures only valid registers are used

## Core Classes

### Assembler

The main assembler class that orchestrates the assembly process.

```python
from isa_xform.core.assembler import Assembler
from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.symbol_table import SymbolTable

# Load ISA definition
loader = ISALoader()
isa_definition = loader.load_isa("zx16")

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
      {"name": "funct4", "bits": "15:12", "value": "0000"},
      {"name": "rs2", "bits": "11:9", "type": "register"},
      {"name": "rd", "bits": "8:6", "type": "register"},
      {"name": "func3", "bits": "5:3", "value": "000"},
      {"name": "opcode", "bits": "2:0", "value": "000"}
    ]
  }
}
```

### ZX16 Encoding Example

```json
{
  "mnemonic": "ADD",
  "format": "R-type",
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
```

## Operand Resolution

The assembler resolves different operand types based on the ISA definition:

### Register Operands

- Resolves register names to numeric indices
- Supports register aliases defined in the ISA
- Handles ISA-specific register prefixes
- Case-sensitive or case-insensitive based on ISA settings
- Validates that only valid registers are used

**ZX16 Register Example:**
```assembly
ADD a0, a1    # Uses register aliases: a0 -> x6, a1 -> x7
LI t1, 5      # Uses register alias: t1 -> x5
```

### Immediate Operands

- Parses decimal, hexadecimal, and binary numbers
- Validates immediate values fit within specified bit widths
- Handles signed and unsigned immediates
- Supports ISA-specific immediate prefixes
- Provides detailed error messages for immediate overflow

**ZX16 Immediate Validation:**
```assembly
LI a0, 10     # Valid: 10 fits in 7-bit signed range (-64 to 63)
LI a0, 100    # Error: 100 doesn't fit in 7-bit signed field
ADDI a0, -5   # Valid: -5 fits in 7-bit signed range
```

### Address Operands

- Resolves labels to memory addresses
- Handles forward references through two-pass assembly
- Supports relative and absolute addressing
- Validates addresses are within valid ranges

## Pseudo-Instruction Support

The assembler automatically expands pseudo-instructions into actual machine code:

### Built-in Pseudo-Instructions

#### Load Immediate (LI)
```assembly
LI a0, 10     # Expands to: ADDI a0, x0, 10
```

#### Clear Register (CLR)
```assembly
CLR a0        # Expands to: XOR a0, a0
```

#### Move Register (MV)
```assembly
MV a1, a0     # Expands to: ADD a1, x0; ADD a1, a0
```

### Custom Pseudo-Instructions

ISA definitions can include custom pseudo-instructions:

```json
{
  "pseudo_instructions": [
    {
      "mnemonic": "LI16",
      "description": "Load 16-bit immediate",
      "syntax": "LI16 rd, imm",
      "expansion": "LI rd, imm[7:0]; ORI rd, imm[15:8]"
    }
  ]
}
```

### Bit Field Extraction

Pseudo-instructions support bit field extraction in expansions:

```assembly
LI16 a0, 0x1234    # Expands to:
                   # LI a0, 0x34
                   # ORI a0, 0x12
```

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
- `.text`: Switches to text section
- `.data`: Switches to data section

### ZX16 Directive Example

```assembly
    .text
    .globl main

main:
    LI a0, 10
    ADD a0, a1
    ECALL 0x3FF

    .data
message:
    .asciiz "Hello, World!"
```

## Error Handling

The assembler provides comprehensive error reporting:

### Error Types

- **AssemblerError**: General assembly errors
- **ParseError**: Malformed assembly syntax
- **SymbolError**: Undefined or duplicate symbols
- **BitUtilsError**: Bit manipulation errors
- **ImmediateError**: Immediate value validation errors
- **RegisterError**: Invalid register usage

### Error Context

All errors include:
- Source file name and line/column numbers
- Context of the problematic code
- Suggestions for resolution where applicable
- Detailed error messages with specific constraints

### ZX16 Error Examples

```assembly
# Error: Unknown register
LI a2, 10     # Error: Unknown register: a2

# Error: Immediate too large
LI a0, 100    # Error: Immediate value 100 doesn't fit in 7-bit signed field

# Error: Invalid instruction
INVALID a0    # Error: Unknown instruction: INVALID
```

## ZX16 Assembly Example

### Complete Program
```assembly
# ZX16 Arithmetic Operations
    .text
    .globl main

main:
    # Load immediate values
    LI a0, 10          # a0 = 10
    LI a1, 5           # a1 = 5
    
    # Arithmetic operations
    ADD a0, a1         # a0 = a0 + a1 (10 + 5 = 15)
    SUB a0, a1         # a0 = a0 - a1 (15 - 5 = 10)
    ADDI a0, 20        # a0 = a0 + 20 (10 + 20 = 30)
    
    # Logical operations
    AND a0, a1         # a0 = a0 & a1
    OR a0, a1          # a0 = a0 | a1
    XOR a0, a1         # a0 = a0 ^ a1
    
    # Exit program
    ECALL 0x3FF        # Exit with code in a0
```

### Assembly Process
```bash
# Assemble the program
python3 -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin

# Verify with disassembly
python3 -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program_dis.s
```

## Performance Considerations

### Two-Pass Assembly

- First pass: Symbol collection and address calculation
- Second pass: Machine code generation
- Efficient for programs with forward references

### Memory Usage

- Processes instructions incrementally
- Symbol table grows with program complexity
- Efficient bit manipulation for instruction encoding

### Optimization Features

- Immediate value validation during assembly
- Register validation for early error detection
- Pseudo-instruction expansion optimization

## Integration with Other Components

### Parser Integration

The assembler works seamlessly with the parser:

```python
from isa_xform.core.parser import Parser

# Parse assembly source
parser = Parser(isa_def)
nodes = parser.parse(assembly_source)

# Assemble parsed nodes
assembler = Assembler(isa_def)
result = assembler.assemble(nodes)
```

### Symbol Table Integration

Advanced symbol management:

```python
# Use existing symbol table
symbol_table = SymbolTable()
symbol_table.add_symbol("main", 0x1000)

# Assemble with symbol table
assembler = Assembler(isa_def, symbol_table)
result = assembler.assemble(nodes)
```

### CLI Integration

Command-line interface support:

```bash
python3 -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin --verbose
```

## Best Practices

### Immediate Values

Always validate immediate values fit within ISA constraints:

```assembly
# Good: Use valid immediates
LI a0, 10     # Valid for ZX16 (7-bit signed: -64 to 63)

# Bad: Use invalid immediates
LI a0, 100    # Error: Too large for ZX16
```

### Register Usage

Use only valid registers defined in the ISA:

```assembly
# Good: Use valid ZX16 registers
ADD a0, a1    # Valid: a0 and a1 are defined

# Bad: Use undefined registers
ADD a2, a3    # Error: a2 and a3 not defined in ZX16
```

### Pseudo-Instructions

Use pseudo-instructions for cleaner code:

```assembly
# Good: Use pseudo-instructions
LI a0, 10     # Clear and readable
CLR a1        # Clear register

# Alternative: Direct instructions
ADDI a0, x0, 10   # More verbose
XOR a1, a1        # Less readable
```

This assembler provides professional-grade assembly capabilities with comprehensive validation, pseudo-instruction support, and detailed error reporting, making it suitable for educational, research, and development applications. 

## Binary Output Format

The assembler generates binary files with metadata headers by default, following industry best practices for robust toolchain interoperability.

### Default Headered Binary Format

By default, the assembler outputs a binary with an ISA-specific header that includes:

- **Magic Number**: `ISA\x01` (4 bytes) - identifies the file format
- **ISA Name Length**: 1 byte - length of the ISA name
- **ISA Name**: Variable length - name of the ISA used for assembly
- **Code Size**: 4 bytes (little-endian) - size of the machine code section
- **Entry Point**: 4 bytes (little-endian) - starting address for execution
- **Machine Code**: The actual assembled instructions and data

### Raw Binary Output

For special cases (bootloaders, legacy systems, etc.), you can output a raw binary without headers using the `--raw` flag:

```bash
# Output raw binary (no header)
python -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin --raw
```

### Header Format Example

```bash
# Default: headered binary
python -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin

# Hexdump shows header + machine code
hexdump -C program.bin
00000000  49 53 41 01 04 5a 58 31  36 08 00 00 00 20 00 00  |ISA..ZX16.... ..|
00000010  00 39 14 79 0a 00 02 87  02                       |.9.y.....|
#         ^^^^^^^^^^^^^^^^ header ^^^^^^^^^^^^ machine code ^
```

### Benefits of Headered Binaries

1. **Automatic Address Detection**: Disassemblers can automatically determine the correct starting address
2. **Tool Interoperability**: Debuggers, loaders, and other tools can work without manual configuration
3. **Robust Disassembly**: No need to specify `--start-address` when disassembling
4. **Industry Standard**: Follows the same patterns as ELF, PE, and other executable formats

### Command Line Options

```bash
python -m isa_xform.cli assemble [options] --isa <isa> --input <files> --output <file>

Options:
  --isa <name>           ISA definition name or file path
  --input <files>        Input assembly files (can specify multiple)
  --output <file>        Output binary file
  --verbose, -v          Enable verbose output
  --list-symbols         Display symbol table after assembly
  --raw                  Output raw binary without header (for bootloaders/legacy)
```

## Assembly Process

```bash
# Assemble the program
python3 -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin

# Verify with disassembly
python3 -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program_dis.s
``` 