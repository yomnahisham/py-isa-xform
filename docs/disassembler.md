# Disassembler Documentation

The Disassembler component converts machine code back into human-readable assembly language. It supports various instruction formats, handles data sections, and provides configurable output formatting with correct operand ordering.

## Overview

The disassembler takes binary machine code and reconstructs assembly language instructions based on the ISA definition. It can differentiate between code and data sections, handle different instruction encodings, and generate formatted assembly output with operands in the correct syntax order.

## Key Features

- **ISA-agnostic design**: Works with any custom ISA definition
- **Pattern matching**: Flexible instruction recognition using opcode patterns and masks
- **Data section detection**: Automatically identifies non-instruction data
- **Symbol extraction**: Attempts to identify and name jump targets and data references
- **Configurable output**: Various formatting options for disassembled code
- **Error resilience**: Gracefully handles invalid or corrupted machine code
- **Correct operand ordering**: Outputs operands in syntax order, not encoding order
- **Professional output**: Clean, readable assembly code generation

## Core Classes

### Disassembler

The main disassembler class that handles machine code analysis and conversion.

```python
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.isa_loader import ISALoader

# Load ISA definition
loader = ISALoader()
isa_definition = loader.load_isa("zx16")

# Create disassembler with custom configuration
disassembler = Disassembler(isa_definition, max_consecutive_nops=16)

# Disassemble machine code
with open("program.bin", "rb") as f:
    machine_code = f.read()

result = disassembler.disassemble(machine_code, start_address=0x1000)
```

#### Constructor Parameters

- `isa_definition`: ISADefinition object containing the target architecture specification
- `symbol_table`: Optional SymbolTable instance for symbol information
- `max_consecutive_nops`: Threshold for treating consecutive NOPs as data (default: 8)

#### Methods

##### `disassemble(machine_code, start_address=0)`

Disassembles binary machine code into assembly instructions.

**Parameters:**
- `machine_code`: bytes object containing the binary machine code
- `start_address`: Starting memory address for disassembly (default: uses ISA default)

**Returns:**
- `DisassemblyResult` object containing instructions, symbols, and data sections

##### `format_disassembly(result, include_addresses=True, include_machine_code=False)`

Formats disassembly result into human-readable text.

**Parameters:**
- `result`: DisassemblyResult object from disassemble()
- `include_addresses`: Whether to include memory addresses in output
- `include_machine_code`: Whether to include raw machine code bytes

**Returns:**
- String containing formatted assembly code

### DisassembledInstruction

Represents a single disassembled instruction.

**Attributes:**
- `address`: Memory address of the instruction
- `machine_code`: Raw bytes of the instruction
- `mnemonic`: Instruction mnemonic (e.g., "ADD", "JMP")
- `operands`: List of operand strings in correct syntax order
- `instruction`: Reference to the original Instruction definition
- `comment`: Optional comment or annotation

### DisassemblyResult

Complete result of the disassembly process.

**Attributes:**
- `instructions`: List of DisassembledInstruction objects
- `symbols`: Dictionary mapping addresses to symbol names
- `data_sections`: Dictionary mapping addresses to raw data bytes
- `entry_point`: Optional entry point address

## Instruction Recognition

The disassembler uses sophisticated pattern matching to identify instructions:

### Pattern-Based Matching

For modern ISA definitions with field-based encoding:

```python
# Example instruction pattern for ZX16 ADD instruction
pattern = {
    'instruction': instruction_def,
    'opcode': 0b0000,           # Expected opcode bits
    'mask': 0b1111,             # Mask for opcode bits
    'fields': field_definitions  # Field layout
}
```

### Opcode Lookup

For simple ISA definitions with direct opcode mapping:

```python
# Direct opcode to instruction mapping
opcode_to_instruction = {
    0b1010: add_instruction,
    0b1011: sub_instruction,
    # ...
}
```

### Multiple Format Support

The disassembler handles various opcode formats:
- Binary strings: "1010"
- Hexadecimal: "0xA"
- Decimal: "10"

## Operand Ordering

The disassembler correctly outputs operands in the order specified by the instruction syntax, not the encoding field order.

### Syntax-Based Ordering

For ZX16 instructions, the disassembler parses the `syntax` field to determine operand order:

```json
{
  "mnemonic": "ADD",
  "syntax": "ADD rd, rs2",
  "encoding": {
    "fields": [
      {"name": "rs2", "bits": "11:9", "type": "register"},
      {"name": "rd", "bits": "8:6", "type": "register"}
    ]
  }
}
```

**Result**: `ADD rd, rs2` (correct syntax order) instead of `ADD rs2, rd` (encoding order)

### ZX16 Example

```assembly
# Source assembly
ADD a0, a1         # a0 = a0 + a1

# Disassembled output (correct)
ADD x6, x7         # Operands in syntax order: rd, rs2

# Previous incorrect output (encoding order)
ADD x7, x6         # Wrong order based on field encoding
```

## Data Section Detection

The disassembler automatically identifies data sections:

### Consecutive NOP Detection

Large blocks of zero bytes (NOPs) are treated as data:

```python
# Configurable threshold
disassembler = Disassembler(isa_def, max_consecutive_nops=16)
```

### Invalid Instruction Handling

Bytes that don't match any instruction pattern are treated as data:

```python
# Unknown bytes become data sections
data_sections[address] = unknown_bytes
```

### Padding Recognition

Common padding patterns are identified and separated from code.

## Symbol Extraction

The disassembler attempts to identify symbols and labels:

### Jump Target Identification

Branch and jump instructions reveal code labels:

