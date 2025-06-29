# Bit Utilities Documentation

The Bit Utilities module provides low-level bit manipulation functions essential for instruction encoding, decoding, and data processing in the ISA transformation toolkit. All functions are designed to be ISA-agnostic and configurable.

## Overview

The bit utilities handle common operations needed in assembly, disassembly, and instruction processing:

- Bit field extraction and manipulation
- Sign extension with configurable bit widths
- Number format parsing and validation
- Alignment operations
- Endianness conversions

## Key Features

- **Configurable bit widths**: No hardcoded assumptions about data sizes
- **Comprehensive validation**: All functions validate inputs and provide clear error messages
- **Multiple number formats**: Support for binary, decimal, and hexadecimal representations
- **Endianness handling**: Conversion between byte arrays and integers
- **Performance optimized**: Efficient implementations for common operations

## Core Functions

### Bit Field Operations

#### `extract_bits(value, high, low)`

Extracts bits from a value between high and low positions (inclusive).

```python
from isa_xform.utils.bit_utils import extract_bits

# Extract bits 7:4 from 0b11110000
result = extract_bits(0b11110000, 7, 4)  # Returns 0b1111 (15)

# Extract instruction opcode (bits 31:28)
opcode = extract_bits(instruction_word, 31, 28)
```

**Parameters:**
- `value`: Integer value to extract bits from
- `high`: High bit position (inclusive)
- `low`: Low bit position (inclusive)

**Returns:**
- Integer containing the extracted bits

**Raises:**
- `ValueError`: If bit positions are invalid

#### `set_bits(value, high, low, new_value)`

Sets bits in a value between high and low positions (inclusive).

```python
from isa_xform.utils.bit_utils import set_bits

# Set bits 7:4 to 0b1010 in 0x00
result = set_bits(0x00, 7, 4, 0b1010)  # Returns 0xA0

# Encode register field in instruction
instruction = set_bits(instruction, 23, 20, register_num)
```

**Parameters:**
- `value`: Original integer value
- `high`: High bit position (inclusive)
- `low`: Low bit position (inclusive)
- `new_value`: New value for the bit field

**Returns:**
- Integer with the specified bits modified

**Raises:**
- `ValueError`: If bit positions are invalid or new_value doesn't fit

### Sign Extension

#### `sign_extend(value, source_bit_width, target_bit_width=32)`

Sign extends a value from source bit width to target bit width.

```python
from isa_xform.utils.bit_utils import sign_extend

# Sign extend 4-bit value to 8 bits
result = sign_extend(0b1111, 4, 8)  # Returns 0b11111111 (-1)

# Sign extend immediate field for different architectures
extended = sign_extend(immediate, 12, isa_def.word_size)
```

**Parameters:**
- `value`: Value to sign extend
- `source_bit_width`: Original bit width of the value
- `target_bit_width`: Target bit width (default: 32)

**Returns:**
- Sign-extended integer value

**Raises:**
- `ValueError`: If bit widths are invalid or value doesn't fit in source width

### Bit Range Parsing

#### `parse_bit_range(bit_range)`

Parses a bit range string in format "high:low".

```python
from isa_xform.utils.bit_utils import parse_bit_range

# Parse instruction field specification
high, low = parse_bit_range("15:12")  # Returns (15, 12)

# Parse from ISA definition
field_bits = instruction.encoding.fields[0]["bits"]
high, low = parse_bit_range(field_bits)
```

**Parameters:**
- `bit_range`: String in format "high:low"

**Returns:**
- Tuple of (high, low) bit positions

**Raises:**
- `ValueError`: If format is invalid or bit positions are invalid

### Mask Operations

#### `create_mask(bit_width)`

Creates a mask with the specified number of bits set.

```python
from isa_xform.utils.bit_utils import create_mask

# Create 8-bit mask
mask = create_mask(8)  # Returns 0xFF

# Create field mask for instruction encoding
field_mask = create_mask(field_width)
```

**Parameters:**
- `bit_width`: Number of bits in the mask

**Returns:**
- Integer mask with specified number of lower bits set

**Raises:**
- `ValueError`: If bit width is invalid (≤ 0 or > 64)

### Alignment Operations

#### `align_up(value, alignment)`

Aligns a value up to the nearest multiple of alignment.

```python
from isa_xform.utils.bit_utils import align_up

# Align address to 4-byte boundary
aligned_addr = align_up(0x1003, 4)  # Returns 0x1004

# Align data section to ISA-specified boundary
aligned = align_up(current_addr, isa_def.alignment_requirement)
```

**Parameters:**
- `value`: Value to align
- `alignment`: Alignment boundary (must be power of 2)

