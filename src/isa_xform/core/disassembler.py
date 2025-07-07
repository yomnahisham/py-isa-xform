"""
Disassembler: Converts machine code back to assembly language
"""

import struct
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
    label_map: Optional[Dict[int, str]] = None  # Map addresses to label names


class Disassembler:
    """Converts machine code to assembly language"""
    
    def __init__(self, isa_definition: ISADefinition, symbol_table: Optional[SymbolTable] = None, 
        max_consecutive_nops: int = 8):
        self.isa_definition = isa_definition
        self.symbol_table = symbol_table or SymbolTable()
        self.instruction_size_bytes = isa_definition.instruction_size // 8
        self.max_consecutive_nops = max_consecutive_nops
        
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
                if any(keyword in mnemonic for keyword in ['JMP', 'CALL', 'JAL', 'J']):
                    self.jump_instructions.add(mnemonic)
                    self.control_flow_instructions.add(mnemonic)
                elif any(keyword in mnemonic for keyword in ['BEQ', 'BNE', 'BLT', 'BGE', 'BLTU', 'BGEU', 'BZ', 'BNZ']):
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
            
            # Parse the expansion to understand the pattern
            expansion_lines = pseudo.expansion.strip().split('\n')
            if not expansion_lines:
                continue
            
            # Get the first instruction from the expansion
            first_line = expansion_lines[0].strip()
            if not first_line:
                continue
            
            # Parse the first instruction to understand the pattern
            parts = first_line.split()
            if len(parts) < 2:
                continue
            
            first_mnemonic = parts[0].upper()
            
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
            if len(parts) >= 3:
                rd = parts[1]
                rs2 = parts[2] if len(parts) > 2 else None
                
                if rd == 'x0' and rs2 == 'x0':
                    pattern['conditions'].append(('rd', 0))
                    pattern['conditions'].append(('rs2', 0))
                elif rd == 'x0':
                    pattern['conditions'].append(('rd', 0))
                elif rs2 == 'x0':
                    pattern['conditions'].append(('rs2', 0))
            
            self.pseudo_patterns[first_mnemonic].append(pattern)
    
    def _build_label_map_from_symbols(self, instructions: List[DisassembledInstruction]) -> Dict[int, str]:
        """Build a map of addresses to label names from disassembled instructions"""
        label_map = {}
        
        # First pass: collect all addresses that are targets of branches/jumps
        branch_targets = set()
        for instr in instructions:
            if instr.instruction:
                mnemonic = instr.instruction.mnemonic.upper()
                if any(keyword in mnemonic for keyword in ['JMP', 'CALL', 'BEQ', 'BNE', 'JZ', 'JNZ', 'JAL', 'J']):
                    # Extract target address from operands
                    for operand in instr.operands:
                        if operand.startswith('0x'):
                            try:
                                addr = int(operand, 16)
                                branch_targets.add(addr)
                            except ValueError:
                                pass
                        elif operand.isdigit():
                            try:
                                addr = int(operand)
                                branch_targets.add(addr)
                            except ValueError:
                                pass
        
        # Second pass: assign labels to branch targets
        label_counter = 1
        for addr in sorted(branch_targets):
            if addr not in label_map:
                label_map[addr] = f"L{label_counter:04d}"
                label_counter += 1
        
        return label_map
    
    def _resolve_address_to_label(self, address: int) -> str:
        """Resolve an address to a label name"""
        if address in self.label_map:
            return self.label_map[address]
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
                    
                    # If we've seen too many unknown instructions in a row, treat remaining as data
                    if consecutive_unknown >= max_unknown_before_data:
                        remaining_data = code_bytes[i:]
                        if len(remaining_data) > 0:
                            data_sections[code_addr] = remaining_data
                            if debug:
                                print(f"[DEBUG] PC=0x{code_addr:04X} | Switching to data mode, {len(remaining_data)} bytes")
                        break
                
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
                # ZX16 has a 65536-byte address space
                address_space_size = 65536  # Fixed for ZX16
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
                    
                    # More aggressive switching to data mode
                    if consecutive_nops >= max_nops_before_data and not in_data_section:
                        # Switch to data mode for blocks of zeros
                        in_data_section = True
                        data_start = current_address - (consecutive_nops - 1) * self.instruction_size_bytes
                        data_sections[data_start] = b'\x00' * (consecutive_nops * self.instruction_size_bytes)
                        if debug:
                            print(f"[DEBUG] PC=0x{current_address:04X} | SWITCHING TO DATA MODE (NOP block)")
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
                            
                            # Check if this is a return instruction
                            if decoded.instruction and 'RET' in decoded.instruction.mnemonic.upper():
                                last_instruction_was_return = True
                            
                            instructions.append(decoded)
                            if debug:
                                print(f"[DEBUG] PC=0x{current_address:04X} | Decoded: {decoded.mnemonic} {', '.join(decoded.operands)}")
                        else:
                            consecutive_invalid += 1
                            consecutive_valid_instructions = 0
                            
                            # If we've seen too many invalid instructions in a row, switch to data mode
                            if consecutive_invalid >= 3 and not in_data_section:
                                in_data_section = True
                                data_start = current_address - (consecutive_invalid - 1) * self.instruction_size_bytes
                                data_sections[data_start] = machine_code[i - (consecutive_invalid - 1) * self.instruction_size_bytes:i + self.instruction_size_bytes]
                                if debug:
                                    print(f"[DEBUG] PC=0x{current_address:04X} | SWITCHING TO DATA MODE (invalid instructions)")
                                    print(f"[DEBUG] Data section starts at 0x{data_start:04X}")
                                consecutive_invalid = 0
                            else:
                                # Add as unknown instruction
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

        # Reconstruct full immediate for any instruction with multiple immediate fields
        encoding_fields = getattr(instruction, 'encoding', {}).get('fields', [])
        immediate_fields = [f for f in encoding_fields if f.get('type') == 'immediate' and f.get('name') != 'opcode']
        if len(immediate_fields) > 1:
            # Use the instruction's implementation to reconstruct the full immediate
            # This is fully modular - the ISA definition tells us how to combine fields
            full_imm = self._reconstruct_immediate_from_implementation(instruction, field_values)
            
            # Now format operands using the reconstructed immediate
            for syntax_op in syntax_operands:
                if syntax_op in ('imm', 'immediate', 'offset'):
                    # Check if this is a branch/jump target address
                    if (instruction.mnemonic.upper() in ['JMP', 'CALL', 'BEQ', 'BNE', 'JZ', 'JNZ', 'JAL', 'J'] and 
                        syntax_op in ['immediate', 'imm', 'offset']):
                        # Try to resolve as label
                        resolved = self._resolve_address_to_label(full_imm)
                        operands.append(resolved)
                    else:
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
                # Check if this is a branch/jump target address
                if (instruction.mnemonic.upper() in ['JMP', 'CALL', 'BEQ', 'BNE', 'JZ', 'JNZ', 'JAL', 'J'] and 
                    field_name in ['immediate', 'imm', 'offset']):
                    # Try to resolve as label
                    resolved = self._resolve_address_to_label(value)
                    operands.append(resolved)
                else:
                    # Regular immediate formatting
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
            if instr.address in result.symbols:
                lines.append(f"{result.symbols[instr.address]}:")
            elif result.label_map and instr.address in result.label_map:
                lines.append(f"{result.label_map[instr.address]}:")
            
            # Format instruction
            instr_str = instr.mnemonic
            if instr.operands:
                instr_str += f" {', '.join(instr.operands)}"
            
            line_parts.append(instr_str)
            
            # Add comment if available
            if instr.comment:
                line_parts.append(f"; {instr.comment}")
            
            lines.append("    " + " ".join(line_parts))
        
        # Add data sections with enhanced formatting
        if result.data_sections:
            lines.append("")
            lines.append("; Data sections:")

            # Process each data section
            for addr, data_bytes in sorted(result.data_sections.items()):
                if include_addresses:
                    lines.append(f"    ; Data section at 0x{addr:04X}")
                
                # Detect ASCII strings in the data
                strings = self._detect_ascii_strings(data_bytes, addr)
                string_positions = {pos: (length, text) for pos, length, text in strings}
                
                # Output data with string detection
                i = 0
                word_size = self.isa_definition.word_size // 8
                endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
                
                while i < len(data_bytes):
                    current_pos = addr + i
                    
                    # Check if we're at a string position
                    if current_pos in string_positions:
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
                            lines.append(f"    {current_pos:04X}: {word_directive} 0x{value:04X}")
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
        """Reconstruct pseudo-instructions from hardware instructions"""
        if not self.pseudo_patterns:
            return instructions
        
        reconstructed = []
        i = 0
        
        while i < len(instructions):
            instr = instructions[i]
            
            # Check if this instruction matches a pseudo-pattern
            pseudo_mnemonic = self._check_pseudo_pattern(instr, instructions, i)
            
            if pseudo_mnemonic:
                # Replace with pseudo-instruction
                reconstructed.append(DisassembledInstruction(
                    address=instr.address,
                    machine_code=instr.machine_code,
                    mnemonic=pseudo_mnemonic,
                    operands=instr.operands,
                    instruction=instr.instruction,
                    comment=f"pseudo: {pseudo_mnemonic}"
                ))
                
                # Skip the next instruction if it was part of the pseudo-instruction
                # (e.g., LA expands to AUIPC + ADDI)
                if pseudo_mnemonic in ['LA', 'LI'] and i + 1 < len(instructions):
                    i += 1  # Skip the second instruction
            else:
                reconstructed.append(instr)
            
            i += 1
        
        return reconstructed
    
    def _check_pseudo_pattern(self, instr: DisassembledInstruction, instructions: List[DisassembledInstruction], index: int) -> Optional[str]:
        """Check if an instruction matches a pseudo-instruction pattern"""
        if not instr.instruction:
            return None
        
        mnemonic = instr.instruction.mnemonic.upper()
        
        if mnemonic not in self.pseudo_patterns:
            return None
        
        # Extract field values from the instruction
        field_values = self._extract_field_values(instr)
        
        for pattern in self.pseudo_patterns[mnemonic]:
            if self._matches_pseudo_pattern(field_values, pattern):
                return pattern['pseudo_mnemonic']
        
        return None
    
    def _extract_field_values(self, instr: DisassembledInstruction) -> Dict[str, int]:
        """Extract field values from a disassembled instruction"""
        field_values = {}
        
        if not instr.instruction or not hasattr(instr.instruction, 'encoding'):
            return field_values
        
        encoding = instr.instruction.encoding
        if not isinstance(encoding, dict) or 'fields' not in encoding:
            return field_values
        
        # Parse operands to extract field values
        # This is a simplified approach - in a full implementation, you'd decode the machine code
        if instr.operands:
            # For now, try to extract register numbers from operand strings
            for i, operand in enumerate(instr.operands):
                if operand.startswith('x'):
                    try:
                        reg_num = int(operand[1:])
                        field_values[f'rd'] = reg_num if i == 0 else field_values.get('rd', 0)
                        field_values[f'rs{i+1}'] = reg_num
                    except ValueError:
                        pass
                elif operand.isdigit() or operand.startswith('0x'):
                    try:
                        imm_val = int(operand, 16) if operand.startswith('0x') else int(operand)
                        field_values['imm'] = imm_val
                    except ValueError:
                        pass
        
        return field_values
    
    def _matches_pseudo_pattern(self, field_values: Dict[str, int], pattern: Dict[str, Any]) -> bool:
        """Check if field values match a pseudo-instruction pattern"""
        for field_name, expected_value in pattern['conditions']:
            if field_name not in field_values:
                return False
            if field_values[field_name] != expected_value:
                return False
        return True
    
    def _reconstruct_immediate_from_implementation(self, instruction: Instruction, field_values: Dict[str, int]) -> int:
        """Reconstruct the full immediate value from instruction implementation"""
        # Parse the implementation to understand how to combine immediate fields
        implementation = getattr(instruction, 'implementation', '')
        
        # Create a local namespace with the field values
        local_vars = field_values.copy()
        
        try:
            # Extract immediate combination logic from implementation
            # Look for patterns like: offset = (imm1 << 3) | imm2
            lines = implementation.split('\n')
            for line in lines:
                line = line.strip()
                if '=' in line and ('<<' in line or '|' in line or '&' in line):
                    # This line likely combines immediate fields
                    # Execute it in our local namespace
                    exec(line, {}, local_vars)
            
            # Look for the final immediate value
            # Common variable names: offset, imm, immediate, result
            for var_name in ['offset', 'imm', 'immediate', 'result']:
                if var_name in local_vars:
                    return local_vars[var_name]
            
            # If no specific variable found, try to reconstruct from field names
            # This is a fallback for when the implementation doesn't clearly define the output
            immediate_fields = [f for f in getattr(instruction, 'encoding', {}).get('fields', []) 
                              if f.get('type') == 'immediate' and f.get('name') != 'opcode']
            
            if len(immediate_fields) == 2:
                # Common pattern: combine two immediate fields
                field_names = [f['name'] for f in immediate_fields]
                if 'imm' in field_names and 'imm2' in field_names:
                    imm_val = field_values.get('imm', 0)
                    imm2_val = field_values.get('imm2', 0)
                    # Default pattern: (imm << 3) | imm2
                    return (imm_val << 3) | imm2_val
                elif 'imm1' in field_names and 'imm2' in field_names:
                    imm1_val = field_values.get('imm1', 0)
                    imm2_val = field_values.get('imm2', 0)
                    # Default pattern: (imm1 << 3) | imm2
                    return (imm1_val << 3) | imm2_val
            
            # If all else fails, return the first immediate field value
            for field_name, value in field_values.items():
                if field_name in ['imm', 'immediate', 'offset']:
                    return value
            
            return 0
            
        except Exception:
            # If execution fails, fall back to simple concatenation
            immediate_fields = [f for f in getattr(instruction, 'encoding', {}).get('fields', []) 
                              if f.get('type') == 'immediate' and f.get('name') != 'opcode']
            
            if len(immediate_fields) == 2:
                field_names = [f['name'] for f in immediate_fields]
                if 'imm' in field_names and 'imm2' in field_names:
                    imm_val = field_values.get('imm', 0)
                    imm2_val = field_values.get('imm2', 0)
                    return (imm_val << 3) | imm2_val
            
            return field_values.get('imm', 0) 