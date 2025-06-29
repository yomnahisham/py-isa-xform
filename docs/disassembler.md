# Disassembler Documentation

The Disassembler component converts machine code back into human-readable assembly language. It supports various instruction formats, handles data sections, and provides configurable output formatting.

## Overview

The disassembler takes binary machine code and reconstructs assembly language instructions based on the ISA definition. It can differentiate between code and data sections, handle different instruction encodings, and generate formatted assembly output.

## Key Features

- **ISA-agnostic design**: Works with any custom ISA definition
- **Pattern matching**: Flexible instruction recognition using opcode patterns and masks
- **Data section detection**: Automatically identifies non-instruction data
- **Symbol extraction**: Attempts to identify and name jump targets and data references
- **Configurable output**: Various formatting options for disassembled code
- **Error resilience**: Gracefully handles invalid or corrupted machine code

## Core Classes

### Disassembler

The main disassembler class that handles machine code analysis and conversion.

```python
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.isa_loader import ISALoader

# Load ISA definition
loader = ISALoader()
isa_definition = loader.load_isa("simple_risc")

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
- `operands`: List of operand strings
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
# Example instruction pattern
pattern = {
    'instruction': instruction_def,
    'opcode': 0b1010,           # Expected opcode bits
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
0x1000: JMP 0x1020    # Creates label at 0x1020
# ...
0x1020: ADD R1, R2    # Becomes "label_1020:"
```

### Data Reference Detection

Memory access instructions may reveal data symbols:

```assembly
0x1000: LD R1, 0x2000   # May indicate data at 0x2000
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
ADD R1, R2, R3
SUB R4, R5, R6
JMP label_1020
```

### With Addresses

```assembly
0x1000: ADD R1, R2, R3
0x1004: SUB R4, R5, R6
0x1008: JMP label_1020
```

### With Machine Code

```assembly
0x1000: 12340000    ADD R1, R2, R3
0x1004: 23450000    SUB R4, R5, R6
0x1008: 80001020    JMP label_1020
```

### With Data Sections

```assembly
# Code section
0x1000: ADD R1, R2, R3
0x1004: JMP data_2000

# Data section
data_2000:
    .word 0x12345678
    .word 0x9ABCDEF0
```

## Error Handling

The disassembler includes robust error handling:

### Graceful Degradation

- Invalid instructions are treated as data
- Partial instructions at end of file are handled gracefully
- Corrupted machine code doesn't crash the disassembler

### Error Reporting

```python
from isa_xform.utils.error_handling import DisassemblerError

try:
    result = disassembler.disassemble(machine_code)
except DisassemblerError as e:
    print(f"Disassembly failed: {e}")
```

### Diagnostic Information

- Reports unrecognized instruction patterns
- Identifies suspicious data patterns
- Provides statistics on successful vs. failed instruction decoding

## Configuration

The disassembler adapts to ISA-specific configurations:

### Instruction Size

Automatically uses the ISA-defined instruction size:

```python
instruction_size_bytes = isa_definition.instruction_size // 8
```

### Endianness

Respects the ISA endianness setting:

```python
endianness = 'little' if isa_def.endianness.lower().startswith('little') else 'big'
```

### Register Names

Uses ISA-defined register names and aliases:

```python
reg_name = get_register_name(reg_num)  # Uses ISA register definitions
```

## Advanced Features

### Context-Aware Disassembly

The disassembler uses context to improve accuracy:

- **Branch analysis**: Identifies likely code vs. data based on branch targets
- **Pattern recognition**: Recognizes common instruction sequences
- **Statistical analysis**: Uses instruction frequency to validate disassembly

### Heuristic Improvements

Various heuristics improve disassembly quality:

- **Function boundary detection**: Identifies function starts and ends
- **Loop recognition**: Identifies loop structures
- **Data alignment**: Recognizes aligned data structures

## Usage Examples

### Basic Disassembly

```python
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.isa_loader import ISALoader

# Load ISA definition
loader = ISALoader()
isa_def = loader.load_isa("simple_risc")

# Create disassembler
disassembler = Disassembler(isa_def)

# Read and disassemble binary file
with open("program.bin", "rb") as f:
    machine_code = f.read()

result = disassembler.disassemble(machine_code, start_address=0x1000)

# Format and display results
output = disassembler.format_disassembly(
    result, 
    include_addresses=True,
    include_machine_code=True
)
print(output)
```

### Custom Configuration

```python
# Custom consecutive NOP threshold
disassembler = Disassembler(isa_def, max_consecutive_nops=32)

# Disassemble with custom start address
result = disassembler.disassemble(machine_code, start_address=0x8000)

# Access individual components
for instruction in result.instructions:
    print(f"{instruction.address:04X}: {instruction.mnemonic} {', '.join(instruction.operands)}")

for addr, data in result.data_sections.items():
    print(f"Data at {addr:04X}: {data.hex()}")
```

### Symbol Analysis

```python
# Extract and analyze symbols
symbols = result.symbols
print("Discovered symbols:")
for addr, name in symbols.items():
    print(f"  {name} at 0x{addr:04X}")

# Find entry points
entry_points = [addr for addr, name in symbols.items() if name.startswith('func_')]
print(f"Potential entry points: {len(entry_points)}")
```

## Integration with Other Components

### File Format Support

The disassembler works with various file formats:

- **Raw binary**: Direct machine code bytes
- **ISA binary format**: Custom format with headers
- **ELF/COFF**: Via external loaders (future enhancement)

### Symbol Table Integration

```python
from isa_xform.core.symbol_table import SymbolTable

# Use existing symbol table
symbol_table = SymbolTable()
# ... populate symbol table ...

disassembler = Disassembler(isa_def, symbol_table)
result = disassembler.disassemble(machine_code)
```

### Parser Integration

Disassembled output can be re-parsed:

```python
from isa_xform.core.parser import Parser

# Disassemble to text
assembly_text = disassembler.format_disassembly(result)

# Parse back to AST
parser = Parser(isa_def)
nodes = parser.parse(assembly_text)
```

## Performance Considerations

### Memory Usage

- Instruction lookup tables are built once during initialization
- Large machine code files are processed in streaming fashion where possible
- Symbol tables grow with the number of discovered symbols

### Processing Speed

- Pattern matching is optimized with pre-computed masks
- Opcode lookup uses hash tables for O(1) access
- Data section detection uses efficient byte scanning

### Optimization Tips

- Use appropriate `max_consecutive_nops` threshold for your data
- Pre-load symbol tables when available
- Process large files in chunks if memory is limited

## Extensibility

The disassembler supports various extensions:

### Custom Instruction Handlers

```python
def custom_instruction_decoder(instr_word, instr_bytes, address, pattern):
    # Custom decoding logic
    return DisassembledInstruction(...)

# Register custom handler
disassembler.custom_decoders['CUSTOM_FORMAT'] = custom_instruction_decoder
```

### Custom Symbol Recognition

```python
def custom_symbol_extractor(instructions):
    # Custom symbol extraction logic
    return symbol_dict

# Use custom symbol extraction
symbols = custom_symbol_extractor(result.instructions)
```

### Output Format Extensions

```python
def custom_formatter(result, options):
    # Custom output formatting
    return formatted_text

# Use custom formatter
output = custom_formatter(result, custom_options)
``` 