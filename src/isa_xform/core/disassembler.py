"""
Disassembler: Converts machine code back to assembly language
"""

import struct
import sys
from pathlib import Path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
from typing import List, Optional, Dict, Any, Tuple, Union
from dataclasses import dataclass
from .isa_loader import ISADefinition, Instruction
from .symbol_table import SymbolTable
from ..utils.error_handling import DisassemblerError, ErrorLocation
from ..utils.bit_utils import (
    extract_bits, set_bits, sign_extend, parse_bit_range, 
    create_mask, bytes_to_int, int_to_bytes
)



@dataclass
class DisassembledInstruction:
    """Represents a disassembled instruction"""
    address: int
    machine_code: bytes
    mnemonic: str
    operands: List[str]
    instruction: Optional[Instruction] = None
    comment: str = ""


@dataclass
class DisassemblyResult:
    """Complete disassembly result"""
    instructions: List[DisassembledInstruction]
    symbols: Dict[int, str]
    data_sections: Dict[int, bytes]
    entry_point: Optional[int] = None


class Disassembler:
    """Converts machine code to assembly language"""
    
    def __init__(self, isa_definition: ISADefinition, symbol_table: Optional[SymbolTable] = None, 
        max_consecutive_nops: int = 8):
        self.isa_definition = isa_definition
        self.symbol_table = symbol_table or SymbolTable()
        self.instruction_size_bytes = (isa_definition.instruction_size // 8)
        self.max_consecutive_nops = max_consecutive_nops
        
        # Build lookup tables for fast disassembly
        self._build_lookup_tables()
    
    def _build_lookup_tables(self):
        """Build lookup tables for efficient instruction matching"""
        self.opcode_to_instruction = {}
        self.instruction_patterns = []
        
        try:
            for instruction in self.isa_definition.instructions:
                # Extract opcode pattern for quick lookup
                encoding = instruction.encoding
                if isinstance(encoding, dict) and "fields" in encoding:
                    # Modern encoding format with fields
                    opcode_info = self._extract_opcode_from_fields(encoding["fields"])
                    if opcode_info:
                        opcode_value, opcode_mask = opcode_info
                        self.instruction_patterns.append({
                            'instruction': instruction,
                            'opcode': opcode_value,
                            'mask': opcode_mask,
                            'fields': encoding["fields"]
                        })
                elif hasattr(instruction, 'opcode') and instruction.opcode:
                    # Simple opcode format
                    try:
                        opcode_value = int(instruction.opcode, 2) if instruction.opcode else 0
                        self.opcode_to_instruction[opcode_value] = instruction
                    except ValueError as e:
                        # Handle non-binary opcode formats - try other bases
                        try:
                            if instruction.opcode.startswith('0x'):
                                opcode_value = int(instruction.opcode, 16)
                            else:
                                opcode_value = int(instruction.opcode, 10)
                            self.opcode_to_instruction[opcode_value] = instruction
                        except ValueError:
                            # Skip invalid opcodes with warning
                            continue
        except Exception as e:
            raise DisassemblerError(f"Error building lookup tables: {e}")
    
    def _extract_opcode_from_fields(self, fields: List[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
        """Extract opcode pattern (value and mask) from field definitions"""
        pattern_value = 0
        pattern_mask = 0
        
        try:
            for field in fields:
                # Include ALL fixed-value fields (opcode, funct, unused, etc.) in the pattern
                if "value" in field:
                    bits = field.get("bits", "")
                    value = field.get("value", "")
                    
                    if not bits:
                        continue
                    
                    try:
                        high, low = parse_bit_range(bits)
                        bit_width = high - low + 1
                        
                        # Convert value to integer
                        if isinstance(value, str):
                            if value.startswith('0b'):
                                field_value = int(value, 2)
                            elif value.startswith('0x'):
                                field_value = int(value, 16)
                            else:
                                field_value = int(value, 2) if all(c in '01' for c in value) else int(value)
                        else:
                            field_value = int(value)
                        
                        # Validate field value fits in bit width
                        if field_value >= (1 << bit_width):
                            continue  # Skip invalid field values
                        
                        # Create mask and value for this field
                        field_mask = create_mask(bit_width) << low
                        pattern_mask |= field_mask
                        pattern_value |= (field_value << low)
                    except (ValueError, TypeError):
                        # Skip invalid bit ranges or values
                        continue
        except Exception:
            # Return None if parsing fails
            return None
        
        return (pattern_value, pattern_mask) if pattern_mask else None
    
    def disassemble(self, machine_code: bytes, start_address: int = 0, debug: bool = False) -> DisassemblyResult:
        """Disassemble machine code to assembly"""
        instructions = []
        data_sections = {}
        
        # Use ISA default code start if not specified
        if start_address is None:
            start_address = self.isa_definition.address_space.default_code_start
        
        if debug:
            print(f"[DEBUG] Starting disassembly at PC=0x{start_address:04X}")
            print(f"[DEBUG] Machine code size: {len(machine_code)} bytes")
            print(f"[DEBUG] Instruction size: {self.instruction_size_bytes} bytes")
            print(f"[DEBUG] ISA: {self.isa_definition.name}")
            print(f"[DEBUG] Endianness: {self.isa_definition.endianness}")
            print("-" * 60)
        
        current_address = start_address
        
        # Process the machine code in instruction-sized chunks
        i = 0
        consecutive_nops = 0
        consecutive_invalid = 0
        in_data_section = False
        last_instruction_was_return = False
        
        # Track data section boundaries more intelligently
        data_start_address = None
        consecutive_valid_instructions = 0
        min_consecutive_for_code = 3  # Need 3 consecutive valid instructions to switch to code mode
        
        while i < len(machine_code):
            if debug:
                print(f"[DEBUG] PC=0x{current_address:04X} | Byte offset={i:04X} | Mode={'DATA' if in_data_section else 'CODE'}")
            
            if i + self.instruction_size_bytes > len(machine_code):
                # Remaining bytes are data
                if len(machine_code[i:]) > 0:
                    data_sections[current_address] = machine_code[i:]
                    if debug:
                        print(f"[DEBUG] PC=0x{current_address:04X} | Remaining {len(machine_code[i:])} bytes as DATA")
                break
            
            # Extract instruction bytes
            instr_bytes = machine_code[i:i + self.instruction_size_bytes]
            
            # Check if this looks like padding (all zeros)
            if all(b == 0 for b in instr_bytes):
                consecutive_nops += 1
                if debug:
                    print(f"[DEBUG] PC=0x{current_address:04X} | NOP detected (consecutive: {consecutive_nops})")
                
                # Only switch to data mode after many consecutive NOPs (more conservative)
                if consecutive_nops >= self.max_consecutive_nops * 3 and not in_data_section:
                    # Switch to data mode for large blocks of zeros
                    in_data_section = True
                    data_start = current_address - (consecutive_nops - 1) * self.instruction_size_bytes
                    data_sections[data_start] = b'\x00' * (consecutive_nops * self.instruction_size_bytes)
                    if debug:
                        print(f"[DEBUG] PC=0x{current_address:04X} | SWITCHING TO DATA MODE (large NOP block)")
                        print(f"[DEBUG] Data section starts at 0x{data_start:04X}")
                    consecutive_nops = 0
                elif not in_data_section:
                    # Still in instruction mode, add as NOP
                    instructions.append(DisassembledInstruction(
                        address=current_address,
                        machine_code=instr_bytes,
                        mnemonic="NOP",
                        operands=[],
                        comment=""
                    ))
                    if debug:
                        print(f"[DEBUG] PC=0x{current_address:04X} | Adding NOP instruction")
            else:
                # Reset consecutive NOP counter
                consecutive_nops = 0
                
                # Decode the instruction
                try:
                    endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
                    instr_word = bytes_to_int(instr_bytes, endianness)
                    
                    decoded = self._disassemble_instruction(instr_word, instr_bytes, current_address)
                    if decoded:
                        consecutive_invalid = 0  # Reset invalid counter on successful decode
                        
                        # Track consecutive valid instructions
                        consecutive_valid_instructions += 1
                        
                        # If we're in data mode, check if we should switch to code mode
                        if in_data_section:
                            if consecutive_valid_instructions >= min_consecutive_for_code:
                                # We've found enough consecutive valid instructions, switch to code mode
                                in_data_section = False
                                consecutive_valid_instructions = 0
                                if debug:
                                    print(f"[DEBUG] PC=0x{current_address:04X} | SWITCHING TO CODE MODE ({min_consecutive_for_code}+ consecutive valid instructions)")
                        else:
                            # We're already in code mode, just continue
                            pass
                        
                        # Add the instruction
                        instructions.append(decoded)
                        
                        if debug:
                            print(f"[DEBUG] PC=0x{current_address:04X} | Decoded: {decoded.mnemonic} {', '.join(decoded.operands)}")
                        
                        # Check if this is a return instruction (JR, RET, etc.)
                        if decoded.mnemonic in ['JR', 'RET', 'JALR'] and 'ra' in decoded.operands:
                            last_instruction_was_return = True
                            if debug:
                                print(f"[DEBUG] PC=0x{current_address:04X} | Return instruction detected")
                        else:
                            last_instruction_was_return = False
                    else:
                        # Unknown instruction - check if we should switch to data mode
                        consecutive_invalid += 1
                        consecutive_valid_instructions = 0  # Reset valid instruction counter
                        
                        if debug:
                            print(f"[DEBUG] PC=0x{current_address:04X} | Unknown instruction: 0x{instr_word:04X} (consecutive invalid: {consecutive_invalid})")
                        
                        # Switch to data mode if:
                        # 1. We just had a return instruction, OR
                        # 2. We have multiple consecutive invalid instructions
                        should_switch_to_data = (
                            last_instruction_was_return or 
                            consecutive_invalid >= 1
                        )
                        
                        if should_switch_to_data and not in_data_section:
                            # Switch to data mode
                            in_data_section = True
                            data_start_address = current_address
                            if debug:
                                print(f"[DEBUG] PC=0x{current_address:04X} | SWITCHING TO DATA MODE (unknown instruction)")
                            # Add the current word to data section
                            if data_start_address not in data_sections:
                                data_sections[data_start_address] = bytearray()
                            data_sections[data_start_address].extend(instr_bytes)
                        elif not in_data_section:
                            # Still try to decode as instruction, but mark as unknown
                            instructions.append(DisassembledInstruction(
                                address=current_address,
                                machine_code=instr_bytes,
                                mnemonic="UNKNOWN",
                                operands=[],
                                comment=f"0x{instr_word:04X}"
                            ))
                            if debug:
                                print(f"[DEBUG] PC=0x{current_address:04X} | Adding UNKNOWN instruction")
                        else:
                            # Already in data mode, add to data section
                            if data_start_address not in data_sections:
                                data_sections[data_start_address] = bytearray()
                            data_sections[data_start_address].extend(instr_bytes)
                            if debug:
                                print(f"[DEBUG] PC=0x{current_address:04X} | Adding to data section: 0x{instr_word:04X}")
                except Exception as e:
                    # Decoding failed - be very conservative
                    consecutive_invalid += 1
                    
                    if debug:
                        print(f"[DEBUG] PC=0x{current_address:04X} | Decode error: {e} (consecutive invalid: {consecutive_invalid})")
                    
                    # Switch to data mode if we just had a return instruction
                    should_switch_to_data = (
                        last_instruction_was_return or 
                        consecutive_invalid >= 1
                    )
                    
                    if should_switch_to_data and not in_data_section:
                        # Switch to data mode
                        in_data_section = True
                        if debug:
                            print(f"[DEBUG] PC=0x{current_address:04X} | SWITCHING TO DATA MODE (decode error)")
                        if current_address not in data_sections:
                            data_sections[current_address] = bytearray()
                        data_sections[current_address].extend(instr_bytes)
                    elif not in_data_section:
                        # Still try to treat as instruction
                        instructions.append(DisassembledInstruction(
                            address=current_address,
                            machine_code=instr_bytes,
                            mnemonic="INVALID",
                            operands=[],
                            comment=f"Decode error: {e}"
                        ))
                        if debug:
                            print(f"[DEBUG] PC=0x{current_address:04X} | Adding INVALID instruction")
                    else:
                        # Already in data mode, add to data section
                        if current_address not in data_sections:
                            data_sections[current_address] = bytearray()
                        data_sections[current_address].extend(instr_bytes)
                        if debug:
                            print(f"[DEBUG] PC=0x{current_address:04X} | Adding to data section (decode error): 0x{bytes_to_int(instr_bytes, 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'):04X}")
            
            i += self.instruction_size_bytes
            current_address += self.instruction_size_bytes
        
        if debug:
            print("-" * 60)
            print(f"[DEBUG] Disassembly complete!")
            print(f"[DEBUG] Total instructions: {len(instructions)}")
            print(f"[DEBUG] Data sections: {len(data_sections)}")
            print(f"[DEBUG] Final PC: 0x{current_address:04X}")
            print(f"[DEBUG] Code range: 0x{start_address:04X} - 0x{current_address-1:04X}")
            if data_sections:
                data_addrs = sorted(data_sections.keys())
                print(f"[DEBUG] Data sections at: {[f'0x{addr:04X}' for addr in data_addrs]}")
            print("-" * 60)
        
        return DisassemblyResult(
            instructions=instructions,
            data_sections=data_sections,
            symbols=self._extract_symbols(instructions)
        )
    
    def _disassemble_instruction(self, instr_word: int, instr_bytes: bytes, address: int) -> Optional[DisassembledInstruction]:
        """Disassemble a single instruction word"""
        # Try pattern matching first (more flexible)
        for pattern in self.instruction_patterns:
            if (instr_word & pattern['mask']) == pattern['opcode']:
                return self._decode_instruction_with_pattern(
                    instr_word, instr_bytes, address, pattern
                )
        
        # Fallback to simple opcode lookup
        opcode = self._extract_simple_opcode(instr_word)
        if opcode in self.opcode_to_instruction:
            instruction = self.opcode_to_instruction[opcode]
            return self._decode_simple_instruction(instr_word, instr_bytes, address, instruction)
        
        return None
    
    def _extract_simple_opcode(self, instr_word: int) -> int:
        """Extract opcode for simple instruction formats"""
        instruction_size = self.isa_definition.instruction_size
        
        # Try to extract opcode from the instruction
        # For most ISAs, opcode is in the upper bits, but the exact size varies
        if instruction_size == 16:
            # For 16-bit instructions, typically 4-bit opcode in upper bits
            return extract_bits(instr_word, 15, 12)
        elif instruction_size == 32:
            # For 32-bit instructions, typically 7-bit opcode in lower bits (RISC-V style)
            return extract_bits(instr_word, 6, 0)
        else:
            # For other sizes, try to extract a reasonable opcode size
            # Assume opcode is in the upper bits with size = instruction_size / 4
            opcode_bits = max(4, instruction_size // 4)
            return extract_bits(instr_word, instruction_size - 1, instruction_size - opcode_bits)
    
    def _decode_instruction_with_pattern(self, instr_word: int, instr_bytes: bytes, address: int, pattern: Dict[str, Any]) -> DisassembledInstruction:
        """Decode instruction using field pattern matching"""
        instruction = pattern['instruction']
        fields = pattern['fields']
        operands = []
        
        # Extract each field from the instruction
        field_values = {}
        for field in fields:
            if field.get("name") == "opcode":
                continue  # Skip opcode field
            
            # Skip fields that have a fixed value (like unused bits)
            if "value" in field and "type" not in field:
                continue
            
            bits = field.get("bits", "")
            field_type = field.get("type", "")
            
            try:
                high, low = parse_bit_range(bits)
                bit_width = high - low + 1
                value = extract_bits(instr_word, high, low)
                
                # Handle signed immediates
                if field.get("signed", False) and (value & (1 << (bit_width - 1))):
                    value = sign_extend(value, bit_width)
                
                field_name = field.get("name", "")
                field_values[field_name] = value
            except ValueError:
                # Skip invalid bit ranges
                continue
        
        # Format operands based on instruction syntax
        operands = self._format_operands(instruction, field_values)
        
        return DisassembledInstruction(
            address=address,
            machine_code=instr_bytes,
            mnemonic=instruction.mnemonic.upper(),
            operands=operands,
            instruction=instruction
        )
    
    def _decode_simple_instruction(self, instr_word: int, instr_bytes: bytes, address: int, instruction: Instruction) -> DisassembledInstruction:
        """Decode instruction using simple field-based approach"""
        # Create fields from instruction format
        fields = self._create_fields_from_format(instruction)
        
        # Extract field values
        field_values = {}
        for field in fields:
            field_name = field["name"]
            bits = field["bits"]
            
            try:
                high, low = parse_bit_range(bits)
                field_value = extract_bits(instr_word, high, low)
                field_values[field_name] = field_value
            except ValueError:
                continue
        
        # Format operands
        operands = self._format_operands(instruction, field_values)
        
        return DisassembledInstruction(
            address=address,
            machine_code=instr_bytes,
            mnemonic=instruction.mnemonic,
            operands=operands,
            instruction=instruction
        )
    
    def _create_fields_from_format(self, instruction: Instruction) -> List[Dict[str, Any]]:
        """Create field definitions from instruction format for decoding"""
        fields = []
        instruction_size = self.isa_definition.instruction_size
        
        # Try to extract opcode from instruction
        opcode = 0
        if hasattr(instruction, 'opcode') and instruction.opcode:
            try:
                opcode = int(instruction.opcode, 2)
            except ValueError:
                opcode = 0
        
        # Create fields based on instruction format
        if instruction.format == "R-type":
            # R-type: opcode | rd | rs1 | rs2
            if instruction_size == 16:
                fields = [
                    {"name": "opcode", "bits": "15:12", "value": opcode},
                    {"name": "rd", "bits": "11:8", "type": "register"},
                    {"name": "rs1", "bits": "7:4", "type": "register"},
                    {"name": "rs2", "bits": "3:0", "type": "register"}
                ]
            else:  # 32-bit
                fields = [
                    {"name": "opcode", "bits": "31:26", "value": opcode},
                    {"name": "rd", "bits": "25:21", "type": "register"},
                    {"name": "rs1", "bits": "20:16", "type": "register"},
                    {"name": "rs2", "bits": "15:11", "type": "register"},
                    {"name": "funct", "bits": "10:0", "value": 0}
                ]
        elif instruction.format == "I-type":
            # I-type: opcode | rd | rs1 | immediate
            if instruction_size == 16:
                fields = [
                    {"name": "opcode", "bits": "15:12", "value": opcode},
                    {"name": "rd", "bits": "11:8", "type": "register"},
                    {"name": "rs1", "bits": "7:4", "type": "register"},
                    {"name": "immediate", "bits": "3:0", "type": "immediate", "signed": True}
                ]
            else:  # 32-bit
                fields = [
                    {"name": "opcode", "bits": "31:26", "value": opcode},
                    {"name": "rd", "bits": "25:21", "type": "register"},
                    {"name": "rs1", "bits": "20:16", "type": "register"},
                    {"name": "immediate", "bits": "15:0", "type": "immediate", "signed": True}
                ]
        elif instruction.format == "J-type":
            # J-type: opcode | address
            if instruction_size == 16:
                fields = [
                    {"name": "opcode", "bits": "15:12", "value": opcode},
                    {"name": "address", "bits": "11:0", "type": "address"}
                ]
            else:  # 32-bit
                fields = [
                    {"name": "opcode", "bits": "31:26", "value": opcode},
                    {"name": "address", "bits": "25:0", "type": "address"}
                ]
        else:
            # Unknown format - create a simple field structure
            fields = [
                {"name": "opcode", "bits": f"{instruction_size-1}:0", "value": opcode}
            ]
        
        return fields
    
    def _format_operands(self, instruction: Instruction, field_values: Dict[str, int]) -> List[str]:
        """Format operands based on instruction syntax order and field values, supporting offset(base) style."""
        operands = []
        assembly_syntax = getattr(self.isa_definition, 'assembly_syntax', None)
        register_prefix = getattr(assembly_syntax, 'register_prefix', '') if assembly_syntax else ''
        immediate_prefix = getattr(assembly_syntax, 'immediate_prefix', '') if assembly_syntax else ''

        # Get operand names from syntax string (e.g., 'LI rd, imm')
        syntax_operands = []
        if hasattr(instruction, 'syntax') and instruction.syntax:
            parts = instruction.syntax.split()
            if len(parts) > 1:
                operand_part = ' '.join(parts[1:])
                syntax_operands = [op.strip() for op in operand_part.split(',')]

        # Reconstruct full immediate for any instruction with multiple immediate fields (contiguous by field width order, works for majority of risc/cicc isas but might fail for scattered immediate fields)
        encoding_fields = getattr(instruction, 'encoding', {}).get('fields', [])
        immediate_fields = [f for f in encoding_fields if f.get('type') == 'immediate' and f.get('name') != 'opcode']
        if len(immediate_fields) > 1:
            # Gather all immediate fields and their widths (use order in encoding)
            field_widths = []
            for f in immediate_fields:
                bits = f.get('bits', '')
                if ':' in bits:
                    high, low = [int(x) for x in bits.split(':')]
                else:
                    high = low = int(bits)
                width = high - low + 1
                field_widths.append((f['name'], width))
            # Use order in encoding
            field_widths = [(f['name'], width) for f, width in zip(immediate_fields, [w for _, w in field_widths])]
            # Reconstruct the full immediate by concatenating field values by width/order
            full_imm = 0
            bit_offset = 0
            for fname, width in field_widths:
                val = field_values.get(fname, 0)
                full_imm |= (val & ((1 << width) - 1)) << bit_offset
                bit_offset += width
            # Now format operands using the reconstructed immediate
            for syntax_op in syntax_operands:
                if syntax_op in ('imm', 'immediate'):
                    operands.append(f"{immediate_prefix}{full_imm}")
                elif syntax_op in ('rd', 'rs1', 'rs2'):
                    reg_val = field_values.get(syntax_op, 0)
                    operands.append(self._format_register(reg_val, register_prefix))
                else:
                    # fallback
                    if syntax_op in field_values:
                        operands.append(str(field_values[syntax_op]))
            return operands

        for syntax_op in syntax_operands:
            # Special handling for offset(base) or imm(base) patterns
            if '(' in syntax_op and syntax_op.endswith(')'):
                # Example: offset(rs1) or imm(rs2)
                before_paren = syntax_op[:syntax_op.index('(')].strip()
                inside_paren = syntax_op[syntax_op.index('(')+1:-1].strip()
                # Map aliases as in the original code
                field_name_imm = before_paren
                field_name_reg = inside_paren
                # Alias resolution for immediate/offset
                if field_name_imm == 'offset' and 'imm' in field_values:
                    field_name_imm = 'imm'
                if field_name_imm not in field_values:
                    if field_name_imm == 'imm' and 'immediate' in field_values:
                        field_name_imm = 'immediate'
                    elif field_name_imm == 'immediate' and 'imm' in field_values:
                        field_name_imm = 'imm'
                # Alias resolution for register
                if field_name_reg not in field_values:
                    if field_name_reg == 'rs1' and 'rd' in field_values:
                        field_name_reg = 'rd'
                    elif field_name_reg == 'rd' and 'rs1' in field_values:
                        field_name_reg = 'rs1'
                # Format
                if field_name_imm in field_values and field_name_reg in field_values:
                    imm_val = field_values[field_name_imm]
                    reg_val = field_values[field_name_reg]
                    # Format immediate
                    if imm_val > 255 or imm_val < -255:
                        imm_str = f"{immediate_prefix}0x{imm_val:X}"
                    else:
                        imm_str = f"{immediate_prefix}{imm_val}"
                    reg_str = self._format_register(reg_val, register_prefix)
                    operands.append(f"{imm_str}({reg_str})")
                else:
                    # Fallback: just output what we can
                    if field_name_imm in field_values:
                        operands.append(str(field_values[field_name_imm]))
                    if field_name_reg in field_values:
                        operands.append(self._format_register(field_values[field_name_reg], register_prefix))
                continue
            # Normal operand (not offset(base))
            field_name = syntax_op
            # Special case: map 'offset' to 'imm' for branch instructions
            if field_name == 'offset' and 'imm' in field_values:
                field_name = 'imm'
            if field_name not in field_values:
                # Try to map aliases (e.g., key->imm, etc.)
                if field_name == 'imm' and 'immediate' in field_values:
                    field_name = 'immediate'
                elif field_name == 'immediate' and 'imm' in field_values:
                    field_name = 'imm'
                elif field_name == 'key' and 'imm' in field_values:
                    field_name = 'imm'
                elif field_name == 'imm' and 'key' in field_values:
                    field_name = 'key'
                elif field_name == 'rd' and 'rs1' in field_values and 'rd' not in field_values:
                    field_name = 'rs1'
                elif field_name == 'rs1' and 'rd' in field_values and 'rs1' not in field_values:
                    field_name = 'rd'
                else:
                    continue
            value = field_values[field_name]
            # Format based on type
            if field_name.startswith('r') or field_name in ('rd', 'rs1', 'rs2'):
                operands.append(self._format_register(value, register_prefix))
            elif field_name in ('immediate', 'imm', 'offset', 'key', 'svc'):
                if value > 255 or value < -255:
                    operands.append(f"{immediate_prefix}0x{value:X}")
                else:
                    operands.append(f"{immediate_prefix}{value}")
            elif field_name == 'address':
                symbol = self.symbol_table.get_symbol_at_address(value)
                if symbol:
                    operands.append(symbol.name)
                else:
                    operands.append(f"0x{value:X}")
            else:
                operands.append(str(value))
        return operands
    
    def _format_register(self, reg_num: int, register_prefix: str) -> str:
        """Format register name using ISA's register configuration"""
        # Look up register name in ISA definition
        for category, registers in self.isa_definition.registers.items():
            if reg_num < len(registers):
                reg = registers[reg_num]
                # Use the register name from ISA definition with proper prefix
                return f"{register_prefix}{reg.name}"
        
        # Fallback to generic name with prefix
        return f"{register_prefix}R{reg_num}"
    
    def _get_register_name(self, reg_num: int) -> str:
        """Get register name from register number"""
        # Look up register name in ISA definition
        for category, registers in self.isa_definition.registers.items():
            if reg_num < len(registers):
                reg = registers[reg_num]
                # Use alias if available, otherwise use full name
                if reg.alias:
                    return reg.alias[0]
                return reg.name
        
        # Fallback to generic name
        return f"R{reg_num}"
    
    def _extract_symbols(self, instructions: List[DisassembledInstruction]) -> Dict[int, str]:
        """Extract potential symbols from disassembled instructions"""
        symbols = {}
        
        for instr in instructions:
            # Look for jump/branch targets
            if instr.instruction and any(keyword in instr.instruction.mnemonic.upper() 
                                       for keyword in ['JMP', 'CALL', 'BEQ', 'BNE', 'JZ', 'JNZ']):
                # Extract target addresses from operands
                for operand in instr.operands:
                    if operand.startswith('0x'):
                        try:
                            addr = int(operand, 16)
                            if addr not in symbols:
                                symbols[addr] = f"L_{addr:04X}"
                        except ValueError:
                            pass
        
        return symbols
    
    def format_disassembly(self, result: DisassemblyResult, include_addresses: bool = True, include_machine_code: bool = False) -> str:
        """Format disassembly result as human-readable assembly"""
        lines = []
        
        # Add header
        lines.append(f"; Disassembly of {self.isa_definition.name} v{self.isa_definition.version}")
        lines.append(f"; Word size: {self.isa_definition.word_size} bits")
        lines.append(f"; Endianness: {self.isa_definition.endianness}")
        lines.append("")
        
        # Sort instructions by address
        sorted_instructions = sorted(result.instructions, key=lambda x: x.address)
        
        for instr in sorted_instructions:
            line_parts = []
            
            # Add address if requested
            if include_addresses:
                line_parts.append(f"{instr.address:04X}:")
            
            # Add machine code if requested
            if include_machine_code:
                machine_code_str = " ".join(f"{b:02X}" for b in instr.machine_code)
                line_parts.append(f"[{machine_code_str}]")
            
            # Check if this address has a symbol
            if instr.address in result.symbols:
                lines.append(f"{result.symbols[instr.address]}:")
            
            # Format instruction
            instr_str = instr.mnemonic
            if instr.operands:
                instr_str += f" {', '.join(instr.operands)}"
            
            line_parts.append(instr_str)
            
            # Add comment if available
            if instr.comment:
                line_parts.append(f"; {instr.comment}")
            
            lines.append("    " + " ".join(line_parts))
        
        # Add data sections
        if result.data_sections:
            lines.append("")
            lines.append("; Data sections:")
            
            # Create a complete data map by analyzing all data sections
            all_data = bytearray()
            data_start = min(result.data_sections.keys())
            data_end = max(addr + len(data) for addr, data in result.data_sections.items())
            
            # Initialize with zeros
            all_data = bytearray(data_end - data_start)
            
            # Fill in the actual data
            for addr, data in result.data_sections.items():
                offset = addr - data_start
                all_data[offset:offset + len(data)] = data
            
            # Now process the complete data region intelligently
            i = 0
            while i < len(all_data):
                # Try to detect ASCII string first
                ascii_start = i
                ascii_length = 0
                is_null_terminated = False
                
                # Look for printable ASCII characters
                while (i + ascii_length < len(all_data) and 
                       ascii_length < 64 and  # Limit string length
                       all_data[i + ascii_length] >= 32 and 
                       all_data[i + ascii_length] <= 126):
                    ascii_length += 1
                
                # Check if string is null-terminated
                if (i + ascii_length < len(all_data) and 
                    all_data[i + ascii_length] == 0):
                    is_null_terminated = True
                    ascii_length += 1  # Include the null terminator
                
                # Output ASCII string if we found one (minimum 2 chars or null-terminated)
                if ascii_length >= 2 or is_null_terminated:
                    ascii_data = all_data[ascii_start:ascii_start + ascii_length]
                    if is_null_terminated:
                        # Remove null terminator for display
                        ascii_str = ascii_data[:-1].decode('ascii', errors='replace')
                        directive = ".asciiz"
                    else:
                        ascii_str = ascii_data.decode('ascii', errors='replace')
                        directive = ".ascii"
                    
                    if include_addresses:
                        lines.append(f"    {data_start + ascii_start:04X}: {directive} \"{ascii_str}\"")
                    else:
                        lines.append(f"    {directive} \"{ascii_str}\"")
                    i += ascii_length
                else:
                    # Not ASCII, check if we can output as word
                    word_size = self.isa_definition.word_size // 8
                    if i + word_size <= len(all_data):
                        # Check if this looks like a word (not just random bytes)
                        chunk = all_data[i:i+word_size]
                        endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
                        value = int.from_bytes(chunk, endianness)
                        
                        # Output as word if it's a reasonable value
                        if include_addresses:
                            lines.append(f"    {data_start + i:04X}: .word 0x{value:04X}")
                        else:
                            lines.append(f"    .word 0x{value:04X}")
                        i += word_size
                    else:
                        # Output remaining bytes as individual bytes
                        chunk = all_data[i:]
                        if len(chunk) == 1:
                            # Single byte
                            hex_byte = f'0x{chunk[0]:02X}'
                            if include_addresses:
                                lines.append(f"    {data_start + i:04X}: .byte {hex_byte}")
                            else:
                                lines.append(f"    .byte {hex_byte}")
                        else:
                            # Multiple bytes
                            hex_bytes = ', '.join(f'0x{b:02X}' for b in chunk)
                            if include_addresses:
                                lines.append(f"    {data_start + i:04X}: .byte {hex_bytes}")
                            else:
                                lines.append(f"    .byte {hex_bytes}")
                        i += len(chunk)
        
        return "\n".join(lines) 