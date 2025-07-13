"""
Bit manipulation utilities for ISA transformation
"""

from typing import Tuple, List, Literal


def extract_bits(value: int, high: int, low: int) -> int:
    """
    Extract bits from high to low position (inclusive)
    
    Args:
        value: The value to extract bits from
        high: High bit position (inclusive)
        low: Low bit position (inclusive)
    
    Returns:
        Extracted bits as integer
    """
    mask = (1 << (high - low + 1)) - 1
    return (value >> low) & mask


def set_bits(value: int, high: int, low: int, new_value: int) -> int:
    """
    Set bits from high to low position (inclusive)
    
    Args:
        value: The value to modify
        high: High bit position (inclusive)
        low: Low bit position (inclusive)
        new_value: New value for the bits
    
    Returns:
        Modified value
    """
    mask = (1 << (high - low + 1)) - 1
    cleared = value & ~(mask << low)
    return cleared | ((new_value & mask) << low)


def sign_extend(value: int, source_bit_width: int, target_bit_width: int = 32) -> int:
    """
    Sign extend a value from source bit width to target bit width
    
    Args:
        value: The value to sign extend
        source_bit_width: Original bit width of the value
        target_bit_width: Target bit width (default: 32)
    
    Returns:
        Sign extended value
        
    Raises:
        ValueError: If bit widths are invalid
    """
    if source_bit_width <= 0 or target_bit_width <= 0:
        raise ValueError("Bit widths must be positive")
    if source_bit_width > target_bit_width:
        raise ValueError("Source bit width cannot be greater than target bit width")
    if value < 0 or value >= (1 << source_bit_width):
        raise ValueError(f"Value {value} doesn't fit in {source_bit_width} bits")
    
    if value & (1 << (source_bit_width - 1)):
        # Negative value, extend with 1s
        sign_bits = ((1 << (target_bit_width - source_bit_width)) - 1) << source_bit_width
        return value | sign_bits
    else:
        # Positive value, extend with 0s
        return value


def parse_bit_range(bit_range: str) -> Tuple[int, int]:
    """
    Parse a bit range string like "15:12" or "7:0"
    
    Args:
        bit_range: Bit range string in format "high:low"
    
    Returns:
        Tuple of (high, low) bit positions
    
    Raises:
        ValueError: If bit range format is invalid
    """
    if not isinstance(bit_range, str):
        raise ValueError(f"Bit range must be a string, got {type(bit_range)}")
    
    try:
        parts = bit_range.split(":")
        if len(parts) != 2:
            raise ValueError(f"Bit range must be in format 'high:low', got '{bit_range}'")
        
        high, low = map(int, parts)
        if high < 0 or low < 0:
            raise ValueError(f"Bit positions must be non-negative: {bit_range}")
        if high < low:
            raise ValueError(f"High bit ({high}) must be >= low bit ({low})")
        return high, low
    except (ValueError, AttributeError) as e:
        if "invalid literal" in str(e):
            raise ValueError(f"Invalid bit range format: {bit_range}")
        raise


def parse_multi_field_bits(bit_spec: str) -> List[Tuple[int, int]]:
    """
    Parse a multi-field bit specification like "15:12,0" or "31:25,11:8"
    
    Args:
        bit_spec: Bit specification string in format "high1:low1,high2:low2,..."
    
    Returns:
        List of (high, low) bit position tuples
    
    Raises:
        ValueError: If bit specification format is invalid
    """
    if not isinstance(bit_spec, str):
        raise ValueError(f"Bit specification must be a string, got {type(bit_spec)}")
    
    try:
        # Split by comma to get individual bit ranges
        ranges = bit_spec.split(",")
        result = []
        
        for range_str in ranges:
            range_str = range_str.strip()
            if ":" in range_str:
                # Parse as "high:low" range
                high, low = parse_bit_range(range_str)
                result.append((high, low))
            else:
                # Parse as single bit
                bit_pos = int(range_str)
                if bit_pos < 0:
                    raise ValueError(f"Bit position must be non-negative: {range_str}")
                result.append((bit_pos, bit_pos))
        
        return result
    except (ValueError, AttributeError) as e:
        if "invalid literal" in str(e):
            raise ValueError(f"Invalid bit specification format: {bit_spec}")
        raise


def extract_multi_field_bits(value: int, bit_spec: str) -> int:
    """
    Extract bits from a value according to a multi-field specification
    
    Args:
        value: Source value to extract bits from
        bit_spec: Bit specification string like "15:12,0"
    
    Returns:
        Extracted value with bits concatenated according to specification
    
    Example:
        extract_multi_field_bits(0x1234, "15:12,0") 
        # Extracts bits 15:12 and bit 0, concatenates them
    """
    ranges = parse_multi_field_bits(bit_spec)
    result = 0
    bit_offset = 0
    
    # Process ranges in reverse order to maintain bit order
    for high, low in reversed(ranges):
        width = high - low + 1
        extracted = extract_bits(value, high, low)
        result |= (extracted << bit_offset)
        bit_offset += width
    
    return result


def set_multi_field_bits(value: int, bit_spec: str, new_value: int) -> int:
    """
    Set bits in a value according to a multi-field specification
    
    Args:
        value: Target value to modify
        bit_spec: Bit specification string like "15:12,0"
        new_value: Value to insert into the specified bits
    
    Returns:
        Modified value with new_value inserted into specified bits
    
    Example:
        set_multi_field_bits(0x0000, "15:12,0", 0x1A)
        # Sets bits 15:12 to 0x1 and bit 0 to 0x0
    """
    ranges = parse_multi_field_bits(bit_spec)
    result = value
    bit_offset = 0
    
    # Process ranges in reverse order to maintain bit order
    for high, low in reversed(ranges):
        width = high - low + 1
        mask = (1 << width) - 1
        field_value = (new_value >> bit_offset) & mask
        result = set_bits(result, high, low, field_value)
        bit_offset += width
    
    return result


