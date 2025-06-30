# Custom Instruction Implementations

This document explains how to extend ISA definitions with custom instruction implementations using Python code.

## Overview

The ISA transformation toolkit now supports custom instruction implementations that allow users to define the actual behavior of instructions using Python code. This enables:

- **Custom arithmetic operations** (multiplication, division, etc.)
- **Specialized instructions** (crypto operations, DSP functions, etc.)
- **Memory operations** (block copy, pattern matching, etc.)
- **System instructions** (I/O, interrupts, etc.)

## ISA Definition Format

To add custom implementations to your ISA definition, add an `implementation` field to your instruction definitions:

```json
{
  "mnemonic": "MULT",
  "format": "R-type",
  "description": "Multiply registers (custom instruction)",
  "syntax": "MULT rd, rs2",
  "semantics": "rd = rd * rs2 (16-bit result)",
  "implementation": "# Custom multiplication instruction\nrd_val = read_register(operands['rd'])\nrs2_val = read_register(operands['rs2'])\nresult = (rd_val * rs2_val) & 0xFFFF\nwrite_register(operands['rd'], result)\n# Set flags\nset_flag('Z', result == 0)\nset_flag('N', (result & 0x8000) != 0)",
  "encoding": {
    "fields": [
      {"name": "funct4", "bits": "15:12", "value": "1111"},
      {"name": "rs2", "bits": "11:9", "type": "register"},
      {"name": "rd", "bits": "8:6", "type": "register"},
      {"name": "func3", "bits": "5:3", "value": "000"},
      {"name": "opcode", "bits": "2:0", "value": "000"}
    ]
  }
}
```

## Implementation Environment

Your custom instruction implementations run in a controlled environment with access to:

### Available Variables

- `registers`: Dictionary of register values
- `memory`: Bytearray representing memory
- `pc`: Current program counter
- `flags`: Dictionary of status flags
- `operands`: Dictionary of instruction operands (from encoding)
- `context`: Full execution context object

### Helper Functions

- `read_register(name)`: Read a register value
- `write_register(name, value)`: Write a value to a register
- `read_memory(addr)`: Read a 16-bit value from memory (little-endian)
- `write_memory(addr, value)`: Write a 16-bit value to memory (little-endian)
- `set_flag(name, value)`: Set a status flag
- `get_flag(name)`: Get a status flag value

### Available Built-ins

The implementation environment provides safe access to common Python built-ins:
- Mathematical functions: `abs`, `min`, `max`, `pow`, `round`
- Type conversions: `int`, `bool`, `str`, `hex`, `bin`
- Iteration: `range`, `len`, `enumerate`
- And more...

## Examples

### Basic Arithmetic Instruction

```json
{
  "mnemonic": "MULT",
  "implementation": "# Multiply two registers\nrd_val = read_register(operands['rd'])\nrs2_val = read_register(operands['rs2'])\nresult = (rd_val * rs2_val) & 0xFFFF\nwrite_register(operands['rd'], result)\n# Set zero and negative flags\nset_flag('Z', result == 0)\nset_flag('N', (result & 0x8000) != 0)"
}
```

### Register Swap Instruction

```json
{
  "mnemonic": "SWAP",
  "implementation": "# Swap two register values\ntemp = read_register(operands['rd'])\nwrite_register(operands['rd'], read_register(operands['rs2']))\nwrite_register(operands['rs2'], temp)"
}
```

### Memory Copy Instruction

```json
{
  "mnemonic": "MEMCPY",
  "implementation": "# Copy 16 bytes from source to destination\nsrc_addr = read_register(operands['rs2'])\ndst_addr = read_register(operands['rd'])\nfor i in range(16):\n    if src_addr + i < len(memory) and dst_addr + i < len(memory):\n        value = memory[src_addr + i]\n        memory[dst_addr + i] = value"
}
```

### Cryptographic Instruction

```json
{
  "mnemonic": "CRC16",
  "implementation": "# Calculate CRC16\ndef crc16_update(crc, byte):\n    crc ^= byte\n    for _ in range(8):\n        if crc & 1:\n            crc = (crc >> 1) ^ 0xA001\n        else:\n            crc >>= 1\n    return crc\n\nrd_val = read_register(operands['rd'])\nrs2_val = read_register(operands['rs2'])\nresult = crc16_update(rd_val, rs2_val & 0xFF)\nwrite_register(operands['rd'], result)"
}
```

### Conditional Instruction

```json
{
  "mnemonic": "CMPZ",
  "implementation": "# Compare register with zero and set flags\nval = read_register(operands['rd'])\nset_flag('Z', val == 0)\nset_flag('N', (val & 0x8000) != 0)\nset_flag('P', val > 0)"
}
```

## Usage in Assembly

Once you've defined custom instructions in your ISA, you can use them in assembly code:

```assembly
; Example using custom instructions
.org 0x100

start:
    ADD x6, x7      ; Standard add instruction
    MULT x6, x7     ; Custom multiply instruction
    SWAP x6, x7     ; Custom swap instruction
    CRC16 x6, x7    ; Custom CRC16 instruction
    MEMCPY x6, x7   ; Custom memory copy instruction
```

## Loading and Compilation

Custom instruction implementations are automatically compiled when you load an ISA definition:

```python
from isa_xform.core.isa_loader import ISALoader

# Load ISA with custom implementations
loader = ISALoader()
isa_def = loader.load_isa_from_file("my_custom_isa.json")

# The implementations are now compiled and ready to use
```

## Error Handling

If there are syntax errors in your implementation code, the ISA loader will report them:

```python
try:
    isa_def = loader.load_isa_from_file("my_isa.json")
except Exception as e:
    print(f"Failed to load ISA: {e}")
```

## Security Considerations

- Custom implementations run in a sandboxed environment
- Only safe built-in functions are available
- No file system or network access
- Memory access is bounds-checked

## Best Practices

1. **Keep implementations simple**: Complex logic should be broken into multiple instructions
2. **Handle edge cases**: Check for division by zero, overflow, etc.
3. **Set appropriate flags**: Update status flags to match instruction semantics
4. **Document behavior**: Use comments to explain complex implementations
5. **Test thoroughly**: Verify implementations work correctly with various inputs

## Integration with Assembler and Disassembler

Custom instructions work seamlessly with the existing assembler and disassembler:

- **Assembler**: Custom instructions are encoded using their defined encoding
- **Disassembler**: Custom instructions are disassembled using their defined syntax
- **Simulator**: Custom instructions can be executed using their implementations

## Example: Complete Custom ISA

See `src/isa_definitions/custom_isa_example.json` for a complete example ISA with custom instruction implementations.

## Testing Custom Instructions

Use the provided test script to verify your custom instructions:

```bash
python test_custom_instructions.py
```

This will test loading, compilation, and execution of custom instruction implementations. 