```assembly
0x1000: J 0x1020    # Creates label at 0x1020
# ...
0x1020: ADD x6, x7  # Becomes "label_1020:"
```

### Data Reference Detection

Memory access instructions may reveal data symbols:

```assembly
0x1000: LW x6, 0x2000   # May indicate data at 0x2000
```

### Symbol Naming

Generated symbols follow consistent naming conventions:
- Code labels: `label_<address>`
- Data symbols: `data_<address>`
- Function entries: `func_<address>`

## Output Formatting

The disassembler provides flexible output formatting:

### Basic Format

```assembly
ADD x6, x7
SUB x6, x7
J label_1020
```

### With Addresses

```assembly
0x1000: ADD x6, x7
0x1002: SUB x6, x7
0x1004: J label_1020
```

### With Machine Code

```assembly
0x1000: [00 76] ADD x6, x7
0x1002: [01 76] SUB x6, x7
0x1004: [F0 00] J label_1020
```

## ZX16 Disassembly Example

### Input Binary
```bash
python3 -m isa_xform.cli disassemble --isa zx16 --input test_arithmetic.bin --output test_arithmetic_dis.s
```

### Output Assembly
```assembly
; Disassembly of ZX16 v1.0
; Word size: 16 bits
; Endianness: little

    LI x6, 10
    LI x7, 5
    LI x5, 3
    LI x3, 2
    ADD x6, x7
    SUB x6, x7
    ADDI x6, 20
    ADDI x6, 0xFFFFFFFB
    AND x6, x5
    OR x6, x3
    XOR x6, x7
    SLT x6, x5
    SLTU x6, x3
    SLL x6, x5
    SRL x6, x3
    SRA x6, x5
    MV x7, x6
    ECALL 0
```

## Error Handling

The disassembler gracefully handles various error conditions:

### Invalid Instructions

Unknown or corrupted instructions are treated as data:

```python
# Invalid instruction becomes data section
data_sections[current_address] = invalid_bytes
```

### Incomplete Instructions

Partial instructions at the end of binary files are handled:

```python
# Remaining bytes become data
if remaining_bytes:
    data_sections[current_address] = remaining_bytes
```

### Memory Access Errors

File reading errors are handled with appropriate error messages.

## Performance Considerations

### Efficient Pattern Matching

The disassembler builds lookup tables for fast instruction recognition:

```python
# Pre-built pattern tables for efficient matching
self.instruction_patterns = []
self.opcode_to_instruction = {}
```

### Memory Usage

The disassembler processes instructions incrementally to minimize memory usage:

```python
# Process in instruction-sized chunks
while i < len(machine_code):
    instr_bytes = machine_code[i:i + instruction_size]
    # Process instruction...
    i += instruction_size
```

## Integration with Other Components

### ISA Loader Integration

The disassembler works seamlessly with the ISA loader:

```python
# Load ISA and create disassembler
isa_def = loader.load_isa("zx16")
disassembler = Disassembler(isa_def)
```

### Symbol Table Integration

Optional symbol table support for enhanced disassembly:

```python
# Use existing symbol table
symbol_table = SymbolTable()
symbol_table.add_symbol("main", 0x1000)
disassembler = Disassembler(isa_def, symbol_table)
```

### CLI Integration

The disassembler is accessible through the command-line interface:

```bash
python3 -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s
```

## Best Practices

### ISA Definition

Ensure ISA definitions include proper syntax fields for correct operand ordering:

```json
{
  "mnemonic": "ADD",
  "syntax": "ADD rd, rs2",
  "encoding": {
    "fields": [...]
  }
}
```

### Error Handling

Always check for disassembly errors and handle data sections appropriately:

```python
result = disassembler.disassemble(machine_code)
if result.data_sections:
    print("Data sections found:", result.data_sections)
```

### Output Formatting

Choose appropriate output format for your use case:

```python
# For debugging
formatted = disassembler.format_disassembly(result, include_addresses=True, include_machine_code=True)

# For clean assembly
formatted = disassembler.format_disassembly(result, include_addresses=False)
```

## Binary Input Format

The disassembler supports both headered and raw binary formats, automatically detecting the format and extracting metadata when available.

### Headered Binary Support

The disassembler automatically detects and processes ISA-specific headers:

- **Magic Detection**: Recognizes `ISA\x01` magic number
- **Entry Point Extraction**: Automatically uses the entry point from the header
- **ISA Verification**: Confirms the binary was assembled with the correct ISA
- **Fallback**: Falls back to raw binary processing if no header is detected

### Header Format

```
ISA\x01 + [ISA Name Length] + [ISA Name] + [Code Size] + [Entry Point] + [Machine Code]
```

### Automatic Address Detection

When a headered binary is detected, the disassembler automatically:

1. **Extracts the entry point** from the header
2. **Starts disassembly at the correct address** without requiring `--start-address`
3. **Uses the ISA name** for verification and enhanced output

### Raw Binary Support

For raw binaries (no header), the disassembler:

1. **Uses the ISA default** code start address
2. **Requires manual specification** of start address if different from default
3. **Processes the entire file** as machine code

### Examples

```bash
# Headered binary (automatic entry point detection)
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s

# Raw binary (manual start address)
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s --start-address 0x20

# Debug output shows header detection
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s --debug
```

### Header Detection Output

When processing headered binaries, verbose output shows:

```
Loaded ISA: ZX16 v1.1
Read 25 bytes from program.bin
Extracted 8 bytes of code from header
File entry point: 0x20
Disassembled 4 instructions
Found 0 data sections
```

## Disassembly Process

This disassembler provides professional-grade machine code analysis with correct operand ordering and comprehensive error handling, making it suitable for educational, research, and development applications. 