"""
Disassembler: Converts machine code back to assembly language
"""

import struct
from typing import List, Optional, Dict, Any, Tuple, Union
from dataclasses import dataclass
from .isa_loader import ISADefinition, Instruction
from .symbol_table import SymbolTable, SymbolType
from ..utils.error_handling import DisassemblerError, ErrorLocation
from ..utils.bit_utils import (
    extract_bits, set_bits, sign_extend, parse_bit_range, 
    create_mask, bytes_to_int, int_to_bytes
)
from ..utils.isa_utils import (
    get_word_mask, get_sign_bit_mask, get_immediate_sign_bit, 
    get_immediate_sign_extend, get_shift_type_width, get_shift_amount_width,
    get_immediate_width, get_address_mask, get_register_count, format_signed_immediate
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
    label_map: Optional[Dict[int, str]] = None  # Map addresses to label names


class Disassembler:
    """Converts machine code to assembly language"""
    
    def __init__(self, isa_definition: ISADefinition, symbol_table: Optional[SymbolTable] = None, 
        max_consecutive_nops: int = 8):
        self.isa_definition = isa_definition
        self.symbol_table = symbol_table or SymbolTable()
        self.instruction_size_bytes = isa_definition.instruction_size // 8
        self.max_consecutive_nops = max_consecutive_nops
        
        # Calculate address space mask from ISA definition using ISA-aware utilities
        self.address_mask = get_address_mask(isa_definition)
        
        # Build lookup tables for fast disassembly
        self._build_lookup_tables()
        
        # Initialize label map for address-to-label resolution
        self.label_map = {}
    
    def _build_lookup_tables(self):
        """Build lookup tables for efficient instruction matching"""
        self.opcode_to_instruction = {}
        self.instruction_patterns = []
        
        # Build pseudo-instruction patterns for reconstruction
        self.pseudo_patterns = {}
        self.control_flow_instructions = set()
        self.branch_instructions = set()
        self.jump_instructions = set()
        self.relative_branch_instructions = set()
        
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
                
                # Categorize control flow instructions
                mnemonic = instruction.mnemonic.upper()
                if self._is_jump_instruction(mnemonic):
                    self.jump_instructions.add(mnemonic)
                    self.control_flow_instructions.add(mnemonic)
                elif self._is_control_flow_instruction(mnemonic):
                    self.branch_instructions.add(mnemonic)
                    self.control_flow_instructions.add(mnemonic)
                    self.relative_branch_instructions.add(mnemonic)
            
            # Build pseudo-instruction patterns from ISA definition
            self._build_pseudo_patterns()
            
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
    
    def _build_pseudo_patterns(self):
        """Build patterns for pseudo-instruction reconstruction from ISA definition"""
        if not hasattr(self.isa_definition, 'pseudo_instructions'):
            return
        
        for pseudo in self.isa_definition.pseudo_instructions:
            if not hasattr(pseudo, 'expansion') or not pseudo.expansion:
                continue
            
            # Skip multi-instruction pseudo-instructions - they're handled separately
            disassembly_config = getattr(pseudo, 'disassembly', {})
            if disassembly_config.get('reconstruction_type') == 'multi_instruction':
                continue
            
            # Parse the expansion to understand the pattern
            expansion_lines = pseudo.expansion.strip().split('\n')
            if not expansion_lines:
                continue
            
            # Get the first instruction from the expansion
            first_line = expansion_lines[0].strip()
            if not first_line:
                continue
            
            # Parse the first instruction to understand the pattern
            # Split by spaces, then clean up commas and semicolons
            parts = first_line.split()
            if len(parts) < 2:
                continue
            
            # Clean up parts by removing trailing commas and semicolons
            cleaned_parts = []
            for part in parts:
                cleaned_part = part.rstrip(',;')
                if cleaned_part:  # Only add non-empty parts
                    cleaned_parts.append(cleaned_part)
            
            first_mnemonic = cleaned_parts[0].upper()
            
            # Build pattern for this pseudo-instruction
            if first_mnemonic not in self.pseudo_patterns:
                self.pseudo_patterns[first_mnemonic] = []
            
            pattern = {
                'pseudo_mnemonic': pseudo.mnemonic,
                'expansion': pseudo.expansion,
                'syntax': getattr(pseudo, 'syntax', ''),
                'conditions': []
            }
            
            # Add conditions based on the expansion pattern
            # For example, NOP: ADD x0, x0
            if len(cleaned_parts) >= 3:
                rd = cleaned_parts[1]
                rs2 = cleaned_parts[2] if len(cleaned_parts) > 2 else None
                
                # Parse register numbers
                if rd.startswith('x'):
                    try:
                        rd_num = int(rd[1:])
                        pattern['conditions'].append(('rd', rd_num))
                    except ValueError:
                        pass
                
                if rs2 and rs2.startswith('x'):
                    try:
                        rs2_num = int(rs2[1:])
                        pattern['conditions'].append(('rs2', rs2_num))
                    except ValueError:
                        pass
                
                # Handle special cases like x0
                if rd == 'x0':
                    pattern['conditions'].append(('rd', 0))
                elif rs2 == 'x0':
                    pattern['conditions'].append(('rs2', 0))
            
            # Add conditions for immediate values
            # For example, INC: ADDI rd, 1
            if len(cleaned_parts) >= 3:
                # Check if the last part is a number (immediate)
                try:
                    imm_value = int(cleaned_parts[-1])
                    pattern['conditions'].append(('imm', imm_value))
                except ValueError:
                    # Not a number, skip
                    pass
            
            self.pseudo_patterns[first_mnemonic].append(pattern)
    
    def _build_label_map_from_symbols(self, instructions: List[DisassembledInstruction]) -> Dict[int, str]:
        """Build a map of addresses to label names from disassembled instructions"""
        # Standard disassemblers don't create auto-labels - only use symbols from symbol table
        label_map = {}
        
        # Only add labels that exist in the symbol table
        if hasattr(self, 'symbol_table') and self.symbol_table:
            for symbol in self.symbol_table.symbols.values():
                if symbol.defined and symbol.type == SymbolType.LABEL:
                    label_map[symbol.value] = symbol.name
        
        return label_map
    
    def _resolve_address_to_label(self, address: int) -> str:
        """Resolve an address to a label name"""
        # Use labels from the label map (loaded from symbol table in binary)
        if hasattr(self, 'label_map') and self.label_map and address in self.label_map:
            print(f"[DEBUG] Resolved address 0x{address:X} to label: {self.label_map[address]}")
            return self.label_map[address]
        # Always return hex address for standard disassembler behavior
        print(f"[DEBUG] No label found for address 0x{address:X}, returning hex")
        return f"0x{address:X}"
    
    def _detect_ascii_strings(self, data_bytes: bytes, start_addr: int) -> List[Tuple[int, int, str]]:
        """Detect ASCII strings in data bytes based on ISA definition"""
        strings = []
        i = 0
        
        # Get word size and endianness from ISA definition
        word_size_bytes = self.isa_definition.word_size // 8
        endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
        
        # Get printable character range from ISA definition, with fallback to standard ASCII
        ascii_config = getattr(self.isa_definition, 'ascii_config', {})
        printable_min = ascii_config.get('printable_min', 32)  # Space
        printable_max = ascii_config.get('printable_max', 126)  # Tilde
        min_string_length = ascii_config.get('min_string_length', 2)
        
        while i < len(data_bytes):
            # Look for printable character sequence based on ISA definition
            if i < len(data_bytes) and printable_min <= data_bytes[i] <= printable_max:
                # Found printable character, look for more
                string_start = i
                string_chars = []
                
                while i < len(data_bytes) and printable_min <= data_bytes[i] <= printable_max:
                    string_chars.append(chr(data_bytes[i]))
                    i += 1
                
                if len(string_chars) >= min_string_length:
                    strings.append((start_addr + string_start, len(string_chars), ''.join(string_chars)))
            else:
                i += 1
        
        return strings
    
    def disassemble(self, machine_code: bytes, start_address: int = 0, debug: bool = False, 
                   data_regions: Optional[List[Tuple[int, int]]] = None, reconstruct_pseudo: bool = True) -> DisassemblyResult:
        """Disassemble machine code to assembly
        
        Args:
            machine_code: The binary data to disassemble
            start_address: Starting address for disassembly (None for ISA default)
            debug: Enable debug output
            data_regions: List of (start_addr, end_addr) tuples specifying data regions
            reconstruct_pseudo: Whether to reconstruct pseudo-instructions
        """
        instructions = []
        data_sections = {}
        
        # Check for ISAX header
        if machine_code[:4] == b'ISAX':
            # Parse header: [magic][version][entry_point][code_start][code_size][data_start][data_size][symbol_size][code][data][symbols]
            version = int.from_bytes(machine_code[4:8], 'little')
            entry_point = int.from_bytes(machine_code[8:12], 'little')
            code_start = int.from_bytes(machine_code[12:16], 'little')
            code_size = int.from_bytes(machine_code[16:20], 'little')
            data_start = int.from_bytes(machine_code[20:24], 'little')
            data_size = int.from_bytes(machine_code[24:28], 'little')
            symbol_size = int.from_bytes(machine_code[28:32], 'little')
            code_bytes = machine_code[32:32+code_size]
            data_bytes = machine_code[32+code_size:32+code_size+data_size]
            symbol_bytes = machine_code[32+code_size+data_size:32+code_size+data_size+symbol_size]
            
            if debug:
                print(f"[DEBUG] ISAX header detected (version {version}):")
                print(f"[DEBUG] Entry point: 0x{entry_point:04X}")
                print(f"[DEBUG] Code start: 0x{code_start:04X}, size: {code_size} bytes")
                print(f"[DEBUG] Data start: 0x{data_start:04X}, size: {data_size} bytes")
                print(f"[DEBUG] Symbol table size: {symbol_size} bytes")
                print(f"[DEBUG] Total binary size: {len(machine_code)} bytes")
                print(f"[DEBUG] Instruction size: {self.instruction_size_bytes} bytes")
                print(f"[DEBUG] ISA: {self.isa_definition.name}")
                print(f"[DEBUG] Endianness: {self.isa_definition.endianness}")
                print("-" * 60)
            
            # Disassemble code section
            code_addr = code_start
            i = 0
            consecutive_unknown = 0
            max_unknown_before_data = 3
            
            while i < len(code_bytes):
                if debug:
                    print(f"[DEBUG] PC=0x{code_addr:04X} | Byte offset={i:04X} | Disassembling instruction")
                
                instr_bytes = code_bytes[i:i+self.instruction_size_bytes]
                if len(instr_bytes) < self.instruction_size_bytes:
                    if debug:
                        print(f"[DEBUG] PC=0x{code_addr:04X} | Insufficient bytes for instruction, stopping")
                    break
                endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
                instr_word = bytes_to_int(instr_bytes, endianness)
                if debug:
                    print(f"[DEBUG] PC=0x{code_addr:04X} | Raw bytes: {instr_bytes.hex()}, Instruction word: 0x{instr_word:04X}")
                decoded = self._disassemble_instruction(instr_word, instr_bytes, code_addr)
                if decoded:
                    instructions.append(decoded)
                    consecutive_unknown = 0  # Reset counter on successful decode
                    if debug:
                        print(f"[DEBUG] PC=0x{code_addr:04X} | Decoded: {decoded.mnemonic} {', '.join(decoded.operands)}")
                else:
                    consecutive_unknown += 1
                    instructions.append(DisassembledInstruction(
                        address=code_addr,
                        machine_code=instr_bytes,
                        mnemonic="UNKNOWN",
                        operands=[],
                        comment=f"0x{instr_word:04X}"
                    ))
                    if debug:
                        print(f"[DEBUG] PC=0x{code_addr:04X} | Unknown instruction: 0x{instr_word:04X}")
                    
                    # Continue processing all instructions - don't switch to data mode automatically
                    # The disassembler should process all code regardless of unknown instructions
                
                i += self.instruction_size_bytes
                code_addr += self.instruction_size_bytes
            
            # Load symbol table from binary if available
            if symbol_size > 0 and len(symbol_bytes) > 0:
                try:
                    symbol_json = symbol_bytes.decode('utf-8')
                    import json
                    symbol_data = json.loads(symbol_json)
                    
                    # Build enhanced label map from symbol table
                    self.label_map = {}
                    for name, info in symbol_data.items():
                        if info.get('type') == 'label':
                            addr = info['value']
                            self.label_map[addr] = name
                    
                    if debug:
                        print(f"[DEBUG] Loaded {len(symbol_data)} symbols from binary")
                        for name, info in symbol_data.items():
                            print(f"[DEBUG] Symbol: {name} = 0x{info['value']:04X} ({info['type']})")
                        print(f"[DEBUG] Label map: {self.label_map}")
                except Exception as e:
                    if debug:
                        print(f"[DEBUG] Failed to load symbol table: {e}")
                    # Fall back to building label map from instructions
                    self.label_map = self._build_label_map_from_symbols(instructions)
            else:
                # Build label map from instructions
                self.label_map = self._build_label_map_from_symbols(instructions)
            
            # Disassemble data section: store as a single entry at the correct address
            data_addr = data_start
            if len(data_bytes) > 0:
                data_sections[data_addr] = data_bytes
                if debug:
                    print(f"[DEBUG] Data section at 0x{data_addr:04X}, size: {len(data_bytes)} bytes")
                    print(f"[DEBUG] Data bytes: {' '.join(f'{b:02X}' for b in data_bytes)}")
            else:
                if debug:
                    print(f"[DEBUG] No data section found")
            
            return DisassemblyResult(
                instructions=instructions,
                symbols=self._extract_symbols(instructions),
                data_sections=data_sections,
                entry_point=entry_point,
                label_map=self.label_map
            )
        
        # Use ISA default code start if not specified
        if start_address is None:
            start_address = self.isa_definition.address_space.default_code_start
        
        # Helper function to check if address is in a data region
        def is_in_data_region(addr: int) -> bool:
            if not data_regions:
                return False
            for start, end in data_regions:
                if start <= addr < end:
                    return True
            return False
        
        # Helper function to get automatic data regions based on ISA
        def get_automatic_data_regions() -> List[Tuple[int, int]]:
            """Get data regions based on ISA memory layout"""
            auto_regions = []
            
            # Check if ISA has address space definition
            if hasattr(self.isa_definition, 'address_space') and self.isa_definition.address_space:
                addr_space = self.isa_definition.address_space
                memory_layout = addr_space.memory_layout
                
                # For compact binaries, we need to detect if this is a full address space binary
                # or a compact binary. If the binary size is much smaller than the address space,
                # assume it's a compact binary and don't use absolute ISA addresses
                # Use ISA-derived address space size
                address_space_size = 1 << self.isa_definition.instruction_architecture.get('address_bits', 16)
                is_compact_binary = len(machine_code) < address_space_size // 10  # Heuristic: if binary is < 10% of address space
                
                if is_compact_binary:
                    # For compact binaries, use intelligent detection based on content
                    # Don't use absolute ISA addresses since the binary is compact
                    if debug:
                        print(f"[DEBUG] Detected compact binary ({len(machine_code)} bytes), using intelligent data detection")
                    return []
                else:
                    # For full address space binaries, use ISA-defined regions
                    # Add interrupt vectors as data region
                    if 'interrupt_vectors' in memory_layout:
                        vectors = memory_layout['interrupt_vectors']
                        if 'start' in vectors and 'end' in vectors:
                            auto_regions.append((vectors['start'], vectors['end'] + 1))
                    
                    # Add data section as data region
                    if 'data_section' in memory_layout:
                        data_sect = memory_layout['data_section']
                        if 'start' in data_sect and 'end' in data_sect:
                            auto_regions.append((data_sect['start'], data_sect['end'] + 1))
                    
                    # Add MMIO as data region
                    if 'mmio' in memory_layout:
                        mmio = memory_layout['mmio']
                        if 'start' in mmio and 'end' in mmio:
                            auto_regions.append((mmio['start'], mmio['end'] + 1))
            
            return auto_regions
        
        # If no user-specified data regions, use automatic detection
        if data_regions is None:
            auto_regions = get_automatic_data_regions()
            if auto_regions:
                data_regions = auto_regions
                if debug:
                    print(f"[DEBUG] Using automatic data regions: {auto_regions}")
        
        if debug:
            print(f"[DEBUG] Starting disassembly at PC=0x{start_address:04X}")
            print(f"[DEBUG] Machine code size: {len(machine_code)} bytes")
            print(f"[DEBUG] Instruction size: {self.instruction_size_bytes} bytes")
            print(f"[DEBUG] ISA: {self.isa_definition.name}")
            print(f"[DEBUG] Endianness: {self.isa_definition.endianness}")
            print("-" * 60)
        
        current_address = start_address
        
        # Calculate the byte offset to start reading from
        # The machine code in the binary is placed at the correct addresses,
        # so we need to start reading from the entry point offset
        start_byte_offset = start_address
        
        # Process the machine code in instruction-sized chunks
        i = start_byte_offset
        consecutive_nops = 0
        consecutive_invalid = 0
        in_data_section = False
        last_instruction_was_return = False
        
        # Track data section boundaries more intelligently
        data_start_address = None
        consecutive_valid_instructions = 0
        min_consecutive_for_code = 3  # Need 3 consecutive valid instructions to switch to code mode
        
        # More aggressive data detection for compact binaries
        max_nops_before_data = 4  # Reduced from 8 to 4 for more aggressive detection
        
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
            
            # Check if current address is in a user-specified data region
            if is_in_data_region(current_address):
                if not in_data_section:
                    in_data_section = True
                    data_start_address = current_address
                    if debug:
                        print(f"[DEBUG] PC=0x{current_address:04X} | ENTERING USER-SPECIFIED DATA REGION")
                
                # Add bytes to data section
                if data_start_address not in data_sections:
                    data_sections[data_start_address] = bytearray()
                data_sections[data_start_address].extend(machine_code[i:i + self.instruction_size_bytes])
                
                if debug:
                    print(f"[DEBUG] PC=0x{current_address:04X} | Adding to data section (user-specified)")
                
                i += self.instruction_size_bytes
                current_address += self.instruction_size_bytes
                continue
            
            # Check if we're exiting a data region
            if in_data_section and not is_in_data_region(current_address):
                in_data_section = False
                consecutive_valid_instructions = 0
                if debug:
                    print(f"[DEBUG] PC=0x{current_address:04X} | EXITING DATA REGION, SWITCHING TO CODE MODE")
            
            # Only emit instructions if not in a data region
            if not in_data_section:
                # Extract instruction bytes
                instr_bytes = machine_code[i:i + self.instruction_size_bytes]
                
                # Check if this looks like padding (all zeros)
                if all(b == 0 for b in instr_bytes):
                    consecutive_nops += 1
                    if debug:
                        print(f"[DEBUG] PC=0x{current_address:04X} | NOP detected (consecutive: {consecutive_nops})")
                    
                    # Always add as NOP instruction - don't switch to data mode automatically
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
                            
                            # Check if this is a return instruction
                            if decoded.instruction and 'RET' in decoded.instruction.mnemonic.upper():
                                last_instruction_was_return = True
                            
                            instructions.append(decoded)
                            if debug:
                                print(f"[DEBUG] PC=0x{current_address:04X} | Decoded: {decoded.mnemonic} {', '.join(decoded.operands)}")
                        else:
                            consecutive_invalid += 1
                            consecutive_valid_instructions = 0
                            
                            # Add as unknown instruction - don't switch to data mode automatically
                            # Let the disassembler continue processing all instructions
                            instructions.append(DisassembledInstruction(
                                address=current_address,
                                machine_code=instr_bytes,
                                mnemonic="UNKNOWN",
                                operands=[],
                                comment=f"0x{instr_word:04X}"
                            ))
                            if debug:
                                print(f"[DEBUG] PC=0x{current_address:04X} | Unknown instruction: 0x{instr_word:04X}")
                    except Exception as e:
                        consecutive_invalid += 1
                        consecutive_valid_instructions = 0
                        
                        if debug:
                            print(f"[DEBUG] PC=0x{current_address:04X} | Error decoding: {e}")
                        
                        # If we've seen too many errors in a row, switch to data mode
                        if consecutive_invalid >= 3 and not in_data_section:
                            in_data_section = True
                            data_start = current_address - (consecutive_invalid - 1) * self.instruction_size_bytes
                            data_sections[data_start] = machine_code[i - (consecutive_invalid - 1) * self.instruction_size_bytes:i + self.instruction_size_bytes]
                            if debug:
                                print(f"[DEBUG] PC=0x{current_address:04X} | SWITCHING TO DATA MODE (decoding errors)")
                                print(f"[DEBUG] Data section starts at 0x{data_start:04X}")
                            consecutive_invalid = 0
                        else:
                            # Add as unknown instruction
                            instructions.append(DisassembledInstruction(
                                address=current_address,
                                machine_code=instr_bytes,
                                mnemonic="UNKNOWN",
                                operands=[],
                                comment=f"Error: {e}"
                            ))
            else:
                # We're in a data section, add bytes to data
                if data_start_address not in data_sections:
                    data_sections[data_start_address] = bytearray()
                data_sections[data_start_address].extend(machine_code[i:i + self.instruction_size_bytes])
                
                if debug:
                    print(f"[DEBUG] PC=0x{current_address:04X} | Adding to data section")
            
            i += self.instruction_size_bytes
            current_address += self.instruction_size_bytes
        
        # Build label map from instructions
        self.label_map = self._build_label_map_from_symbols(instructions)
        
        return DisassemblyResult(
            instructions=instructions,
            symbols=self._extract_symbols(instructions),
            data_sections=data_sections,
            entry_point=start_address,
            label_map=self.label_map
        )
    
    def _disassemble_instruction(self, instr_word: int, instr_bytes: bytes, address: int) -> Optional[DisassembledInstruction]:
        """Disassemble a single instruction word"""
        # Try pattern matching first (more flexible)
        matched_patterns = []
        
        # First pass: collect all matching patterns
        for pattern in self.instruction_patterns:
            if (instr_word & pattern['mask']) == pattern['opcode']:
                matched_patterns.append(pattern)
        
        # Second pass: handle special cases and select the best match
        for pattern in matched_patterns:
            instruction = pattern['instruction']
            
            # Special handling for shift instructions that share func3 but differ by shift_type
            if instruction.mnemonic in ['SLLI', 'SRLI', 'SRAI']:
                # Check if this is actually the correct shift instruction based on shift_type
                shift_type = self._extract_shift_type(instr_word, pattern['fields'])
                expected_shift_type = self._get_expected_shift_type(instruction)
                if shift_type == expected_shift_type:
                    return self._decode_instruction_with_pattern(
                        instr_word, instr_bytes, address, pattern
                    )
            else:
                # For non-shift instructions, use the first match
                return self._decode_instruction_with_pattern(
                    instr_word, instr_bytes, address, pattern
                )
        
        # Fallback to simple opcode lookup
        opcode = self._extract_simple_opcode(instr_word)
        if opcode in self.opcode_to_instruction:
            instruction = self.opcode_to_instruction[opcode]
            return self._decode_simple_instruction(instr_word, instr_bytes, address, instruction)
        
        return None
    
    def _extract_shift_type(self, instr_word: int, fields: List[Dict[str, Any]]) -> Optional[int]:
        """Extract shift type from instruction word for any field with shift_type property (modular, ISA-driven)"""
        for field in fields:
            if field.get("name") and field.get("shift_type") is not None:
                bits = field.get("bits", "")
                shift_type_str = field.get("shift_type", "")
                if bits:
                    try:
                        high, low = parse_bit_range(bits)
                        imm_value = extract_bits(instr_word, high, low)
                        # The shift_type is embedded in the immediate field
                        # Use ISA-derived shift configuration
                        shift_type_width = get_shift_type_width(self.isa_definition)
                        shift_amount_width = get_shift_amount_width(self.isa_definition)
                        shift_type_mask = (1 << shift_type_width) - 1
                        # Extract shift_type from the upper bits of the immediate
                        shift_type = (imm_value >> shift_amount_width) & shift_type_mask
                        print(f"[DEBUG] Modular shift_type extraction: instr_word=0x{instr_word:04X}, field={field.get('name')}, imm_value={imm_value}, shift_type_width={shift_type_width}, shift_type={shift_type}")
                        return shift_type
                    except ValueError:
                        continue
        return None
    
    def _get_expected_shift_type(self, instruction: Instruction) -> Optional[int]:
        """Get the expected shift type for a shift instruction"""
        if not hasattr(instruction, 'encoding') or not isinstance(instruction.encoding, dict):
            return None
        
        fields = instruction.encoding.get('fields', [])
        for field in fields:
            if field.get("name") == "imm" and "shift_type" in field:
                shift_type_str = field.get("shift_type", "")
                try:
                    expected = int(shift_type_str, 2)
                    print(f"[DEBUG] Expected shift type for {instruction.mnemonic}: {shift_type_str} = {expected}")
                    return expected
                except ValueError:
                    continue
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
        """Decode instruction using pattern-based approach"""
        instruction = pattern['instruction']
        # Create a temporary DisassembledInstruction to use _extract_field_values
        temp_instr = DisassembledInstruction(
            address=address,
            machine_code=instr_bytes,
            mnemonic=instruction.mnemonic,
            operands=[],
            instruction=instruction
        )
        
        # Use modular field extraction to get all field values including _raw
        field_values = self._extract_field_values(temp_instr)
        
        # Format operands based on instruction syntax
        operands = self._format_operands(instruction, field_values, address, instr_word)
        
        return DisassembledInstruction(
            address=address,
            machine_code=instr_bytes,
            mnemonic=instruction.mnemonic.upper(),
            operands=operands,
            instruction=instruction
        )
    
    def _decode_simple_instruction(self, instr_word: int, instr_bytes: bytes, address: int, instruction: Instruction) -> DisassembledInstruction:
        """Decode instruction using simple field-based approach"""
        # Create a temporary DisassembledInstruction to use _extract_field_values
        temp_instr = DisassembledInstruction(
            address=address,
            machine_code=instr_bytes,
            mnemonic=instruction.mnemonic,
            operands=[],
            instruction=instruction
        )
        
        # Use modular field extraction to get all field values including _raw
        field_values = self._extract_field_values(temp_instr)
        
        # Format operands
        operands = self._format_operands(instruction, field_values, address, instr_word)
        
        return DisassembledInstruction(
            address=address,
            machine_code=instr_bytes,
            mnemonic=instruction.mnemonic,
            operands=operands,
            instruction=instruction
        )
    
    def _create_fields_from_format(self, instruction: Instruction) -> List[Dict[str, Any]]:
        """Create field definitions from instruction format for decoding"""
        # If the instruction has a specific encoding defined, use that instead of generic format
        if hasattr(instruction, 'encoding') and isinstance(instruction.encoding, dict) and 'fields' in instruction.encoding:
            return instruction.encoding['fields']
        
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
    
    def _format_operands(self, instruction: Instruction, field_values: Dict[str, int], address: int, instr_word: int = 0) -> List[str]:
        """Format operands based on instruction syntax order and field values, supporting offset(base) style."""
        operands = []
        
        # Get operand formatting config from ISA
        op_config = getattr(self.isa_definition, 'operand_formatting', {})
        immediate_prefix = op_config.get('immediate_prefix', '#')
        hex_prefix = op_config.get('hex_prefix', '0x')
        binary_prefix = op_config.get('binary_prefix', '0b')
        register_prefix = op_config.get('register_prefix', 'x')
        address_format = op_config.get('address_format', '0x{addr:X}')
        immediate_format = op_config.get('immediate_format', '{value}')
        register_format = op_config.get('register_format', 'x{reg}')
        separators = op_config.get('separators', {})
        operand_sep = separators.get('operand', ', ')
        address_open = separators.get('address', '(')
        address_close = separators.get('address_close', ')')
        
        # Fallback to assembly_syntax for backward compatibility
        assembly_syntax = getattr(self.isa_definition, 'assembly_syntax', None)
        if not immediate_prefix and assembly_syntax:
            immediate_prefix = getattr(assembly_syntax, 'immediate_prefix', '#')
        if not register_prefix and assembly_syntax:
            register_prefix = getattr(assembly_syntax, 'register_prefix', 'x')

        # Get operand names from syntax string (e.g., 'LI rd, imm')
        syntax_operands = []
        if hasattr(instruction, 'syntax') and instruction.syntax:
            parts = instruction.syntax.split()
            if len(parts) > 1:
                operand_part = ' '.join(parts[1:])
                # Handle load/store instructions with offset(base) syntax
                if '(' in operand_part and ')' in operand_part:
                    # Split by comma, but preserve the offset(base) part
                    operands_split = operand_part.split(',')
                    for op in operands_split:
                        op = op.strip()
                        if '(' in op and ')' in op:
                            # This is offset(base) format
                            syntax_operands.append(op)
                        else:
                            # This is a simple operand
                            syntax_operands.append(op)
                else:
                    syntax_operands = [op.strip() for op in operand_part.split(',')]

        # Check if this is a load/store instruction that needs special handling
        is_load_store = instruction.mnemonic.upper() in ['SB', 'SW', 'LB', 'LW', 'LBU']
        
        # Reconstruct full immediate for any instruction with immediate fields
        encoding_fields = getattr(instruction, 'encoding', {}).get('fields', [])
        immediate_fields = [f for f in encoding_fields if f.get('type') == 'immediate' and f.get('name') != 'opcode']
        
        if len(immediate_fields) >= 1 and not is_load_store:
            # Use the instruction's implementation to reconstruct the full immediate
            # This is fully modular - the ISA definition tells us how to combine fields
            full_imm = self._reconstruct_immediate_from_implementation(instruction, field_values, address, instr_word)
            # For PC-relative jumps/branches, calculate the actual target address
            target_addr = None
            if instruction.mnemonic.upper() in ['JMP', 'J', 'JAL', 'CALL', 'BEQ', 'BNE', 'BZ', 'BNZ', 'BLT', 'BGE', 'BLTU', 'BGEU']:
                # Use ISA-driven PC behavior for jump target calculation - FIXED to match assembler
                pc_config = getattr(self.isa_definition, 'pc_behavior', {})
                pc_offset = pc_config.get('offset_for_jumps', 0)
                
                # Use the SAME calculation as the assembler: target = instruction_address + pc_offset + full_imm
                # This ensures consistency between assembly and disassembly
                target_addr = (address + pc_offset + full_imm) & self.address_mask

            
            for syntax_op in syntax_operands:
                if syntax_op in ('imm', 'immediate', 'offset'):
                    if target_addr is not None:
                        resolved = self._resolve_address_to_label(target_addr)
                        operands.append(resolved)
                    else:
                        # For non-jump instructions, format the immediate normally
                        disassembly_config = op_config.get('disassembly', {})
                        always_hex_for = disassembly_config.get('always_hex_for', [])
                        
                        # Check if this is a signed immediate that should be shown as negative
                        field_signed = False
                        for f in immediate_fields:
                            if f.get('signed', False):
                                field_signed = True
                                break
                        
                        if field_signed and full_imm > (1 << (self.isa_definition.word_size - 1)):
                            # Convert to signed representation
                            signed_value = full_imm - (1 << self.isa_definition.word_size)
                            formatted = f"{immediate_prefix}{signed_value}"
                        elif instruction.mnemonic.upper() in always_hex_for:
                            formatted = f"{immediate_prefix}{hex_prefix}{full_imm:X}"
                        else:
                            formatted = f"{immediate_prefix}{full_imm}"
                        operands.append(formatted)
                elif syntax_op in ('rd', 'rs1', 'rs2'):
                    reg_val = field_values.get(syntax_op, 0)
                    operands.append(self._format_register(reg_val, register_prefix))
                else:
                    if syntax_op in field_values:
                        operands.append(str(field_values[syntax_op]))
            return operands

        for syntax_op in syntax_operands:
            print(f"[DEBUG] Processing syntax_op: {syntax_op}")
            # Special handling for offset(base) or imm(base) patterns
            if '(' in syntax_op and syntax_op.endswith(')'):
                before_paren = syntax_op[:syntax_op.index('(')].strip()
                inside_paren = syntax_op[syntax_op.index('(')+1:-1].strip()
                print(f"[DEBUG] offset(base) pattern: before_paren={before_paren}, inside_paren={inside_paren}")
                # Map aliases as in the original code
                field_name_imm = before_paren
                field_name_reg = inside_paren
                # Alias resolution for immediate/offset
                if field_name_imm == 'offset' and 'imm' in field_values:
                    print(f"[DEBUG] Aliasing 'offset' to 'imm'")
                    field_name_imm = 'imm'
                if field_name_imm not in field_values:
                    if field_name_imm == 'imm' and 'immediate' in field_values:
                        print(f"[DEBUG] Aliasing 'imm' to 'immediate'")
                        field_name_imm = 'immediate'
                    elif field_name_imm == 'immediate' and 'imm' in field_values:
                        print(f"[DEBUG] Aliasing 'immediate' to 'imm'")
                        field_name_imm = 'imm'
                if field_name_reg not in field_values:
                    if field_name_reg == 'rs1' and 'rs1' not in field_values:
                        if 'rs2' in field_values:
                            print(f"[DEBUG] Aliasing 'rs1' to 'rs2'")
                            field_name_reg = 'rs2'
                        elif 'rd' in field_values:
                            print(f"[DEBUG] Aliasing 'rs1' to 'rd'")
                            field_name_reg = 'rd'
                    elif field_name_reg == 'rs2' and 'rs2' not in field_values:
                        if 'rs1' in field_values:
                            print(f"[DEBUG] Aliasing 'rs2' to 'rs1'")
                            field_name_reg = 'rs1'
                        elif 'rd' in field_values:
                            print(f"[DEBUG] Aliasing 'rs2' to 'rd'")
                            field_name_reg = 'rd'
                print(f"[DEBUG] Final field_name_imm={field_name_imm}, field_name_reg={field_name_reg}")
                if field_name_imm in field_values and field_name_reg in field_values:
                    imm_val = field_values[field_name_imm]
                    reg_val = field_values[field_name_reg]
                    print(f"[DEBUG] offset(base) values: imm_val={imm_val}, reg_val={reg_val}")
                    # Format offset for memory operands (no immediate prefix)
                    if field_name_imm + '_raw' in field_values:
                        raw_imm_val = field_values[field_name_imm + '_raw']
                        # Find bit width for this field
                        bit_width = 0
                        encoding_fields = getattr(instruction, 'encoding', {}).get('fields', [])
                        for f in encoding_fields:
                            if f.get('name') == field_name_imm and 'bits' in f:
                                bits = f['bits']
                                if isinstance(bits, str) and ',' in bits:
                                    from isa_xform.utils.bit_utils import parse_multi_field_bits
                                    ranges = parse_multi_field_bits(bits)
                                    bit_width = sum(high - low + 1 for high, low in ranges)
                                elif isinstance(bits, str) and ':' in bits:
                                    high, low = [int(x) for x in bits.split(':')]
                                    bit_width = high - low + 1
                                elif isinstance(bits, str):
                                    bit_width = 1
                        from ..utils.isa_utils import format_signed_immediate
                        imm_str = format_signed_immediate(raw_imm_val, bit_width)
                        print(f"[DEBUG] Called format_signed_immediate({raw_imm_val}, {bit_width}) -> {imm_str}")
                    else:
                        imm_str = f"{imm_val}"
                        print(f"[DEBUG] No raw value, using imm_val={imm_val}")
                    reg_str = self._format_register(reg_val, register_prefix)
                    operands.append(f"{imm_str}{address_open}{reg_str}{address_close}")
                else:
                    print(f"[DEBUG] Could not find both field_name_imm and field_name_reg in field_values")
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
                print(f"[DEBUG] Processing field {field_name} with value {value}")
                # Check if this is a branch/jump target address
                if (self._is_control_flow_instruction(instruction.mnemonic) and 
                    field_name in ('immediate', 'imm', 'offset')):
                    print(f"[DEBUG] Control flow instruction, handling as target address")
                    # Calculate actual target address using ISA-driven PC behavior - FIXED to match assembler
                    pc_config = getattr(self.isa_definition, 'pc_behavior', {})
                    pc_offset = pc_config.get('offset_for_jumps', 0)
                    
                    # Use the SAME calculation as the assembler: target = instruction_address + pc_offset + value
                    # This ensures consistency between assembly and disassembly
                    target_addr = (address + pc_offset + value) & self.address_mask
                    resolved = self._resolve_address_to_label(target_addr)
                    operands.append(resolved)
                else:
                    print(f"[DEBUG] Non-control flow instruction, handling as immediate")
                    # ISA-driven immediate formatting
                    disassembly_config = op_config.get('disassembly', {})
                    immediate_format = disassembly_config.get('immediate_format', 'decimal')
                    hex_threshold = disassembly_config.get('hex_threshold', 255)
                    negative_hex_threshold = disassembly_config.get('negative_hex_threshold', -255)
                    always_decimal_for = disassembly_config.get('always_decimal_for', [])
                    always_hex_for = disassembly_config.get('always_hex_for', [])
                    # Check if this field is signed
                    field_signed = False
                    encoding_fields = getattr(instruction, 'encoding', {}).get('fields', [])
                    for f in encoding_fields:
                        if f.get('name') == field_name and f.get('signed', False):
                            field_signed = True
                            break
                    print(f"[DEBUG] Field {field_name} signed: {field_signed}")
                    # If signed, the value has already been sign-extended in _extract_field_values
                    # Just format it appropriately
                    if field_signed:
                        print(f"[DEBUG] Field is signed, value={value} (already sign-extended)")
                        bit_width = 0
                        for f in encoding_fields:
                            if f.get('name') == field_name and 'bits' in f:
                                bits = f['bits']
                                if isinstance(bits, str) and ',' in bits:
                                    from isa_xform.utils.bit_utils import parse_multi_field_bits
                                    ranges = parse_multi_field_bits(bits)
                                    bit_width = sum(high - low + 1 for high, low in ranges)
                                elif isinstance(bits, str) and ':' in bits:
                                    high, low = [int(x) for x in bits.split(':')]
                                    bit_width = high - low + 1
                                elif isinstance(bits, str):
                                    bit_width = 1
                        raw_value = field_values.get(field_name + '_raw', value)
                        formatted_value = format_signed_immediate(raw_value, bit_width)
                    elif instruction.mnemonic.upper() in always_decimal_for:
                        formatted_value = f"{immediate_prefix}{value}"
                    elif instruction.mnemonic.upper() in always_hex_for:
                        formatted_value = f"{immediate_prefix}{hex_prefix}{value:X}"
                    else:
                        # Get immediate formatting config from ISA
                        imm_config = getattr(self.isa_definition, 'immediate_formatting', {})
                        always_show_signed = imm_config.get('always_show_signed', False)
                        use_decimal_for_small = imm_config.get('use_decimal_for_small', True)
                        hex_threshold = imm_config.get('hex_threshold', 255)
                        if always_show_signed and value > (1 << (self.isa_definition.word_size - 1)):
                            signed_value = value - (1 << self.isa_definition.word_size)
                            formatted_value = f"{immediate_prefix}{signed_value}"
                        elif use_decimal_for_small and value <= hex_threshold:
                            formatted_value = f"{immediate_prefix}{value}"
                        else:
                            formatted_value = f"{immediate_prefix}{hex_prefix}{value:X}"
                    operands.append(formatted_value)
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
        """Format register name using ISA's register configuration, searching all register banks."""
        reg_config = getattr(self.isa_definition, 'register_formatting', {})
        prefer_canonical = reg_config.get('prefer_canonical', False)
        always_use_xn = reg_config.get('always_use_xn', False)
        use_aliases = reg_config.get('aliases', True)
        prefix = reg_config.get('prefix', 'x')
        suffix = reg_config.get('suffix', '')
        case = reg_config.get('case', 'lower')
        alternatives = reg_config.get('alternatives', {})

        # If ISA prefers canonical names or always use xN, return xN format
        if prefer_canonical or always_use_xn:
            return f"{prefix}{reg_num}{suffix}"

        # Search all register banks (general, vector, etc.)
        for category, registers in self.isa_definition.registers.items():
            if reg_num < len(registers):
                reg = registers[reg_num]
                reg_name = reg.name
                # Apply case transformation
                if case == 'upper':
                    reg_name = reg_name.upper()
                elif case == 'lower':
                    reg_name = reg_name.lower()
                # Check for alternative names only if aliases are enabled
                if use_aliases and reg_name in alternatives:
                    alt_names = alternatives[reg_name]
                    if alt_names:
                        reg_name = alt_names[0]
                return f"{reg_name}{suffix}"
        # Fallback to generic name with prefix
        if prefix:
            return f"{prefix}{reg_num}{suffix}"
        else:
            return f"R{reg_num}{suffix}"
    
    def _get_register_name(self, reg_num: int) -> str:
        """Get register name from register number using ISA configuration"""
        # Get register formatting config from ISA
        reg_config = getattr(self.isa_definition, 'register_formatting', {})
        alternatives = reg_config.get('alternatives', {})
        
        # Look up register name in ISA definition
        for category, registers in self.isa_definition.registers.items():
            if reg_num < len(registers):
                reg = registers[reg_num]
                reg_name = reg.name
                
                # Check for alternative names
                if reg_name in alternatives:
                    alt_names = alternatives[reg_name]
                    if alt_names:
                        reg_name = alt_names[0]  # Use first alternative
                
                # The register name from ISA already includes the prefix
                return reg_name
        
        # Fallback to generic name
        return f"R{reg_num}"
    
    def _extract_symbols(self, instructions: List[DisassembledInstruction]) -> Dict[int, str]:
        """Extract potential symbols from disassembled instructions"""
        # Standard disassemblers don't create auto-labels - only use symbols from symbol table
        symbols = {}
        
        # Only add symbols that exist in the symbol table
        if hasattr(self, 'symbol_table') and self.symbol_table:
            for symbol in self.symbol_table.symbols.values():
                if symbol.defined and symbol.type == SymbolType.LABEL:
                    symbols[symbol.value] = symbol.name
        
        return symbols
    
    def format_disassembly(self, result: DisassemblyResult, include_addresses: bool = True, include_machine_code: bool = False, reconstruct_pseudo: bool = True) -> str:
        """Format disassembly result as human-readable assembly"""
        lines = []
        
        # Add header
        lines.append(f"; Disassembly of {self.isa_definition.name} v{self.isa_definition.version}")
        lines.append(f"; Word size: {self.isa_definition.word_size} bits")
        lines.append(f"; Endianness: {self.isa_definition.endianness}")
        lines.append("")
        
        # Sort instructions by address
        sorted_instructions = sorted(result.instructions, key=lambda x: x.address)
        
        # Apply pseudo-instruction reconstruction if enabled
        if reconstruct_pseudo:
            # Check ISA setting for pseudo-instruction reconstruction
            pseudo_config = getattr(self.isa_definition, 'pseudo_instruction_reconstruction', {})
            pseudo_enabled = pseudo_config.get('enabled', True)
            if pseudo_enabled:
                sorted_instructions = self._reconstruct_pseudo_instructions(sorted_instructions)
        
        for instr in sorted_instructions:
            line_parts = []
            
            # Add address if requested
            if include_addresses:
                line_parts.append(f"{instr.address:04X}:")
            
            # Add machine code if requested
            if include_machine_code:
                machine_code_str = " ".join(f"{b:02X}" for b in instr.machine_code)
                line_parts.append(f"[{machine_code_str}]")
            
            # Check if this address has a symbol or label
            label_output = False
            if instr.address in result.symbols:
                lines.append(f"{result.symbols[instr.address]}:")
                label_output = True
            elif result.label_map and instr.address in result.label_map:
                lines.append(f"{result.label_map[instr.address]}:")
                label_output = True
            # Format instruction
            instr_str = instr.mnemonic
            if instr.operands:
                instr_str += f" {', '.join(instr.operands)}"
            line_parts.append(instr_str)
            # Add comment if available
            if instr.comment:
                line_parts.append(f"; {instr.comment}")
            # Always output the instruction line, even if a label was output above
            lines.append("    " + " ".join(line_parts))
        
        # Add data sections with enhanced formatting
        if result.data_sections:
            lines.append("")
            lines.append("; Data sections:")

            # Process each data section
            for addr, data_bytes in sorted(result.data_sections.items()):
                if include_addresses:
                    lines.append(f"    ; Data section at 0x{addr:04X}")
                
                # Check ISA data formatting settings
                data_config = getattr(self.isa_definition, 'data_formatting', {})
                force_word = data_config.get('force_word', False)
                ascii_detection = data_config.get('ascii_detection', True)
                
                # Detect ASCII strings in the data only if not forced to word format
                strings = []
                string_positions = {}
                if not force_word and ascii_detection:
                    strings = self._detect_ascii_strings(data_bytes, addr)
                    string_positions = {pos: (length, text) for pos, length, text in strings}
                
                # Output data with string detection
                i = 0
                word_size = self.isa_definition.word_size // 8
                endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
                
                while i < len(data_bytes):
                    current_pos = addr + i
                    
                    # Check if we're at a string position (only if ASCII detection is enabled)
                    if string_positions and current_pos in string_positions:
                        length, text = string_positions[current_pos]
                        # Get string directive name from ISA definition, with fallback to .ascii
                        string_directive = getattr(self.isa_definition, 'string_directive', '.ascii')
                        if include_addresses:
                            lines.append(f"    {current_pos:04X}: {string_directive} \"{text}\"")
                        else:
                            lines.append(f"    {string_directive} \"{text}\"")
                        i += length
                    elif i + word_size <= len(data_bytes):
                        # Output as word
                        chunk = data_bytes[i:i+word_size]
                        value = int.from_bytes(chunk, endianness)
                        # Get word directive name from ISA definition, with fallback to .word
                        word_directive = getattr(self.isa_definition, 'word_directive', '.word')
                        if include_addresses:
                            lines.append(f"    {current_pos:04X}: {word_directive} 0x{value:04X}")
                        else:
                            lines.append(f"    {word_directive} 0x{value:04X}")
                        i += word_size
                    else:
                        # Output remaining bytes as .byte
                        # Get byte directive name from ISA definition, with fallback to .byte
                        byte_directive = getattr(self.isa_definition, 'byte_directive', '.byte')
                        for j in range(i, len(data_bytes)):
                            b = data_bytes[j]
                            if include_addresses:
                                lines.append(f"    {addr + j:04X}: {byte_directive} 0x{b:02X}")
                            else:
                                lines.append(f"    {byte_directive} 0x{b:02X}")
                        break
        
        return "\n".join(lines)
    
    def _reconstruct_pseudo_instructions(self, instructions: List[DisassembledInstruction]) -> List[DisassembledInstruction]:
        """Reconstruct pseudo-instructions from hardware instructions, modular and ISA-driven."""
        if not self.pseudo_patterns:
            return instructions
        
        reconstructed = []
        pseudo_jump_targets = set()
        i = 0
        while i < len(instructions):
            instr = instructions[i]
            pseudo_mnemonic = self._check_pseudo_pattern(instr, instructions, i)
            # Special handling for LA and other multi-instruction pseudo-instructions
            if pseudo_mnemonic in ['LA', 'LI'] and i + 1 < len(instructions):
                # Try to combine the two instructions' field values using the ISA's implementation
                first = instr
                second = instructions[i + 1]
                # Extract field values from both
                fv1 = self._extract_field_values(first)
                fv2 = self._extract_field_values(second)
                # Merge field values (imm, imm2, etc.)
                field_values = fv1.copy()
                field_values.update(fv2)
                
                # For LA pseudo-instruction, reconstruct the full address
                if pseudo_mnemonic == 'LA':
                    # LA expansion: AUIPC rd, label[15:7]; ADDI rd, label[6:0]
                    # AUIPC: imm = (imm1 << 3) | imm2, then shift left by 7
                    # ADDI: add the lower 7 bits
                    auipc_imm = fv1.get('imm', 0)  # From AUIPC (bits 14:9)
                    auipc_imm2 = fv1.get('imm2', 0)  # From AUIPC (bits 5:3)
                    addi_imm = fv2.get('imm', 0)  # From ADDI (bits 15:7)
                    
                    # Reconstruct AUIPC immediate: (imm << 3) | imm2
                    auipc_full = (auipc_imm << 3) | auipc_imm2
                    # Shift left by 7 as per AUIPC semantics
                    auipc_offset = auipc_full << 7
                    # Add ADDI immediate
                    total_offset = auipc_offset + addi_imm
                    # Add to LA instruction address to get target address
                    full_address = first.address + total_offset
                else:
                    # For other pseudo-instructions, use the instruction's implementation
                    if first.instruction and hasattr(first.instruction, 'implementation'):
                        # Get instruction word from machine code
                        from isa_xform.utils.bit_utils import bytes_to_int
                        endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
                        instr_word = bytes_to_int(first.machine_code, endianness)
                        full_imm = self._reconstruct_immediate_from_implementation(first.instruction, field_values, first.address, instr_word)
                    else:
                        full_imm = 0
                    full_address = full_imm
                
                # Use standard disassembler convention: just the address
                operand_str = f"0x{full_address:X}"
                # Add label info as comment if available
                label_str = self._resolve_address_to_label(full_address)
                if label_str != f"0x{full_address:X}":
                    comment = f"pseudo: {pseudo_mnemonic} ; {label_str}"
                else:
                    comment = f"pseudo: {pseudo_mnemonic}"
                # Use the register from the first instruction
                reg_str = None
                for op in first.operands:
                    if op.startswith('x'):
                        reg_str = op
                        break
                if not reg_str:
                    reg_str = 'x0'
                reconstructed.append(DisassembledInstruction(
                    address=first.address,
                    machine_code=first.machine_code,
                    mnemonic=pseudo_mnemonic,
                    operands=[reg_str, operand_str],
                    instruction=first.instruction,
                    comment=comment
                ))
                i += 2  # Skip the next instruction
                continue
            elif pseudo_mnemonic:
                # Get pseudo-instruction metadata from ISA definition
                pseudo_obj = None
                print(f"[DEBUG] Looking for pseudo-instruction: {pseudo_mnemonic}")
                print(f"[DEBUG] Available pseudo-instructions: {[getattr(p, 'mnemonic', '') for p in getattr(self.isa_definition, 'pseudo_instructions', [])]}")
                for pseudo in getattr(self.isa_definition, 'pseudo_instructions', []):
                    if getattr(pseudo, 'mnemonic', '').upper() == pseudo_mnemonic.upper():
                        pseudo_obj = pseudo
                        print(f"[DEBUG] Found pseudo_obj: {pseudo_obj}")
                        break
                if not pseudo_obj:
                    print(f"[DEBUG] No pseudo_obj found for {pseudo_mnemonic}")
                # Determine operands based on JSON metadata
                operands = self._get_pseudo_operands_for_disassembly(pseudo_mnemonic, pseudo_obj, instr)
                # If this is a jump/call pseudo-instruction, record the computed target address
                if pseudo_obj is not None:
                    disassembly_config = getattr(pseudo_obj, 'disassembly', {})
                    reconstruction_type = disassembly_config.get('reconstruction_type', '')
                    if reconstruction_type in ('jump', 'jump_with_return') and operands:
                        # The first operand is the resolved label or address
                        op = operands[0]
                        # If it's a hex address, convert to int
                        if isinstance(op, str) and op.startswith('0x'):
                            try:
                                pseudo_jump_targets.add(int(op, 16))
                            except Exception:
                                pass
                        # If it's a label, we will resolve it later
                reconstructed.append(DisassembledInstruction(
                    address=instr.address,
                    machine_code=instr.machine_code,
                    mnemonic=pseudo_mnemonic,
                    operands=operands,
                    instruction=instr.instruction,
                    comment=f"pseudo: {pseudo_mnemonic}"
                ))
                if pseudo_mnemonic in ['LA', 'LI'] and i + 1 < len(instructions):
                    i += 1  # Skip the second instruction
            else:
                reconstructed.append(instr)
            i += 1
        # After reconstructing, update the label map with any jump/call targets that match a label in the symbol table
        if hasattr(self, 'label_map') and hasattr(self, 'symbol_table') and self.symbol_table:
            for addr in pseudo_jump_targets:
                symbol = self.symbol_table.get_symbol_at_address(addr)
                if symbol and symbol.name:
                    self.label_map[addr] = symbol.name
        # Rebuild the label map from the reconstructed instructions to ensure all targets are included
        self.label_map = self._build_label_map_from_symbols(reconstructed)
        return reconstructed
    
    def _check_pseudo_pattern(self, instr: DisassembledInstruction, instructions: List[DisassembledInstruction], index: int) -> Optional[str]:
        """Check if an instruction matches a pseudo-instruction pattern"""
        if not instr.instruction:
            return None
        
        mnemonic = instr.instruction.mnemonic.upper()
        
        # First, check if this instruction could be part of a multi-instruction pseudo-instruction
        # by looking at the ISA definition's pseudo-instructions
        for pseudo in getattr(self.isa_definition, 'pseudo_instructions', []):
            disassembly_config = getattr(pseudo, 'disassembly', {})
            if disassembly_config.get('reconstruction_type') == 'multi_instruction':
                instruction_list = disassembly_config.get('instructions', [])
                if mnemonic == instruction_list[0].upper() and len(instruction_list) > 1:
                    # This could be the first instruction of a multi-instruction pseudo
                    # Check if the next instruction matches the second instruction in the sequence
                    if index + 1 < len(instructions):
                        next_instr = instructions[index + 1]
                        if (next_instr.instruction and 
                            next_instr.instruction.mnemonic.upper() == instruction_list[1].upper()):
                            # Check if they use the same register (for LI16, LA, etc.)
                            if self._check_multi_instruction_pseudo(instr, next_instr, pseudo):
                                return pseudo.mnemonic
        
        # Fallback to simple pattern matching for single-instruction pseudo-instructions
        if mnemonic not in self.pseudo_patterns:
            return None
        
        # Extract field values from the instruction
        field_values = self._extract_field_values(instr)
        
        # Check if pseudo-instruction reconstruction is enabled for this ISA
        pseudo_config = getattr(self.isa_definition, 'pseudo_instruction_reconstruction', {})
        pseudo_enabled = pseudo_config.get('enabled', True)
        
        # If pseudo-instruction reconstruction is disabled, don't reconstruct
        if not pseudo_enabled:
            return None
        
        for pattern in self.pseudo_patterns[mnemonic]:
            if self._matches_pseudo_pattern(field_values, pattern):
                # Additional check: for XOR instructions, only reconstruct as CLR if it's actually a clear operation
                # This prevents legitimate XOR operations from being incorrectly reconstructed
                if mnemonic == 'XOR' and pattern['pseudo_mnemonic'] == 'CLR':
                    # Check if this is actually a clear operation (XOR rd, rd)
                    # Extract rd and rs2 from field values
                    rd = field_values.get('rd', -1)
                    rs2 = field_values.get('rs2', -1)
                    # Only reconstruct as CLR if both operands are the same register
                    if rd == rs2 and rd >= 0:
                        return pattern['pseudo_mnemonic']
                    # Otherwise, keep it as XOR (legitimate XOR operation)
                    continue
                return pattern['pseudo_mnemonic']
        
        return None
    
    def _check_multi_instruction_pseudo(self, first_instr: DisassembledInstruction, second_instr: DisassembledInstruction, pseudo: Any) -> bool:
        """Check if two consecutive instructions form a multi-instruction pseudo-instruction"""
        # Extract field values from both instructions
        first_fields = self._extract_field_values(first_instr)
        second_fields = self._extract_field_values(second_instr)
        
        # For LI16, check if both instructions use the same register
        # LI16 expansion: LUI rd, imm[15:9]; ORI rd, imm[8:0]
        if pseudo.mnemonic == 'LI16':
            # Check if both instructions target the same register
            first_rd = first_fields.get('rd', -1)
            second_rd = second_fields.get('rd', -1)
            return first_rd == second_rd
        
        # For LA, check if both instructions use the same register
        # LA expansion: AUIPC rd, label[15:7]; ADDI rd, label[6:0]
        elif pseudo.mnemonic == 'LA':
            # Check if both instructions target the same register
            first_rd = first_fields.get('rd', -1)
            second_rd = second_fields.get('rd', -1)
            return first_rd == second_rd
        
        # Default: assume they form a pseudo-instruction if they're consecutive
        # and match the instruction sequence
        return True
    
    def _extract_field_values(self, instr: DisassembledInstruction) -> Dict[str, int]:
        """Extract field values from a disassembled instruction"""
        field_values = {}
        
        if not instr.instruction or not hasattr(instr.instruction, 'encoding'):
            return field_values
        
        encoding = instr.instruction.encoding
        if not isinstance(encoding, dict) or 'fields' not in encoding:
            return field_values
        
        # Extract field values from the raw instruction bytes using the encoding fields
        endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
        instr_word = bytes_to_int(instr.machine_code, endianness)
        
        for field in encoding['fields']:
            field_name = field.get('name', '')
            if field_name == 'opcode':
                continue  # Skip opcode field
            # Skip fields that have a fixed value
            if 'value' in field and 'type' not in field:
                continue
            bits = field.get('bits', '')
            if not bits:
                continue
            try:
                high, low = parse_bit_range(bits)
                bit_width = high - low + 1
                value = extract_bits(instr_word, high, low)
                field_values[field_name + '_raw'] = value  # Store raw value for display
                # Handle signed immediates
                if field.get("signed", False) and (value & (1 << (bit_width - 1))):
                    from ..utils.isa_utils import sign_extend_immediate
                    value = sign_extend_immediate(self.isa_definition, value, bit_width)
                
                # Handle shift instructions - extract only the shift amount (lower bits)
                if field.get("shift_type") is not None:
                    # For shift instructions, the immediate field contains shift_type + shift_amount
                    # We want to display only the shift_amount (lower bits)
                    shift_type_width = get_shift_type_width(self.isa_definition)
                    shift_amount_width = get_shift_amount_width(self.isa_definition)
                    # Extract only the shift amount (lower bits)
                    shift_amount = value & ((1 << shift_amount_width) - 1)
                    field_values[field_name] = shift_amount
                else:
                    field_values[field_name] = value
            except ValueError:
                continue
        
        return field_values
    
    def _matches_pseudo_pattern(self, field_values: Dict[str, int], pattern: Dict[str, Any]) -> bool:
        """Check if field values match a pseudo-instruction pattern"""
        for field_name, expected_value in pattern['conditions']:
            if field_name not in field_values:
                return False
            if field_values[field_name] != expected_value:
                return False
        return True
    
    def _should_show_pseudo_operands(self, pseudo_mnemonic: str) -> bool:
        """Check if pseudo-instruction should show operands in disassembly based on ISA metadata"""
        # Check ISA metadata first
        for pseudo in getattr(self.isa_definition, 'pseudo_instructions', []):
            if getattr(pseudo, 'mnemonic', '').upper() == pseudo_mnemonic.upper():
                disassembly_config = getattr(pseudo, 'disassembly', {})
                if isinstance(disassembly_config, dict):
                    return not disassembly_config.get('hide_operands', False)
        # Fallback to hardcoded list for backward compatibility
        hardcoded_hide_list = ['CLR', 'RET', 'NOP', 'INC', 'DEC', 'NOT', 'NEG']
        return pseudo_mnemonic.upper() not in [i.upper() for i in hardcoded_hide_list]

    def _get_pseudo_operands_for_disassembly(self, pseudo_mnemonic: str, pseudo_obj, instr: DisassembledInstruction) -> List[str]:
        """Get operands for pseudo-instruction disassembly based on JSON metadata"""
        print(f"[DEBUG] Getting operands for {pseudo_mnemonic}")
        if not pseudo_obj:
            # Fallback: check if operands should be hidden
            should_show_operands = self._should_show_pseudo_operands(pseudo_mnemonic)
            print(f"[DEBUG] No pseudo_obj, should_show_operands={should_show_operands}")
            return instr.operands if should_show_operands else []
        
        disassembly_config = getattr(pseudo_obj, 'disassembly', {})
        print(f"[DEBUG] disassembly_config: {disassembly_config}")
        
        # Check if operands should be completely hidden
        if disassembly_config.get('hide_operands', False):
            print(f"[DEBUG] hide_operands=True, returning []")
            return []
        
        # Check reconstruction type for special handling
        reconstruction_type = disassembly_config.get('reconstruction_type', '')
        print(f"[DEBUG] reconstruction_type: {reconstruction_type}")
        
        if reconstruction_type == 'jump' or reconstruction_type == 'jump_with_return':
            # For jump instructions, show the target address
            # Extract the immediate value and calculate target address
            field_values = self._extract_field_values(instr)
            if instr.instruction and hasattr(instr.instruction, 'implementation'):
                # Get instruction word from machine code
                from isa_xform.utils.bit_utils import bytes_to_int
                endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
                instr_word = bytes_to_int(instr.machine_code, endianness)
                offset = self._reconstruct_immediate_from_implementation(instr.instruction, field_values, instr.address, instr_word)
                
                # Use ISA-driven jump target calculation - FIXED to match assembler
                pc_config = getattr(self.isa_definition, 'pc_behavior', {})
                pc_offset = pc_config.get('offset_for_jumps', 0)
                
                # Use the SAME calculation as the assembler: target = instruction_address + pc_offset + offset
                # This ensures consistency between assembly and disassembly
                target_address = (instr.address + pc_offset + offset) & self.address_mask
                
                print(f"[DEBUG] ISA-driven: pc_offset={pc_offset}, instruction_address=0x{instr.address:X}, offset={offset}, target_address=0x{target_address:X}")
            else:
                # Fallback: try to extract from operands
                target_address = 0
                for operand in instr.operands:
                    if operand.startswith('0x'):
                        try:
                            target_address = int(operand, 16)
                            break
                        except ValueError:
                            pass
            # Always return the hex address for jump/call instructions
            result = [f"0x{target_address:X}"]
            print(f"[DEBUG] Returning jump operands: {result}")
            return result
        
        elif reconstruction_type == 'multi_instruction':
            # For multi-instruction pseudo-instructions, show operands from underlying instruction
            return instr.operands
        
        elif reconstruction_type == 'address_reconstruction':
            # For address reconstruction (like LA), show the reconstructed address
            # This is handled in the special LA/LI case above
            return instr.operands
        
        elif reconstruction_type == 'stack_operation':
            # For stack operations, show the register operand
            # Extract register from operands
            for operand in instr.operands:
                if operand.startswith('x'):
                    return [operand]
            return []
        
        else:
            # Default: check show_operands_in_disassembly setting
            show_ops = disassembly_config.get('show_operands_in_disassembly', [])
            if show_ops:
                # Map operand names to values if possible (future-proofing)
                # For now, return underlying operands
                return instr.operands
            else:
                # Default: no operands
                return []

    def _is_control_flow_instruction(self, mnemonic: str) -> bool:
        """Check if instruction is a control flow instruction (jump/branch)"""
        control_flow_instructions = getattr(self.isa_definition, 'control_flow_instructions', None)
        if control_flow_instructions is not None:
            return mnemonic.upper() in [cf.upper() for cf in control_flow_instructions]
        # Fallback to common control flow instruction patterns
        common_control_flow = [
            'J', 'JAL', 'JALR', 'JMP', 'CALL', 'RET', 'IRET',
            'BEQ', 'BNE', 'BLT', 'BGE', 'BLTU', 'BGEU',
            'BZ', 'BNZ', 'BGT', 'BLE', 'BGTU', 'BLEU'
        ]
        return mnemonic.upper() in common_control_flow

    def _is_jump_instruction(self, mnemonic: str) -> bool:
        """Check if instruction is a jump instruction"""
        jump_instructions = getattr(self.isa_definition, 'jump_instructions', None)
        if jump_instructions is not None:
            return mnemonic.upper() in [j.upper() for j in jump_instructions]
        # Fallback to common jump instruction patterns
        common_jumps = ['J', 'JAL', 'JALR', 'JMP', 'CALL']
        return mnemonic.upper() in common_jumps

    def _reconstruct_immediate_from_implementation(self, instruction: Instruction, field_values: Dict[str, int], address: int, instr_word: int = 0) -> int:
        """Reconstruct the full immediate value from instruction implementation"""
        # For branch instructions, we need to use raw field values, not sign-extended ones
        # because the sign extension should happen after reconstruction
        is_branch = instruction.mnemonic.upper() in ['BEQ', 'BNE', 'BZ', 'BNZ', 'BLT', 'BGE', 'BLTU', 'BGEU']
        
        # If multi-field immediate, reconstruct using ISA-driven logic
        encoding_fields = getattr(instruction, 'encoding', {}).get('fields', [])
        immediate_fields = [f for f in encoding_fields if f.get('type') == 'immediate' and f.get('name') != 'opcode']
        if len(immediate_fields) > 1:
            # ISA-specific handling for LUI and AUIPC
            if instruction.mnemonic in ['LUI', 'AUIPC']:
                # For LUI/AUIPC: imm = (imm1 << 3) | imm2, then shift left by 7
                imm_val = field_values.get('imm', 0)  # 6 bits
                imm2_val = field_values.get('imm2', 0)  # 3 bits
                
                # Reconstruct: (imm << 3) | imm2, then shift left by 7
                combined = (imm_val << 3) | imm2_val
                final_value = combined << 7
                # For disassembly, we want to show the original immediate value that was written in assembly
                # The ISA implementation is: result = (imm << 7) & 0xFFFF
                # But we want to show the original imm value, not the shifted result
                # So we return the combined value (imm), not the shifted value
                return combined
            
            # Use ISA-specific implementation logic by parsing the implementation field
            implementation = getattr(instruction, 'implementation', '')
            
            # Parse the implementation to find immediate reconstruction logic
            # Look for patterns like "imm = (imm1 << 3) | imm2" or similar
            import re
            
            # First, try to find variable assignments to understand the mapping
            # Look for patterns like "imm1 = operands['imm']" or "imm1 = operands['imm']"
            var_mapping = {}
            var_pattern = r'(\w+)\s*=\s*operands\[[\'"]([^\'"]+)[\'"]\]'
            for match in re.finditer(var_pattern, implementation):
                var_name = match.group(1)
                field_name = match.group(2)
                var_mapping[var_name] = field_name
            
            # Common patterns for multi-field immediate reconstruction
            patterns = [
                # Pattern: imm = (imm1 << N) | imm2
                r'imm\s*=\s*\((\w+)\s*<<\s*(\d+)\)\s*\|\s*(\w+)',
                # Pattern: imm = imm1 << N | imm2
                r'imm\s*=\s*(\w+)\s*<<\s*(\d+)\s*\|\s*(\w+)',
                # Pattern: result = (imm1 << N) | imm2
                r'result\s*=\s*\((\w+)\s*<<\s*(\d+)\)\s*\|\s*(\w+)',
                # Pattern: result = imm1 << N | imm2
                r'result\s*=\s*(\w+)\s*<<\s*(\d+)\s*\|\s*(\w+)',
                # Pattern: offset = (imm1 << N) | imm2 (for ZX16 J instruction)
                r'offset\s*=\s*\((\w+)\s*<<\s*(\d+)\)\s*\|\s*(\w+)',
                # Pattern: offset = imm1 << N | imm2 (for ZX16 J instruction)
                r'offset\s*=\s*(\w+)\s*<<\s*(\d+)\s*\|\s*(\w+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, implementation)
                if match:
                    var1_name = match.group(1)
                    shift_amount = int(match.group(2))
                    var2_name = match.group(3)
                    
                    # Map variable names to actual field names
                    field1_name = var_mapping.get(var1_name, var1_name)
                    field2_name = var_mapping.get(var2_name, var2_name)
                    
                    # Get the field values
                    field1_val = field_values.get(field1_name, 0)
                    field2_val = field_values.get(field2_name, 0)
                    
                    # Reconstruct using the ISA's logic: (field1 << shift) | field2
                    combined = (field1_val << shift_amount) | field2_val
                    
                    # Handle sign extension for jump instructions
                    if instruction.mnemonic.upper() in ['J', 'JAL']:
                        # For ZX16, the offset is 9 bits with bit 8 as sign bit
                        if combined & 0x100:  # Bit 8 is set (negative)
                            # Sign extend to 16 bits
                            combined = combined | 0xFF00
                    
                    return combined
            
            # If no pattern matches, fall back to generic field reconstruction
            # Sort fields by their bit position in the instruction
            field_specs = []
            for f in immediate_fields:
                bits = f.get("bits", "")
                if ":" in bits:
                    high, low = [int(x) for x in bits.split(":")]
                else:
                    high = low = int(bits)
                width = high - low + 1
                field_specs.append((f["name"], low, width))
            
            # Sort by low bit (LSB first)
            field_specs.sort(key=lambda x: x[1])
            total_width = sum(w for _, _, w in field_specs)
            sign_bit = 1 << (total_width - 1)
            mask = (1 << total_width) - 1
            
            # Combine fields into a single value
            combined = 0
            for name, low, width in field_specs:
                val = field_values.get(name, 0) & ((1 << width) - 1)
                combined |= val << (low - field_specs[0][1])
            
            # Sign-extend if needed
            if combined & sign_bit:
                combined = combined - (1 << total_width)
            return combined
        
        # If single-field immediate, return the value directly
        elif len(immediate_fields) == 1:
            field_name = immediate_fields[0]["name"]
            value = field_values.get(field_name, 0)
            
            # For branch instructions, we need to handle the immediate correctly
            if is_branch:
                # Use ISA-derived branch immediate width
                bit_width = get_immediate_width(self.isa_definition, 'branch')
                # Extract the raw value from the instruction word using multi-field specification
                from isa_xform.utils.bit_utils import extract_multi_field_bits
                encoding_fields = getattr(instruction, 'encoding', {}).get('fields', [])
                imm_field = next((f for f in encoding_fields if f.get('name') == 'imm'), None)
                if imm_field and 'bits' in imm_field:
                    raw_value = extract_multi_field_bits(instr_word, imm_field['bits'])
                    
                    # Sign extend the value to ISA word size
                    if raw_value & (1 << (bit_width - 1)):  # Negative value
                        # Sign extend to ISA word size
                        sign_extend_mask = get_immediate_sign_extend(self.isa_definition, bit_width)
                        value = raw_value | sign_extend_mask
                    else:
                        value = raw_value
                else:
                    # Fallback to field value if no bits specification
                    value = field_values.get(field_name, 0)

            
            return value
        
        # No immediate fields found
        return 0