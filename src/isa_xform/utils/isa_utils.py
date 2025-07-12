"""
ISA-aware utility functions for modular operation
"""

from typing import Dict, Any, Optional
from ..core.isa_loader import ISADefinition


def get_word_mask(isa_def: ISADefinition) -> int:
    """Get word size mask from ISA definition"""
    return isa_def.word_mask


def get_sign_bit_mask(isa_def: ISADefinition) -> int:
    """Get sign bit mask from ISA definition"""
    return isa_def.sign_bit_mask


def get_max_signed_value(isa_def: ISADefinition) -> int:
    """Get maximum signed value from ISA definition"""
    return isa_def.max_signed_value


def get_min_signed_value(isa_def: ISADefinition) -> int:
    """Get minimum signed value from ISA definition"""
    return isa_def.min_signed_value


def get_address_mask(isa_def: ISADefinition) -> int:
    """Get address space mask from ISA definition"""
    return isa_def.address_mask


def get_register_count(isa_def: ISADefinition) -> int:
    """Get register count from ISA definition"""
    return isa_def.register_count


def get_immediate_sign_bit(isa_def: ISADefinition, immediate_width: int) -> int:
    """Get sign bit mask for immediate of given width"""
    return isa_def.get_immediate_sign_bit(immediate_width)


def get_immediate_sign_extend(isa_def: ISADefinition, immediate_width: int) -> int:
    """Get sign extension mask for immediate of given width"""
    return isa_def.get_immediate_sign_extend(immediate_width)


def get_shift_type_width(isa_def: ISADefinition) -> int:
    """Get shift type bit width from ISA configuration"""
    return isa_def.get_shift_type_width()


def get_shift_amount_width(isa_def: ISADefinition) -> int:
    """Get shift amount bit width from ISA configuration"""
    return isa_def.get_shift_amount_width()


def get_immediate_width(isa_def: ISADefinition, instruction_type: str) -> int:
    """Get immediate width for instruction type"""
    return isa_def.get_immediate_width(instruction_type)


def get_pc_increment(isa_def: ISADefinition) -> int:
    """Get PC increment value from ISA definition"""
    return isa_def.pc_increment


def get_constant_value(isa_def: ISADefinition, constant_name: str, default: Optional[int] = None) -> int:
    """Get constant value from ISA definition"""
    if constant_name in isa_def.constants:
        return isa_def.constants[constant_name].value
    return default


def format_instruction_implementation(isa_def: ISADefinition, implementation: str) -> str:
    """Replace hardcoded values in instruction implementation with ISA-derived ones"""
    # Replace common hardcoded values with ISA-aware versions
    replacements = {
        '0xFFFF': f'isa_def.word_mask',
        '0x8000': f'isa_def.sign_bit_mask',
        '0xFF80': f'isa_def.get_immediate_sign_extend(7)',
        '0x40': f'isa_def.get_immediate_sign_bit(7)',
        '0xFFE0': f'isa_def.get_immediate_sign_extend(5)',
        '0x20': f'isa_def.get_immediate_sign_bit(5)',
        '0xF': f'(1 << isa_def.get_shift_amount_width()) - 1',
        '0x10000': f'(1 << isa_def.word_size)',
        '0x7FFF': f'isa_def.max_signed_value',
        '-0x8000': f'isa_def.min_signed_value'
    }
    
    result = implementation
    for old_val, new_val in replacements.items():
        result = result.replace(old_val, new_val)
    
    return result


def validate_immediate_range(isa_def: ISADefinition, value: int, immediate_width: int, signed: bool = True) -> bool:
    """Validate immediate value fits within specified bit width"""
    if signed:
        min_val = -(1 << (immediate_width - 1))
        max_val = (1 << (immediate_width - 1)) - 1
    else:
        min_val = 0
        max_val = (1 << immediate_width) - 1
    
    return min_val <= value <= max_val


def get_immediate_range(isa_def: ISADefinition, immediate_width: int, signed: bool = True) -> tuple[int, int]:
    """Get valid range for immediate of given width"""
    if signed:
        min_val = -(1 << (immediate_width - 1))
        max_val = (1 << (immediate_width - 1)) - 1
    else:
        min_val = 0
        max_val = (1 << immediate_width) - 1
    
    return min_val, max_val


def sign_extend_immediate(isa_def: ISADefinition, value: int, immediate_width: int) -> int:
    """Sign extend immediate value to ISA word size"""
    if value & (1 << (immediate_width - 1)):
        # Negative value, extend with 1s
        sign_bits = ((1 << (isa_def.word_size - immediate_width)) - 1) << immediate_width
        return value | sign_bits
    else:
        # Positive value, extend with 0s
        return value & ((1 << immediate_width) - 1)


def mask_to_word_size(isa_def: ISADefinition, value: int) -> int:
    """Mask value to ISA word size"""
    return value & isa_def.word_mask


def is_negative(isa_def: ISADefinition, value: int) -> bool:
    """Check if value is negative according to ISA word size"""
    return (value & isa_def.sign_bit_mask) != 0


def is_zero(isa_def: ISADefinition, value: int) -> bool:
    """Check if value is zero (after masking to word size)"""
    return (value & isa_def.word_mask) == 0


def get_flag_masks(isa_def: ISADefinition) -> Dict[str, int]:
    """Get flag masks for ISA word size"""
    return {
        'Z': 0,  # Zero flag is always 0 when result is 0
        'N': isa_def.sign_bit_mask,  # Negative flag uses sign bit
        'C': 1 << isa_def.word_size,  # Carry flag is bit beyond word size
        'V': 1 << (isa_def.word_size + 1)  # Overflow flag is bit beyond word size + 1
    } 


def format_signed_immediate(value: int, bit_width: int) -> str:
    """Format a signed immediate value for display, given its bit width."""
    if bit_width <= 0:
        return str(value)
    sign_bit = 1 << (bit_width - 1)
    mask = (1 << bit_width) - 1
    value_masked = value & mask
    if value_masked & sign_bit:
        signed_value = value_masked - (1 << bit_width)
        return str(signed_value)
    else:
        return str(value_masked) 