**Returns:**
- Aligned value

**Raises:**
- `ValueError`: If alignment is not a power of 2 or inputs are invalid

#### `align_down(value, alignment)`

Aligns a value down to the nearest multiple of alignment.

```python
from isa_xform.utils.bit_utils import align_down

# Align address down to 4-byte boundary
aligned_addr = align_down(0x1003, 4)  # Returns 0x1000
```

**Parameters:**
- `value`: Value to align
- `alignment`: Alignment boundary (must be power of 2)

**Returns:**
- Aligned value

**Raises:**
- `ValueError`: If alignment is not a power of 2 or inputs are invalid

### Bit Analysis

#### `count_leading_zeros(value, bit_width)`

Counts the number of leading zero bits in a value.

```python
from isa_xform.utils.bit_utils import count_leading_zeros

# Count leading zeros in 8-bit value
zeros = count_leading_zeros(0b00001111, 8)  # Returns 4

# Analyze instruction density
zeros = count_leading_zeros(instruction_word, isa_def.instruction_size)
```

**Parameters:**
- `value`: Value to analyze
- `bit_width`: Bit width of the value

**Returns:**
- Number of leading zero bits

**Raises:**
- `ValueError`: If inputs are invalid

#### `count_trailing_zeros(value)`

Counts the number of trailing zero bits in a value.

```python
from isa_xform.utils.bit_utils import count_trailing_zeros

# Count trailing zeros
zeros = count_trailing_zeros(0b11110000)  # Returns 4

# Check alignment
alignment = 1 << count_trailing_zeros(address)
```

**Parameters:**
- `value`: Value to analyze

**Returns:**
- Number of trailing zero bits

**Raises:**
- `ValueError`: If value is invalid

### Utility Functions

#### `is_power_of_two(value)`

Checks if a value is a power of 2.

```python
from isa_xform.utils.bit_utils import is_power_of_two

# Check alignment values
if is_power_of_two(alignment):
    # Safe to use for alignment operations
    aligned = align_up(addr, alignment)
```

**Parameters:**
- `value`: Value to check

**Returns:**
- Boolean indicating if value is a power of 2

#### `log2(value)`

Calculates log base 2 of a power-of-2 value.

```python
from isa_xform.utils.bit_utils import log2

# Calculate shift amount
shift_amount = log2(alignment)  # For power-of-2 alignment
```

**Parameters:**
- `value`: Power-of-2 value

**Returns:**
- Log base 2 of the value

**Raises:**
- `ValueError`: If value is not a power of 2

### Bit Pattern Operations

#### `reverse_bits(value, bit_width)`

Reverses the bits in a value.

```python
from isa_xform.utils.bit_utils import reverse_bits

# Reverse 8-bit value
reversed_val = reverse_bits(0b10110001, 8)  # Returns 0b10001101

# Handle different endianness requirements
if isa_def.bit_order == 'reversed':
    instruction = reverse_bits(instruction, isa_def.instruction_size)
```

**Parameters:**
- `value`: Value to reverse
- `bit_width`: Bit width of the value

**Returns:**
- Value with bits reversed

**Raises:**
- `ValueError`: If inputs are invalid

### Endianness Conversion

#### `bytes_to_int(bytes_data, endianness='little')`

Converts byte array to integer with specified endianness.

```python
from isa_xform.utils.bit_utils import bytes_to_int

# Convert instruction bytes to integer
instruction_bytes = b'\x12\x34\x56\x78'
instruction_word = bytes_to_int(instruction_bytes, 'big')

# Use ISA-defined endianness
endianness = 'little' if isa_def.endianness.lower().startswith('little') else 'big'
value = bytes_to_int(data_bytes, endianness)
```

**Parameters:**
- `bytes_data`: Byte array to convert
- `endianness`: 'little' or 'big' (default: 'little')

**Returns:**
- Integer value

**Raises:**
- `ValueError`: If endianness is invalid

#### `int_to_bytes(value, byte_count, endianness='little')`

Converts integer to byte array with specified endianness.

```python
from isa_xform.utils.bit_utils import int_to_bytes

# Convert instruction word to bytes
instruction_word = 0x12345678
instruction_bytes = int_to_bytes(instruction_word, 4, 'big')

# Use ISA-defined parameters
bytes_needed = isa_def.instruction_size // 8
endianness = 'little' if isa_def.endianness.lower().startswith('little') else 'big'
machine_code = int_to_bytes(encoded_instruction, bytes_needed, endianness)
```

**Parameters:**
- `value`: Integer value to convert
- `byte_count`: Number of bytes in output
- `endianness`: 'little' or 'big' (default: 'little')