def create_mask(bit_width: int) -> int:
    """
    Create a mask with specified bit width
    
    Args:
        bit_width: Number of bits in the mask
    
    Returns:
        Mask value
        
    Raises:
        ValueError: If bit width is invalid
    """
    if bit_width <= 0:
        raise ValueError("Bit width must be positive")
    if bit_width > 64:  # Prevent overflow issues
        raise ValueError("Bit width cannot exceed 64")
    return (1 << bit_width) - 1


def is_power_of_two(value: int) -> bool:
    """
    Check if a value is a power of 2
    
    Args:
        value: Value to check
    
    Returns:
        True if value is a power of 2
    """
    return value > 0 and (value & (value - 1)) == 0


def log2(value: int) -> int:
    """
    Calculate log base 2 of a value (must be power of 2)
    
    Args:
        value: Value to calculate log2 of (must be power of 2)
    
    Returns:
        Log base 2 of the value
    
    Raises:
        ValueError: If value is not a power of 2
    """
    if not isinstance(value, int):
        raise ValueError("Value must be an integer")
    if not is_power_of_two(value):
        raise ValueError(f"{value} is not a power of 2")
    
    result = 0
    while value > 1:
        value >>= 1
        result += 1
    return result


def align_up(value: int, alignment: int) -> int:
    """
    Align a value up to the nearest multiple of alignment
    
    Args:
        value: Value to align
        alignment: Alignment boundary (must be power of 2)
    
    Returns:
        Aligned value
    
    Raises:
        ValueError: If alignment is not a power of 2 or inputs are invalid
    """
    if not isinstance(value, int) or not isinstance(alignment, int):
        raise ValueError("Value and alignment must be integers")
    if value < 0:
        raise ValueError("Value must be non-negative")
    if not is_power_of_two(alignment):
        raise ValueError(f"Alignment {alignment} must be a power of 2")
    
    return (value + alignment - 1) & ~(alignment - 1)


def align_down(value: int, alignment: int) -> int:
    """
    Align a value down to the nearest multiple of alignment
    
    Args:
        value: Value to align
        alignment: Alignment boundary (must be power of 2)
    
    Returns:
        Aligned value
    
    Raises:
        ValueError: If alignment is not a power of 2 or inputs are invalid
    """
    if not isinstance(value, int) or not isinstance(alignment, int):
        raise ValueError("Value and alignment must be integers")
    if value < 0:
        raise ValueError("Value must be non-negative")
    if not is_power_of_two(alignment):
        raise ValueError(f"Alignment {alignment} must be a power of 2")
    
    return value & ~(alignment - 1)


def count_leading_zeros(value: int, bit_width: int) -> int:
    """
    Count leading zeros in a value
    
    Args:
        value: Value to count leading zeros in
        bit_width: Bit width of the value
    
    Returns:
        Number of leading zeros
        
    Raises:
        ValueError: If inputs are invalid
    """
    if not isinstance(value, int) or not isinstance(bit_width, int):
        raise ValueError("Value and bit_width must be integers")
    if bit_width <= 0:
        raise ValueError("Bit width must be positive")
    if value < 0 or value >= (1 << bit_width):
        raise ValueError(f"Value {value} doesn't fit in {bit_width} bits")
    
    if value == 0:
        return bit_width
    
    count = 0
    mask = 1 << (bit_width - 1)
    while mask > 0 and (value & mask) == 0:
        count += 1
        mask >>= 1
    return count


def count_trailing_zeros(value: int) -> int:
    """
    Count trailing zeros in a value
    
    Args:
        value: Value to count trailing zeros in

    Returns:
        Number of trailing zeros
        
    Raises:
        ValueError: If value is invalid
    """
    if not isinstance(value, int):
        raise ValueError("Value must be an integer")
    if value < 0:
        raise ValueError("Value must be non-negative")
    
    if value == 0:
        return 32  # Conventional return for zero
    
    count = 0
    while (value & 1) == 0:
        count += 1
        value >>= 1
    return count


def reverse_bits(value: int, bit_width: int) -> int:
    """
    Reverse the bits in a value
    
    Args:
        value: Value to reverse bits in
        bit_width: Bit width of the value
    
    Returns:
        Value with bits reversed
    """
    result = 0
    for i in range(bit_width):
        if value & (1 << i):
            result |= (1 << (bit_width - 1 - i))
    return result


def bytes_to_int(bytes_data: bytes, endianness: Literal["little", "big"] = "little") -> int:
    """
    Convert bytes to integer with specified endianness
    
    Args:
        bytes_data: Bytes to converT
        endianness: Endianness ("little" or "big")
    
    Returns:
        Integer value
    
    Raises:
        ValueError: If endianness is invalid
    """
    if endianness not in ["little", "big"]:
        raise ValueError(f"Invalid endianness: {endianness}")
    
    return int.from_bytes(bytes_data, endianness)


def int_to_bytes(value: int, byte_count: int, endianness: Literal["little", "big"] = "little") -> bytes:
    """
    Convert integer to bytes with specified endianness
    
    Args:
        value: Integer value to convert
        byte_count: Number of bytes to output
        endianness: Endianness ("little" or "big")
    
    Returns:
        Bytes representation
    
    Raises:
        ValueError: If endianness is invalid or value is too large
    """
    if endianness not in ["little", "big"]:
        raise ValueError(f"Invalid endianness: {endianness}")
    
    max_value = (1 << (byte_count * 8)) - 1
    if value > max_value:
        raise ValueError(f"Value {value} is too large for {byte_count} bytes (max: {max_value})")
    
    return value.to_bytes(byte_count, endianness) 