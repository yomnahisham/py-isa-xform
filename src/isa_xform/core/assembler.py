"""
Assembler: Converts assembly language to machine code
"""

import struct
from enum import Enum
from typing import List, Optional, Dict, Any, Union, Tuple
from dataclasses import dataclass, field
import re

from .isa_loader import ISADefinition, Instruction, Directive, Register
from .parser import Parser, ASTNode, LabelNode, InstructionNode, DirectiveNode, CommentNode, OperandNode
from .symbol_table import SymbolTable, Symbol, SymbolType, SymbolScope
from ..utils.error_handling import AssemblerError, ErrorLocation
from ..utils.bit_utils import (
    extract_bits, set_bits, sign_extend, parse_bit_range, 
    create_mask, bytes_to_int, int_to_bytes
)


@dataclass
class AssemblyContext:
    """Context information for assembly process"""
    current_address: int = 0
    current_section: str = "text"
    pass_number: int = 1
    origin_set: bool = False
    symbols_defined: Dict[str, int] = field(default_factory=dict)
    org_address: int = 0


@dataclass 
class AssembledCode:
    """Result of assembly process"""
    machine_code: bytearray
    symbol_table: SymbolTable
    entry_point: Optional[int] = None
    sections: Optional[Dict[str, Tuple[int, int]]] = None  # section_name: (start_addr, size)
    data_section_size: int = 0  # Size of data section in bytes


