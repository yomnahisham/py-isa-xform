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
    
    def disassemble(self, machine_code: bytes, start_address: int = 0) -> DisassemblyResult:
        """Disassemble machine code to assembly"""
        instructions = []
        data_sections = {}
        
        # Use ISA default code start if not specified
        if start_address == 0:
            start_address = self.isa_definition.address_space.default_code_start
        
        current_address = start_address
        
        # Process the machine code in instruction-sized chunks
        i = 0
        consecutive_nops = 0
        in_data_section = False
        
        while i < len(machine_code):
            if i + self.instruction_size_bytes > len(machine_code):
                # Remaining bytes are data
                if len(machine_code[i:]) > 0:
                    data_sections[current_address] = machine_code[i:]
                break
            
            # Extract instruction bytes
            instr_bytes = machine_code[i:i + self.instruction_size_bytes]
            
            # Check if this looks like padding (all zeros)
            if all(b == 0 for b in instr_bytes):
                consecutive_nops += 1
                if consecutive_nops >= self.max_consecutive_nops and not in_data_section:
                    # Switch to data mode for large blocks of zeros
                    in_data_section = True
                    data_start = current_address - (consecutive_nops - 1) * self.instruction_size_bytes
                    data_sections[data_start] = b'\x00' * (consecutive_nops * self.instruction_size_bytes)
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
            else:
                # Reset consecutive NOP counter
                consecutive_nops = 0
                in_data_section = False
                
                # Decode the instruction
                try:
                    endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
                    instr_word = bytes_to_int(instr_bytes, endianness)
                    
                    decoded = self._disassemble_instruction(instr_word, instr_bytes, current_address)
                    if decoded:
                        instructions.append(decoded)
                    else:
                        # Unknown instruction, treat as data
                        data_sections[current_address] = instr_bytes
                except Exception as e:
                    # Decoding failed, treat as data
                    data_sections[current_address] = instr_bytes
            
            i += self.instruction_size_bytes
            current_address += self.instruction_size_bytes
        
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
        # For most RISC architectures, opcode is in the upper bits
        if self.isa_definition.instruction_size == 16:
            return extract_bits(instr_word, 15, 12)
        elif self.isa_definition.instruction_size == 32:
            return extract_bits(instr_word, 6, 0)
        else:
            opcode_bits = 4  # Default opcode size
            return extract_bits(instr_word, self.isa_definition.instruction_size - 1, 
                              self.isa_definition.instruction_size - opcode_bits)
    
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
            
            bits = field.get("bits", "")
            field_type = field.get("type", "")
            
            try:
                high, low = parse_bit_range(bits)
                bit_width = high - low + 1
                value = extract_bits(instr_word, high, low)
                
                # Handle signed immediates
                if field.get("signed", False) and (value & (1 << (bit_width - 1))):
                    value = sign_extend(value, bit_width)
                
                field_values[field.get("name", "")] = value
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
        """Decode instruction using simple format"""
        operands = []
        
        # Basic operand extraction for simple formats
        if instruction.format == "R-type":
            # Extract register fields using bit utilities
            rd = extract_bits(instr_word, 11, 8)
            rs1 = extract_bits(instr_word, 7, 4)
            rs2 = extract_bits(instr_word, 3, 0)
            
            if "rd" in instruction.syntax.lower():
                operands.append(f"R{rd}")
            if "rs1" in instruction.syntax.lower():
                operands.append(f"R{rs1}")
            if "rs2" in instruction.syntax.lower():
                operands.append(f"R{rs2}")
                
        elif instruction.format == "I-type":
            # Extract immediate and register fields
            rd = extract_bits(instr_word, 11, 8)
            rs1 = extract_bits(instr_word, 7, 4)
            imm = extract_bits(instr_word, 3, 0)
            
            if "rd" in instruction.syntax.lower():
                operands.append(f"R{rd}")
            if "rs1" in instruction.syntax.lower():
                operands.append(f"R{rs1}")
            if "imm" in instruction.syntax.lower():
                operands.append(f"#{imm}")
                
        elif instruction.format == "J-type":
            # Extract address field
            addr = extract_bits(instr_word, 11, 0)
            symbol = self.symbol_table.get_symbol_at_address(addr)
            if symbol:
                operands.append(symbol.name)
            else:
                operands.append(f"0x{addr:X}")
        
        return DisassembledInstruction(
            address=address,
            machine_code=instr_bytes,
            mnemonic=instruction.mnemonic.upper(),
            operands=operands,
            instruction=instruction
        )
    
    def _format_operands(self, instruction: Instruction, field_values: Dict[str, int]) -> List[str]:
        """Format operands based on instruction syntax and field values"""
        operands = []
        syntax = instruction.syntax.lower()
        
        # Special case: memory ops with offset and base register
        if 'offset' in field_values and 'rs1' in field_values:
            offset = field_values['offset']
            base = field_values['rs1']
            
            # For LD: rd, offset(rs1). For ST: rs2, offset(rs1)
            if instruction.mnemonic.upper() == 'LD' and 'rd' in field_values:
                operands.append(f"R{field_values['rd']}")
            elif instruction.mnemonic.upper() == 'ST' and 'rs2' in field_values:
                operands.append(f"R{field_values['rs2']}")
            
            # Format offset as hex if it's a reasonable size
            if offset > 255:
                offset_str = f"0x{offset:X}"
            else:
                offset_str = str(offset)
            
            operands.append(f"{offset_str}(R{base})")
            return operands
        
        # Special case: custom immediate for CRAZY or similar
        if 'magic' in field_values:
            if 'rd' in field_values:
                operands.append(f"R{field_values['rd']}")
            operands.append(f"#0x{field_values['magic']:X}")
            return operands
        
        # Default: map field names to their values
        for field_name, value in field_values.items():
            if field_name == "rd" and "rd" in syntax:
                operands.append(f"R{value}")
            elif field_name == "rs1" and "rs1" in syntax:
                operands.append(f"R{value}")
            elif field_name == "rs2" and "rs2" in syntax:
                operands.append(f"R{value}")
            elif field_name in ["immediate", "imm"] and ("imm" in syntax or "immediate" in syntax):
                # Format large immediates as hex
                if value > 255:
                    operands.append(f"#0x{value:X}")
                else:
                    operands.append(f"#{value}")
            elif field_name == "address" and "address" in syntax:
                symbol = self.symbol_table.get_symbol_at_address(value)
                if symbol:
                    operands.append(symbol.name)
                else:
                    operands.append(f"0x{value:X}")
        
        return operands
    
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
            for addr, data in sorted(result.data_sections.items()):
                lines.append(f"    {addr:04X}: {' '.join(f'{b:02X}' for b in data)}")
        
        return "\n".join(lines) 