**Returns:**
- Byte array

**Raises:**
- `ValueError`: If value doesn't fit in specified byte count or endianness is invalid

## Error Handling

All bit utility functions include comprehensive error handling:

### Input Validation

- Type checking for all parameters
- Range validation for bit positions and widths
- Overflow detection for bit operations

### Clear Error Messages

```python
# Example error messages
ValueError: "Bit width must be positive"
ValueError: "Value 16 doesn't fit in 4 bits"
ValueError: "Alignment 6 must be a power of 2"
ValueError: "Bit range must be in format 'high:low', got 'invalid'"
```

### Exception Types

All functions raise `ValueError` for invalid inputs with descriptive messages.

## Usage Examples

### Instruction Encoding

```python
from isa_xform.utils.bit_utils import set_bits, create_mask

def encode_r_type_instruction(opcode, rd, rs1, rs2):
    """Encode R-type instruction: opcode[31:26] rd[25:21] rs1[20:16] rs2[15:11]"""
    instruction = 0
    instruction = set_bits(instruction, 31, 26, opcode)
    instruction = set_bits(instruction, 25, 21, rd)
    instruction = set_bits(instruction, 20, 16, rs1)
    instruction = set_bits(instruction, 15, 11, rs2)
    return instruction
```

### Instruction Decoding

```python
from isa_xform.utils.bit_utils import extract_bits

def decode_i_type_instruction(instruction_word):
    """Decode I-type instruction"""
    opcode = extract_bits(instruction_word, 31, 26)
    rd = extract_bits(instruction_word, 25, 21)
    rs1 = extract_bits(instruction_word, 20, 16)
    immediate = extract_bits(instruction_word, 15, 0)
    
    # Sign extend immediate
    immediate = sign_extend(immediate, 16, 32)
    
    return {
        'opcode': opcode,
        'rd': rd,
        'rs1': rs1,
        'immediate': immediate
    }
```

### ISA-Agnostic Operations

```python
from isa_xform.utils.bit_utils import *

def encode_instruction_field(instruction, field_def, value):
    """Encode instruction field based on ISA definition"""
    high, low = parse_bit_range(field_def['bits'])
    bit_width = high - low + 1
    
    # Validate value fits in field
    max_value = create_mask(bit_width)
    if value > max_value:
        raise ValueError(f"Value {value} doesn't fit in {bit_width}-bit field")
    
    # Set the field
    return set_bits(instruction, high, low, value)
```

### Memory Alignment

```python
from isa_xform.utils.bit_utils import align_up, is_power_of_two

def align_memory_section(address, isa_definition):
    """Align memory section based on ISA requirements"""
    alignment = isa_definition.memory_alignment
    
    if not is_power_of_two(alignment):
        raise ValueError(f"ISA alignment {alignment} must be power of 2")
    
    return align_up(address, alignment)
```

## Performance Considerations

### Optimization Tips

- Bit operations are highly optimized in Python
- Use bitwise operations instead of arithmetic where possible
- Cache mask values for repeated operations
- Pre-compute common bit patterns

### Memory Efficiency

- Functions operate on integers, not object structures
- No unnecessary temporary objects created
- Efficient bit manipulation using native operations

### Common Patterns

```python
# Efficient field extraction pattern
def extract_instruction_fields(instruction_word, field_definitions):
    """Extract multiple fields efficiently"""
    fields = {}
    for field_def in field_definitions:
        name = field_def['name']
        high, low = parse_bit_range(field_def['bits'])
        fields[name] = extract_bits(instruction_word, high, low)
    return fields
```

## Integration

The bit utilities integrate seamlessly with other components:

### With Assembler

```python
# Assembler uses bit utils for instruction encoding
encoded = set_bits(0, 31, 28, opcode)
encoded = set_bits(encoded, 27, 24, register_num)
```

### With Disassembler

```python
# Disassembler uses bit utils for instruction decoding
opcode = extract_bits(instruction_word, 31, 28)
register = extract_bits(instruction_word, 27, 24)
```

### With ISA Loader

```python
# ISA definitions specify bit ranges
field_bits = instruction_field['bits']
high, low = parse_bit_range(field_bits)
```

## Testing

The bit utilities include comprehensive tests:

### Unit Tests

- Test all functions with valid and invalid inputs
- Edge case testing (zero, maximum values, boundary conditions)
- Error condition testing

### Property-Based Testing

- Round-trip testing (encode/decode operations)
- Invariant checking (alignment properties)
- Random input validation

### Performance Testing

- Benchmark critical operations
- Memory usage profiling
- Scalability testing with large values 