class Assembler:
    """Converts assembly language to machine code"""
    
    def __init__(self, isa_definition: ISADefinition, symbol_table: Optional[SymbolTable] = None):
        self.isa_definition = isa_definition
        self.symbol_table = symbol_table or SymbolTable()
        self.context = AssemblyContext()
        self.instruction_size_bytes = isa_definition.instruction_size // 8
        
        # Build instruction lookup tables
        self._build_instruction_lookup()
        
        # Build directive handlers
        self._build_directive_handlers()
        
        # Compile custom directive implementations
        self._compile_directive_implementations()
    
    def _build_instruction_lookup(self):
        """Build fast instruction lookup tables"""
        self.instruction_by_mnemonic = {}
        
        for instruction in self.isa_definition.instructions:
            mnemonic = instruction.mnemonic.upper()
            if not self.isa_definition.assembly_syntax.case_sensitive:
                mnemonic = mnemonic.upper()
            self.instruction_by_mnemonic[mnemonic] = instruction
    
    def _build_directive_handlers(self):
        """Build directive handler mapping"""
        self.directive_handlers = {
            '.org': self._handle_org_directive,
            '.word': self._handle_word_directive,
            '.byte': self._handle_byte_directive,
            '.space': self._handle_space_directive,
            '.ascii': self._handle_ascii_directive,
            '.asciiz': self._handle_asciiz_directive,
            '.section': self._handle_section_directive,
            '.global': self._handle_global_directive,
            '.equ': self._handle_equ_directive,
            '.align': self._handle_align_directive
        }
    
    def _compile_directive_implementations(self):
        """Compile custom directive implementations from ISA definition"""
        from .directive_executor import compile_directive_implementations
        compile_directive_implementations(self.isa_definition)
    
    def assemble(self, nodes: List[ASTNode], two_pass: bool = True) -> AssembledCode:
        """
        Assemble AST nodes into machine code
        
        Args:
            nodes: List of AST nodes to assemble
            two_pass: Whether to use two-pass assembly (default: True)
            
        Returns:
            AssembledCode containing machine code and symbol table
        """
        machine_code = bytearray()
        
        if two_pass:
            # First pass: collect symbols and calculate addresses
            self.context.pass_number = 1
            self._first_pass(nodes)
            
            # Second pass: generate code
            self.context.pass_number = 2
            self.context.current_address = 0
            machine_code = self._second_pass(nodes)
        else:
            # Single pass assembly
            self.context.pass_number = 1
            machine_code = self._single_pass(nodes)
        
        return AssembledCode(
            machine_code=machine_code,
            symbol_table=self.symbol_table,
            entry_point=self._find_entry_point(),
            data_section_size=0  # We'll calculate this properly later
        )
    
    def _first_pass(self, nodes: List[ASTNode]):
        """First pass: collect symbols and calculate addresses"""
        self.symbol_table.reset()
        
        # Initialize with default code start address from ISA
        code_section_start = self.isa_definition.address_space.memory_layout.get('code_section', {}).get('start', 0)
        data_section_start = self.isa_definition.address_space.memory_layout.get('data_section', {}).get('start', 0)
        
        self.context.current_address = code_section_start
        self.context.current_section = "text"
        
        for node in nodes:
            if isinstance(node, LabelNode):
                self._handle_label_definition(node)
                print(f"[DEBUG] After LabelNode {getattr(node, 'name', '')}: address = {self.context.current_address}")
            elif isinstance(node, InstructionNode):
                # Record the address for this instruction node
                node.address = self.context.current_address
                self._advance_address_for_instruction(node)
                print(f"[DEBUG] After InstructionNode {getattr(node, 'mnemonic', '')}: address = {self.context.current_address}")
            elif isinstance(node, DirectiveNode):
                self._handle_directive_first_pass(node)
                print(f"[DEBUG] After DirectiveNode {getattr(node, 'name', '')}: address = {self.context.current_address}")
    
    def _second_pass(self, nodes: List[ASTNode]) -> bytearray:
        """Second pass: generate machine code with section header"""
        # Get ISA memory layout
        data_section_start = self.isa_definition.address_space.memory_layout.get('data_section', {}).get('start', 0)
        code_section_start = self.isa_definition.address_space.memory_layout.get('code_section', {}).get('start', 0)
        
        # Collect code and data sections
        code_bytes = bytearray()
        data_bytes = bytearray()
        current_section = "text"
        # Use code section start address, not org_address
        self.context.current_address = code_section_start
        logical_code_address = code_section_start  # Track logical code address for instructions
        logical_data_address = data_section_start  # Track logical data address for data
        actual_data_start = data_section_start  # Track actual data start address for ISAX header

        for node in nodes:
            if isinstance(node, LabelNode):
                pass
            elif isinstance(node, DirectiveNode):
                if node.name.lower() == '.data':
                    current_section = "data"
                    self.context.current_address = data_section_start
                elif node.name.lower() == '.text':
                    current_section = "text"
                    self.context.current_address = code_section_start
                elif node.name.lower() == '.org':
                    # Handle .org directive in second pass to set correct address
                    if node.arguments:
                        address = self._parse_number(node.arguments[0])
                        if current_section == "data":
                            logical_data_address = address
                            actual_data_start = address  # Update actual data start for ISAX header
                        else:
                            logical_code_address = address
                        self.context.current_address = address
                else:
                    # Use directive handler dispatch
                    handler = self.directive_handlers.get(node.name.lower())
                    if handler:
                        # Automatically detect data directives and put them in data section
                        data_directives = {'.word', '.byte', '.space', '.ascii', '.asciiz'}
                        if node.name.lower() in data_directives or current_section == "data":
                            # Use logical data address for data
                            self.context.current_address = logical_data_address
                            data_bytes.extend(handler(node) or b"")
                            logical_data_address = self.context.current_address
                        else:
                            # Use logical code address for code
                            self.context.current_address = logical_code_address
                            code_bytes.extend(handler(node) or b"")
                            logical_code_address = self.context.current_address
            elif isinstance(node, InstructionNode):
                # Use the address recorded in the first pass for this instruction
                instruction_address = getattr(node, 'address', logical_code_address)
                self.context.current_address = instruction_address
                print(f"[DEBUG] Second pass: logical_code_address={logical_code_address}, current_address={self.context.current_address}, instruction_address={instruction_address}")
                code = self._assemble_instruction(node, instruction_address)
                code_bytes.extend(code)
                logical_code_address = self.context.current_address
        
        # Serialize symbol table for inclusion in binary
        symbol_data = self._serialize_symbol_table()
        symbol_data_bytes = symbol_data.encode('utf-8')
        
        # Build enhanced ISAX header: 
        # [magic][version][entry_point][code_start][code_size][data_start][data_size][symbol_size][code][data][symbols]
        header = bytearray()
        header.extend(b'ISAX')  # Magic (4 bytes)
        header.extend((2).to_bytes(4, 'little'))  # Version 2 with symbol support (4 bytes)
        entry_point = code_section_start.to_bytes(4, 'little')
        header.extend(entry_point)  # Entry point (4 bytes)
        header.extend(code_section_start.to_bytes(4, 'little'))  # Code start (4 bytes)
        header.extend(len(code_bytes).to_bytes(4, 'little'))  # Code size (4 bytes)
        header.extend(actual_data_start.to_bytes(4, 'little'))  # Data start (4 bytes)
        header.extend(len(data_bytes).to_bytes(4, 'little'))  # Data size (4 bytes)
        header.extend(len(symbol_data_bytes).to_bytes(4, 'little'))  # Symbol size (4 bytes)
        
        # Append code, data, and symbols
        header.extend(code_bytes)
        header.extend(data_bytes)
        header.extend(symbol_data_bytes)
        
        return header
    
    def _single_pass(self, nodes: List[ASTNode]) -> bytearray:
        """Single pass assembly (for simple cases)"""
        machine_code = bytearray()
        self.context.current_address = 0
        
        for node in nodes:
            if isinstance(node, LabelNode):
                self._handle_label_definition(node)
            elif isinstance(node, InstructionNode):
                code = self._assemble_instruction(node)
                machine_code.extend(code)
            elif isinstance(node, DirectiveNode):
                code = self._handle_directive_second_pass(node)
                if code:
                    machine_code.extend(code)
        
        return machine_code
    
    def _handle_label_definition(self, node: LabelNode):
        """Handle label definition"""
        self.symbol_table.set_current_address(self.context.current_address)
        symbol = self.symbol_table.define_label(node.name, node.line, node.column, node.file)
        # Ensure the symbol is marked as defined and has the correct value
        if symbol:
            symbol.defined = True
            symbol.value = self.context.current_address
    
    def _advance_address_for_instruction(self, node: InstructionNode):
        """Advance address for instruction during first pass"""
        instruction = self._find_instruction(node.mnemonic)
        if instruction:
            self.context.current_address += self.instruction_size_bytes
            self.symbol_table.set_current_address(self.context.current_address)
        else:
            # Expand pseudo-instruction and advance for each real instruction
            expanded_nodes = self._expand_pseudo_instruction(node, self.context.current_address)
            for n in expanded_nodes:
                self._advance_address_for_instruction(n)
    
    def _assemble_instruction(self, node: InstructionNode, instruction_address: Optional[int] = None) -> bytearray:
        """Assemble a single instruction, expanding pseudo-instructions if needed"""
        instruction = self._find_instruction(node.mnemonic)
        if not instruction:
            # Try pseudo-instruction expansion
            # Pass the current instruction address to the expansion
            expanded_nodes = self._expand_pseudo_instruction(node, self.context.current_address)
            code = bytearray()
            for n in expanded_nodes:
                code.extend(self._assemble_instruction(n, instruction_address))
            return code
        # Use passed instruction address or capture from context
        if instruction_address is None:
            instruction_address = int(self.context.current_address)
        # Encode the instruction based on its format
        encoded = self._encode_instruction(instruction, node.operands, instruction_address)
        
        # Convert to bytes using bit utilities
        endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
        instruction_bytes = int_to_bytes(encoded, self.instruction_size_bytes, endianness)
        
        # Update address
        self.context.current_address += self.instruction_size_bytes
        self.symbol_table.set_current_address(self.context.current_address)
        
        return bytearray(instruction_bytes)
    
    def _encode_instruction(self, instruction: Instruction, operands: List[OperandNode], instruction_address: int = 0) -> int:
        """Encode instruction with operands using only the ISA definition's encoding.fields"""
        encoding = instruction.encoding
        instruction_word = 0

        # DEBUG: Print operands and their types
        print(f"[DEBUG] Encoding instruction: {instruction.mnemonic}")
        for idx, op in enumerate(operands):
            print(f"[DEBUG]   Operand {idx}: type={op.type}, value={op.value}")

        if isinstance(encoding, dict) and "fields" in encoding:
            # Use field-based encoding from ISA definition
            instruction_word = self._encode_with_fields(encoding["fields"], operands, instruction, instruction_address)
        else:
            raise AssemblerError(f"Instruction '{instruction.mnemonic}' is missing 'encoding.fields' in the ISA definition. Modular encoding requires explicit field definitions.")
        return instruction_word

    def _encode_with_fields(self, fields: List[Dict[str, Any]], operands: List[OperandNode], instruction: 'Instruction', instruction_address: int = 0) -> int:
        """Encode instruction using field-based encoding"""
        # Map operands to fields
        operand_mapping = self._map_operands_to_fields_modular(fields, operands, instruction)
        
        # Build the instruction word
        instruction_word = 0
        
        for field in fields:
            field_name = field["name"]
            bits = field["bits"]
            
            if "value" in field:
                # Fixed value field
                field_value = int(field["value"], 2) if isinstance(field["value"], str) else field["value"]
            elif field_name in operand_mapping:
                # Operand field
                operand = operand_mapping[field_name]
                field_type = field.get("type", "immediate")
                bit_width = self._get_bit_width(bits)
                signed = field.get("signed", False)
                # Pass field and instruction for modular offset calculation
                field_value = self._resolve_operand_value(operand, field_type, bit_width, signed, instruction_address, field or {}, instruction)
            else:
                # Field not provided - use default value
                field_value = 0
            
            # Insert field value into instruction word
            instruction_word = self._insert_field(instruction_word, bits, field_value)
        
        return instruction_word

    def _map_operands_to_fields_modular(self, fields: List[Dict[str, Any]], operands: List[OperandNode], instruction: Instruction) -> Dict[str, OperandNode]:
        """Map operands to field names based on the order in the instruction's syntax field, handling mem operands and multi-field immediates."""
        mapping = {}

        # Parse operand names from the syntax string
        syntax_parts = instruction.syntax.split()
        operand_names = []
        if len(syntax_parts) > 1:
            # Remove the mnemonic and join the rest, then split by comma
            operand_str = ' '.join(syntax_parts[1:])
            operand_names = [part.strip() for part in operand_str.split(',') if part.strip()]
            
            # Map operands to syntax names
            for i, (op, name) in enumerate(zip(operands, operand_names)):
                # Special handling for mem operands (offset(base))
                if op.type == "mem" and '(' in name and name.endswith(')'):
                    before_paren = name[:name.index('(')].strip()
                    inside_paren = name[name.index('(')+1:-1].strip()
                    offset_node, reg_node = op.value
                    # Map offset to immediate/offset/imm field
                    mapping[before_paren] = offset_node
                    # Map base register
                    mapping[inside_paren] = reg_node
                    # Also add with $ prefix for compatibility
                    mapping[f"${before_paren}"] = offset_node
                    mapping[f"${inside_paren}"] = reg_node
                    # Add alias mapping for field resolution
                    if before_paren == "offset":
                        mapping["imm"] = offset_node
                        mapping["immediate"] = offset_node
                    continue
                
                # Regular operand mapping
                mapping[f"${name}"] = op
                mapping[name] = op
                # Also add generic names for this operand
                mapping[f"$op{i+1}"] = op
                mapping[f"op{i+1}"] = op
                mapping[f"${i+1}"] = op
                if str(i+1) not in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                    mapping[f"{i+1}"] = op
        
        # Get operand fields (fields that expect operands, not fixed values)
        operand_fields = [f for f in fields if "type" in f and f.get("name") != "opcode"]

        # Map operands to fields by syntax order
        for i, operand_node in enumerate(operands):
            if i < len(operand_names):
                operand_name = operand_names[i]
                # Find the field with this name, or allow offset->imm mapping
                for field in operand_fields:
                    field_name = field["name"]
                    if field_name == operand_name or (operand_name == "offset" and field_name == "imm"):
                        mapping[field_name] = operand_node
                        break
        
        # --- PATCH: For multi-field immediates (like LUI, J, JAL), map the same operand to all immediate fields ---
        # If there is exactly one immediate/label operand and multiple immediate fields, map to all
        immediate_fields = [f for f in fields if f.get("type") == "immediate" and f.get("name") != "opcode"]
        immediate_operands = [op for op in operands if getattr(op, 'type', None) in ['immediate', 'label']]
        if len(immediate_operands) == 1 and len(immediate_fields) > 1:
            for field in immediate_fields:
                mapping[field["name"]] = immediate_operands[0]
        # --- END PATCH ---
        return mapping
    
    def _resolve_operand_value(self, operand: OperandNode, field_type: str, bit_width: int, signed: bool = False, instruction_address: int = 0, field: dict = {}, instruction: Optional['Instruction'] = None) -> int:
        """Resolve operand value based on field type"""
        # DEBUG: Print operand type and value for each field
        print(f"[DEBUG] Resolving operand value: operand.type={operand.type}, operand.value={operand.value}, field_type={field_type}")
        field_name = field.get("name", "")
        if field_type == "register":
            return self._resolve_register_operand(operand)
        elif field_type == "immediate":
            # Check if this is actually a label (for branch/jump instructions)
            if operand.type == "label":
                # Resolve label to address
                target_address = self._resolve_address_operand(operand)
                
                # Use ISA-driven PC behavior for jump offset calculation
                pc_config = getattr(self.isa_definition, 'pc_behavior', {})
                pc_offset = pc_config.get('offset_for_jumps', 0)
                jump_calc = pc_config.get('jump_offset_calculation', 'target_minus_pc')
                
                if jump_calc == 'target_minus_pc':
                    # Calculate offset as target - (instruction_address + pc_offset)
                    offset = target_address - (instruction_address + pc_offset)
                elif jump_calc == 'target_minus_current':
                    # Calculate offset as target - instruction_address
                    offset = target_address - instruction_address
                else:
                    # Fallback to target - current
                    offset = target_address - instruction_address
                
                print(f"[DEBUG] Jump offset calculation: target={target_address}, instruction_addr={instruction_address}, pc_offset={pc_offset}, jump_calc={jump_calc}, offset={offset}")
                
                # Handle multi-field immediates for label operands
                if field and "bits" in field and instruction and hasattr(instruction, "encoding"):
                    encoding_fields = instruction.encoding.get("fields", [])
                    immediate_fields = [f for f in encoding_fields if f.get("type") == "immediate" and f.get("name") != "opcode"]
                    if len(immediate_fields) > 1:
                        print(f"[DEBUG] Multi-field immediate detected for {instruction.mnemonic}, field={field_name}, offset={offset}")
                        # --- ISA-driven multi-field immediate encoding ---
                        # 1. Compute total width and sign bit
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
                        # 2. Encode offset as signed value of correct width
                        if offset < 0:
                            signed_offset = (offset + (1 << total_width)) & mask
                        else:
                            signed_offset = offset & mask
                        # 3. Extract bits for each field
                        for name, low, width in field_specs:
                            field_val = (signed_offset >> (low - field_specs[0][1])) & ((1 << width) - 1)
                            if field_name == name:
                                print(f"[DEBUG] ISA-driven multi-field: field={name}, offset={offset}, signed_offset={signed_offset}, result={field_val}")
                                return field_val
                        # fallback (should not reach)
                        return 0
                
                return offset
            else:
                # Treat as literal immediate value
                value = self._resolve_immediate_operand(operand)

            # Handle multi-field immediates using ISA-driven logic
            if field and "bits" in field and instruction and hasattr(instruction, "encoding"):
                encoding_fields = instruction.encoding.get("fields", [])
                immediate_fields = [f for f in encoding_fields if f.get("type") == "immediate" and f.get("name") != "opcode"]
                print(f"[DEBUG] Checking multi-field for {instruction.mnemonic}, field={field_name}, value={value}")
                print(f"[DEBUG] All fields: {[f['name'] for f in encoding_fields]}")
                print(f"[DEBUG] Immediate fields: {[f['name'] for f in immediate_fields]}")
                if len(immediate_fields) > 1:
                    print(f"[DEBUG] Multi-field immediate detected for {instruction.mnemonic}, field={field_name}, value={value}")
                    print(f"[DEBUG] Immediate fields: {[f['name'] for f in immediate_fields]}")
                    
                    # Use ISA-driven multi-field immediate encoding based on instruction implementation
                    # This is fully modular - the ISA definition tells us how to split the immediate
                    field_value = self._split_multi_field_immediate(instruction, field_name, value, immediate_fields)
                    if field_value is not None:
                        return field_value

            # Validate immediate fits in bit width (for single-field immediates)
            if signed:
                min_val = -(1 << (bit_width - 1))
                max_val = (1 << (bit_width - 1)) - 1
                if value < min_val or value > max_val:
                    raise AssemblerError(f"Immediate value {value} doesn't fit in {bit_width}-bit signed field")
            else:
                if value < 0 or value >= (1 << bit_width):
                    raise AssemblerError(f"Immediate value {value} doesn't fit in {bit_width}-bit unsigned field")
            return value & create_mask(bit_width)  # Ensure proper bit width

        if field_type == "address":
            # For address fields, use absolute address
            return self._resolve_address_operand(operand)
        else:
            # Default to immediate value
            return self._resolve_immediate_operand(operand)
    
    def _split_multi_field_immediate(self, instruction: Instruction, field_name: str, value: int, immediate_fields: List[Dict[str, Any]]) -> Optional[int]:
        """Split multi-field immediate using ISA-driven logic based on instruction implementation"""
        # Get the instruction's implementation to understand how to split the immediate
        implementation = getattr(instruction, 'implementation', '')
        
        # For ZX16 LUI/AUIPC: imm = (imm1 << 3) | imm2
        if instruction.mnemonic in ['LUI', 'AUIPC'] and 'imm1' in implementation and 'imm2' in implementation:
            # Extract field widths
            imm1_field = next((f for f in immediate_fields if f['name'] == 'imm'), None)
            imm2_field = next((f for f in immediate_fields if f['name'] == 'imm2'), None)
            
            if imm1_field and imm2_field:
                imm1_width = self._get_bit_width(imm1_field['bits'])
                imm2_width = self._get_bit_width(imm2_field['bits'])
                
                if field_name == 'imm':  # This is imm1 (upper bits)
                    # Extract upper bits: value >> imm2_width
                    return (value >> imm2_width) & ((1 << imm1_width) - 1)
                elif field_name == 'imm2':  # This is imm2 (lower bits)
                    # Extract lower bits: value & ((1 << imm2_width) - 1)
                    return value & ((1 << imm2_width) - 1)
        
        # For other instructions, use a generic approach based on field order
        # Sort fields by their bit position in the instruction
        field_specs = []
        for f in immediate_fields:
            bits = f.get("bits", "")
            if ":" in bits:
                high, low = [int(x) for x in bits.split(":")]
            else:
                high = low = int(bits)
            field_specs.append((f["name"], low, high - low + 1))
        
        # Sort by bit position (LSB first)
        field_specs.sort(key=lambda x: x[1])
        
        # Extract bits based on field position in the logical immediate
        bit_offset = 0
        for name, _, width in field_specs:
            if name == field_name:
                return (value >> bit_offset) & ((1 << width) - 1)
            bit_offset += width
        
        return None

    def _resolve_register_operand(self, operand: OperandNode) -> int:
        """Resolve register operand to register number using ISA JSON configuration"""
        reg_val = operand.value
        
        # Get register formatting config from ISA
        reg_config = getattr(self.isa_definition, 'register_formatting', {})
        prefix = reg_config.get('prefix', 'x')
        alternatives = reg_config.get('alternatives', {})
        
        # If it's a register object (from OperandParser), match by object
        if hasattr(reg_val, 'name') and hasattr(reg_val, 'alias'):
            for category, registers in self.isa_definition.registers.items():
                for i, register in enumerate(registers):
                    if register is reg_val:
                        return i
        
        # Otherwise, treat as string (name or alias)
        reg_name = reg_val
        
        for category, registers in self.isa_definition.registers.items():
            for i, register in enumerate(registers):
                # Check main register name (with and without prefix)
                if register.name == reg_name:
                    return i
                
                # Check without prefix if the register name has a prefix
                if reg_name.startswith(prefix) and register.name == reg_name[len(prefix):]:
                    return i
                
                # Check with prefix if the register name doesn't have a prefix
                if not reg_name.startswith(prefix) and register.name == prefix + reg_name:
                    return i
                
                # Check aliases
                for alias in register.alias:
                    if alias == reg_name:
                        return i
                    # Check alias without prefix if it has a prefix
                    if reg_name.startswith(prefix) and alias == reg_name[len(prefix):]:
                        return i
                    # Check alias with prefix if it doesn't have a prefix
                    if not reg_name.startswith(prefix) and alias == prefix + reg_name:
                        return i
                
                # Check alternative names from JSON config
                if register.name in alternatives:
                    for alt_name in alternatives[register.name]:
                        if alt_name == reg_name:
                            return i
                        # Check alternative without prefix if it has a prefix
                        if reg_name.startswith(prefix) and alt_name == reg_name[len(prefix):]:
                            return i
                        # Check alternative with prefix if it doesn't have a prefix
                        if not reg_name.startswith(prefix) and alt_name == prefix + reg_name:
                            return i
        
        raise AssemblerError(f"Unknown register: {operand.value}")
    
    def _resolve_immediate_operand(self, operand: OperandNode) -> int:
        """Resolve immediate operand to integer value, supporting label bitfield extraction (e.g., label[15:9])"""
        # Handle memory operands (tuples of immediate and register)
        if isinstance(operand.value, tuple):
            # This is a memory operand like (offset, register)
            offset_node, _ = operand.value
            value_str = offset_node.value
        else:
            value_str = operand.value
        
        # If the value is a register object, this is a bug in the parser or mapping
        if hasattr(value_str, 'name') and hasattr(value_str, 'alias'):
            raise AssemblerError(f"Register operand passed where immediate expected: {value_str.name}")
        
        # Get operand formatting config from ISA
        op_config = getattr(self.isa_definition, 'operand_formatting', {})
        immediate_prefix = op_config.get('immediate_prefix', '#')
        
        # Fallback to assembly_syntax for backward compatibility
        if not immediate_prefix:
            syntax = self.isa_definition.assembly_syntax
            immediate_prefix = getattr(syntax, 'immediate_prefix', '#')
        
        # Remove immediate prefix if present
        if isinstance(value_str, str) and value_str.startswith(immediate_prefix):
            value_str = value_str[len(immediate_prefix):]
        
        # Support label bitfield extraction
        if isinstance(value_str, str):
            # Match pattern like 'label[15:9]'
            m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\[(\d+):(\d+)\]$", value_str)
            if m:
                label = m.group(1)
                high = int(m.group(2))
                low = int(m.group(3))
                # Resolve label address
                symbol = self.symbol_table.get_symbol(label)
                if symbol and symbol.defined:
                    address = symbol.value
                else:
                    # Forward reference: use 0 for first pass, error for second pass
                    if self.context.pass_number == 2:
                        raise AssemblerError(f"Undefined symbol: {label}")
                    address = 0
                # Extract bits
                width = high - low + 1
                mask = (1 << width) - 1
                return (address >> low) & mask
        return self._parse_number(value_str)
    
    def _resolve_address_operand(self, operand: OperandNode) -> int:
        """Resolve address operand (label or immediate)"""
        if operand.type == "label":
            # Look up symbol
            symbol = self.symbol_table.get_symbol(operand.value)
            if symbol and symbol.defined:
                return symbol.value
            else:
                # Forward reference - return 0 for first pass, error for second pass
                if self.context.pass_number == 2:
                    raise AssemblerError(f"Undefined symbol: {operand.value}")
                return 0
        else:
            return self._resolve_immediate_operand(operand)
    
    def _parse_number(self, value_str: str) -> int:
        """Parse number string to integer using ISA JSON configuration"""
        # Get operand formatting config from ISA
        op_config = getattr(self.isa_definition, 'operand_formatting', {})
        hex_prefix = op_config.get('hex_prefix', '0x')
        binary_prefix = op_config.get('binary_prefix', '0b')
        
        # Fallback to assembly_syntax for backward compatibility
        if not hex_prefix or not binary_prefix:
            syntax = self.isa_definition.assembly_syntax
            if not hex_prefix:
                hex_prefix = getattr(syntax, 'hex_prefix', '0x')
            if not binary_prefix:
                binary_prefix = getattr(syntax, 'binary_prefix', '0b')
        
        try:
            # Handle different number formats based on ISA configuration
            if value_str.startswith(hex_prefix):
                return int(value_str, 16)
            elif value_str.startswith(binary_prefix):
                return int(value_str, 2)
            else:
                return int(value_str, 10)
        except ValueError:
            raise AssemblerError(f"Invalid number format: {value_str}")
    
    def _find_instruction(self, mnemonic: str) -> Optional[Instruction]:
        """Find instruction by mnemonic"""
        lookup_name = mnemonic.upper() if not self.isa_definition.assembly_syntax.case_sensitive else mnemonic
        return self.instruction_by_mnemonic.get(lookup_name)
    
    def _handle_directive_first_pass(self, node: DirectiveNode):
        """Handle directive during first pass"""
        directive_name = node.name.lower()
        
        if directive_name == '.org':
            if node.arguments:
                address = self._parse_number(node.arguments[0])
                self.context.current_address = address
                self.context.origin_set = True
                self.symbol_table.set_current_address(address)
        elif directive_name == '.data':
            # Switch to data section, but don't set address yet - wait for .org directive
            self.context.current_section = "data"
            # Only set default address if we haven't seen an .org directive yet
            if not self.context.origin_set:
                data_section_start = self.isa_definition.address_space.memory_layout.get('data_section', {}).get('start', 0)
                self.context.current_address = data_section_start
                self.symbol_table.set_current_address(data_section_start)
        elif directive_name == '.text':
            # Switch to code section address
            code_section_start = self.isa_definition.address_space.memory_layout.get('code_section', {}).get('start', 0)
            self.context.current_address = code_section_start
            self.context.current_section = "text"
            self.symbol_table.set_current_address(code_section_start)
        elif directive_name in ['.word', '.byte']:
            # Calculate space needed
            if directive_name == '.word':
                size = self.isa_definition.word_size // 8  # Use ISA's word size
            else:
                size = 1  # .byte is always 1 byte
            self.context.current_address += size * len(node.arguments)
            self.symbol_table.set_current_address(self.context.current_address)
        elif directive_name == '.space':
            if node.arguments:
                size = self._parse_number(node.arguments[0])
                self.context.current_address += size
                self.symbol_table.set_current_address(self.context.current_address)
        elif directive_name in ['.ascii', '.asciiz']:
            if node.arguments:
                text = node.arguments[0].strip('"\'')
                size = len(text)
                if directive_name == '.asciiz':
                    size += 1  # Null terminator
                self.context.current_address += size
                self.symbol_table.set_current_address(self.context.current_address)
        else:
            # Check if it's a custom directive from ISA definition
            if directive_name in self.isa_definition.directives:
                directive = self.isa_definition.directives[directive_name]
                action = directive.action
                
                if action == "allocate_bytes":
                    # Word directive
                    size = self.isa_definition.word_size // 8  # Use ISA's word size
                    self.context.current_address += size * len(node.arguments)
                    self.symbol_table.set_current_address(self.context.current_address)
                elif action == "allocate_space":
                    # Space directive
                    if node.arguments:
                        size = self._parse_number(node.arguments[0])
                        self.context.current_address += size
                        self.symbol_table.set_current_address(self.context.current_address)
                elif action == "allocate_string":
                    # ASCII directive
                    if node.arguments:
                        text = node.arguments[0].strip('"\'')
                        size = len(text)
                        self.context.current_address += size
                        self.symbol_table.set_current_address(self.context.current_address)
                # elif action == "allocate_crazy":
                #     # Crazy directive - allocate word size per argument
                #     size = 4  # Use word size from ISA
                #     self.context.current_address += size * len(node.arguments)
                #     self.symbol_table.set_current_address(self.context.current_address)
    
    def _handle_directive_second_pass(self, node: DirectiveNode) -> Optional[bytearray]:
        """Handle directive during second pass"""
        directive_name = node.name.lower()
        handler = self.directive_handlers.get(directive_name)
        
        if handler:
            return handler(node)
        else:
            # Check if it's a custom directive from ISA definition
            if directive_name in self.isa_definition.directives:
                return self._handle_custom_directive(node)
        
        return None
    
    # Directive handlers
    def _handle_org_directive(self, node: DirectiveNode) -> Optional[bytearray]:
        """Handle .org directive"""
        if node.arguments:
            address = self._parse_number(node.arguments[0])
            
            # If we need to pad to reach the new address
            if address > self.context.current_address:
                padding_size = address - self.context.current_address
                self.context.current_address = address
                self.symbol_table.set_current_address(address)
                return bytearray(b'\x00' * padding_size)
            else:
                self.context.current_address = address
                self.symbol_table.set_current_address(address)
        
        return None
    
    def _handle_word_directive(self, node: DirectiveNode) -> bytearray:
        """Handle .word directive"""
        data = bytearray()
        word_size = self.isa_definition.word_size // 8
        
        for arg in node.arguments:
            value = self._parse_number(arg)
            endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
            word_bytes = int_to_bytes(value, word_size, endianness)
            data.extend(word_bytes)
        
        self.context.current_address += len(data)
        self.symbol_table.set_current_address(self.context.current_address)
        return data
    
    def _handle_byte_directive(self, node: DirectiveNode) -> bytearray:
        """Handle .byte directive"""
        data = bytearray()
        
        for arg in node.arguments:
            value = self._parse_number(arg) & 0xFF
            data.append(value)
        
        self.context.current_address += len(data)
        self.symbol_table.set_current_address(self.context.current_address)
        return data
    
    def _handle_space_directive(self, node: DirectiveNode) -> bytearray:
        """Handle .space directive"""
        if node.arguments:
            size = self._parse_number(node.arguments[0])
            self.context.current_address += size
            self.symbol_table.set_current_address(self.context.current_address)
            return bytearray(b'\x00' * size)
        return bytearray()
    
    def _handle_ascii_directive(self, node: DirectiveNode) -> bytearray:
        """Handle .ascii directive"""
        if node.arguments:
            text = node.arguments[0].strip('"\'')
            data = text.encode('ascii')
            self.context.current_address += len(data)
            self.symbol_table.set_current_address(self.context.current_address)
            return bytearray(data)
        return bytearray()
    
    def _handle_asciiz_directive(self, node: DirectiveNode) -> bytearray:
        """Handle .asciiz directive"""
        if node.arguments:
            text = node.arguments[0].strip('"\'')
            data = text.encode('ascii') + b'\x00'
            self.context.current_address += len(data)
            self.symbol_table.set_current_address(self.context.current_address)
            return bytearray(data)
        return bytearray()
    
    def _handle_section_directive(self, node: DirectiveNode) -> Optional[bytearray]:
        """Handle .section directive"""
        if node.arguments:
            self.context.current_section = node.arguments[0]
        return None
    
    def _handle_global_directive(self, node: DirectiveNode) -> Optional[bytearray]:
        """Handle .global directive"""
        # Mark symbols as global
        for symbol_name in node.arguments:
            symbol = self.symbol_table.get_symbol(symbol_name)
            if symbol:
                symbol.scope = SymbolScope.GLOBAL
        return None
    
    def _handle_equ_directive(self, node: DirectiveNode) -> Optional[bytearray]:
        """Handle .equ directive"""
        if len(node.arguments) >= 2:
            name = node.arguments[0]
            value = self._parse_number(node.arguments[1])
            self.symbol_table.define_constant(name, value)
        return None
    
    def _handle_align_directive(self, node: DirectiveNode) -> Optional[bytearray]:
        """Handle .align directive"""
        if node.arguments:
            alignment = self._parse_number(node.arguments[0])
            # Align current address to specified boundary
            remainder = self.context.current_address % alignment
            if remainder:
                padding = alignment - remainder
                self.context.current_address += padding
                self.symbol_table.set_current_address(self.context.current_address)
                return bytearray(b'\x00' * padding)
        return None
    
    def _handle_custom_directive(self, node: DirectiveNode) -> Optional[bytearray]:
        """Handle custom directive defined in ISA"""
        directive = self.isa_definition.directives.get(node.name)
        if not directive:
            return None
        
        # If the directive has a custom implementation, execute it
        if directive.implementation:
            from .directive_executor import get_directive_executor, DirectiveContext
            executor = get_directive_executor()
            context = DirectiveContext(
                assembler=self,
                symbol_table=self.symbol_table,
                memory=bytearray(),  # Provide an empty bytearray by default
                current_address=self.context.current_address,
                section=self.context.current_section,
                args=node.arguments,
                extra={}
            )
            result = executor.execute_directive(directive.name, context)
            # If the directive implementation sets 'result' to a bytearray or bytes, return it
            if isinstance(result, (bytearray, bytes)):
                # Convert bytes to bytearray if needed
                if isinstance(result, bytes):
                    result = bytearray(result)
                self.context.current_address = context.current_address
                self.symbol_table.set_current_address(self.context.current_address)
                return result
            return None
        
        action = directive.action
        if action == "allocate_bytes":
            return self._handle_word_directive(node)
        elif action == "allocate_space":
            return self._handle_space_directive(node)
        elif action == "allocate_string":
            return self._handle_ascii_directive(node)
        elif action == "set_section":
            return self._handle_section_directive(node)
        elif action == "align_counter":
            return self._handle_align_directive(node)
        elif action == "define_constant":
            return self._handle_equ_directive(node)
        # elif action == "allocate_crazy":
        #     return self._handle_crazy_directive(node)
        
        return None
    
    def _handle_crazy_directive(self, node: DirectiveNode) -> bytearray:
        """Handle .crazy directive - creates magic data"""
        data = bytearray()
        word_size = self.isa_definition.word_size // 8
        
        for arg in node.arguments:
            value = self._parse_number(arg)
            # Add some "magic" to the value
            magic_value = value ^ 0xCAFEBABE
            endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
            word_bytes = int_to_bytes(magic_value, word_size, endianness)
            data.extend(word_bytes)
        
        self.context.current_address += len(data)
        self.symbol_table.set_current_address(self.context.current_address)
        return data
    
    def _find_entry_point(self) -> Optional[int]:
        """Find the entry point of the program"""
        # Look for common entry point labels
        entry_labels = ['_start', 'main', 'start', 'entry']
        
        for label in entry_labels:
            symbol = self.symbol_table.get_symbol(label)
            if symbol and symbol.defined:
                return symbol.value
        
        # Default to address 0 if no entry point found
        return 0

    def _expand_pseudo_instruction(self, node: InstructionNode, instruction_address: Optional[int] = None) -> List[InstructionNode]:
        """Expand a pseudo-instruction node into real instructions, recursively if needed."""
        pseudo = None
        for p in getattr(self.isa_definition, 'pseudo_instructions', []):
            if (p.mnemonic.upper() if not self.isa_definition.assembly_syntax.case_sensitive else p.mnemonic) == (node.mnemonic.upper() if not self.isa_definition.assembly_syntax.case_sensitive else node.mnemonic):
                pseudo = p
                break
        if not pseudo:
            raise AssemblerError(f"Unknown instruction: {node.mnemonic}")
        expansion = pseudo.expansion
        if not expansion:
            raise AssemblerError(f"Pseudo-instruction '{node.mnemonic}' has no expansion defined")
        
        # Store the current address for LA instruction expansion
        # Use the passed instruction address if available, otherwise use current address
        if instruction_address is not None:
            la_instruction_address = instruction_address
        else:
            la_instruction_address = self.context.current_address
        
        # Build operand map based on pseudo-instruction syntax
        operand_map = {}
        
        # Parse the syntax to understand operand names
        syntax_parts = pseudo.syntax.split()
        if len(syntax_parts) > 1:
            # Remove the mnemonic and join the rest, then split by comma
            operand_str = ' '.join(syntax_parts[1:])
            operand_names = [part.strip() for part in operand_str.split(',') if part.strip()]
            for i, (op, name) in enumerate(zip(node.operands, operand_names)):
                operand_map[f"${name}"] = str(op.value)
                operand_map[name] = str(op.value)
                # Also add generic names for this operand
                operand_map[f"$op{i+1}"] = str(op.value)
                operand_map[f"op{i+1}"] = str(op.value)
                operand_map[f"${i+1}"] = str(op.value)
                if str(i+1) not in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                    operand_map[f"{i+1}"] = str(op.value)
        
        # Handle bit field extractions generically based on expansion patterns
        expanded_text = expansion
        import re
        bitfield_pattern = re.compile(r'(\w+)\[(\d+):(\d+)\]')

        # Replace all bitfield patterns in the expansion string
        def bitfield_replacer(match):
            operand_name, high_str, low_str = match.group(1), match.group(2), match.group(3)
            key = f"${operand_name}" if f"${operand_name}" in operand_map else operand_name
            if key not in operand_map:
                return match.group(0)  # leave as is if not found
            v = operand_map[key]
            try:
                high = int(high_str)
                low = int(low_str)
                width = high - low + 1
                mask = (1 << width) - 1
                # Handle both passes
                # Check if this is a label (either operand_name is "label" or the value is a symbol)
                # In first pass, assume any non-numeric value is a label
                # In second pass, check if it's actually a symbol
                try:
                    # Try to parse as number
                    test_value = self._parse_number(v)
                    is_label = False
                except:
                    # If it's not a number, it's probably a label
                    is_label = True
                
                # In second pass, also check if it's a defined symbol
                if self.context.pass_number == 2 and self.symbol_table.get_symbol(v) is not None:
                    is_label = True
                
                if is_label:
                    try:
                        if self.context.pass_number == 2:
                            symbol = self.symbol_table.get_symbol(v)
                            value = self._resolve_address_operand(OperandNode(v, "label", 0, 0, None))
                            # Modular fix: for LA, use (label_address - current_PC) for bitfield extraction
                            if node.mnemonic.upper() == "LA":
                                offset = value - la_instruction_address
                                bitfield_value = (offset >> low) & mask
                                return str(bitfield_value)
                            else:
                                bitfield_value = (value >> low) & mask
                                return str(bitfield_value)
                        else:
                            # First pass: use 0 as placeholder
                            return "0"
                    except Exception as e:
                        return "0"
                else:
                    try:
                        value = self._parse_number(v)
                        bitfield_value = (value >> low) & mask
                        return str(bitfield_value)
                    except Exception as e:
                        return match.group(0)
            except Exception as e:
                return match.group(0)

        # Replace all bitfield patterns first
        expanded_text = bitfield_pattern.sub(bitfield_replacer, expanded_text)

        # Don't remove remaining bitfield patterns - they should be handled properly
        # expanded_text = bitfield_pattern.sub('', expanded_text)

        # Now do operand substitution only for standalone placeholders
        for k, v in sorted(operand_map.items(), key=lambda x: -len(x[0])):
            pattern = r'(?<![\w.])' + re.escape(k) + r'(?![\w.])'
            expanded_text = re.sub(pattern, v, expanded_text)

        expanded_instrs = [s.strip() for s in expanded_text.split(';') if s.strip()]
        parser = Parser(self.isa_definition)
        nodes = []
        for instr in expanded_instrs:
            parsed = parser.parse(instr)
            for n in parsed:
                if isinstance(n, InstructionNode):
                    if not self._find_instruction(n.mnemonic):
                        nodes.extend(self._expand_pseudo_instruction(n))
                    else:
                        nodes.append(n)
        return nodes

    def _get_bit_width(self, bits: str) -> int:
        """Get bit width from bit range string like '15:12'"""
        try:
            high, low = parse_bit_range(bits)
            return high - low + 1
        except ValueError:
            return 0
    
    def _insert_field(self, instruction_word: int, bits: str, field_value: int) -> int:
        """Insert field value into instruction word at specified bit positions"""
        try:
            high, low = parse_bit_range(bits)
            return set_bits(instruction_word, high, low, field_value)
        except ValueError:
            return instruction_word

    def _serialize_symbol_table(self) -> str:
        """Serialize symbol table to JSON string for storage in binary"""
        import json
        
        symbol_data = {}
        for name, symbol in self.symbol_table.symbols.items():
            if symbol.defined:  # Only include defined symbols
                symbol_data[name] = {
                    'name': symbol.name,
                    'value': symbol.value,
                    'type': symbol.type.value,
                    'scope': symbol.scope.value,
                    'size': symbol.size
                }
        
        return json.dumps(symbol_data, separators=(',', ':'))  # Compact JSON
