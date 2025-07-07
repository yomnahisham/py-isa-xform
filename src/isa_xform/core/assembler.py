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
        self.context.current_address = 0
        
        for node in nodes:
            if isinstance(node, LabelNode):
                self._handle_label_definition(node)
            elif isinstance(node, InstructionNode):
                self._advance_address_for_instruction(node)
            elif isinstance(node, DirectiveNode):
                self._handle_directive_first_pass(node)
    
    def _second_pass(self, nodes: List[ASTNode]) -> bytearray:
        """Second pass: generate machine code with section header"""
        # Get ISA memory layout
        data_section_start = self.isa_definition.address_space.memory_layout.get('data_section', {}).get('start', 0)
        code_section_start = self.isa_definition.address_space.memory_layout.get('code_section', {}).get('start', 0)
        
        # Collect code and data sections
        code_bytes = bytearray()
        data_bytes = bytearray()
        current_section = "text"
        self.context.current_address = self.context.org_address

        for node in nodes:
            if isinstance(node, LabelNode):
                pass
            elif isinstance(node, DirectiveNode):
                if node.name.lower() == '.data':
                    current_section = "data"
                elif node.name.lower() == '.text':
                    current_section = "text"
                elif node.name.lower() == '.org':
                    # .org handled in first pass
                    pass
                else:
                    # Use directive handler dispatch
                    handler = self.directive_handlers.get(node.name.lower())
                    if handler:
                        # Automatically detect data directives and put them in data section
                        data_directives = {'.word', '.byte', '.space', '.ascii', '.asciiz'}
                        if node.name.lower() in data_directives or current_section == "data":
                            data_bytes.extend(handler(node) or b"")
                        else:
                            code_bytes.extend(handler(node) or b"")
            elif isinstance(node, InstructionNode):
                code = self._assemble_instruction(node)
                code_bytes.extend(code)
        
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
        header.extend(data_section_start.to_bytes(4, 'little'))  # Data start (4 bytes)
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
            expanded_nodes = self._expand_pseudo_instruction(node)
            for n in expanded_nodes:
                self._advance_address_for_instruction(n)
    
    def _assemble_instruction(self, node: InstructionNode) -> bytearray:
        """Assemble a single instruction, expanding pseudo-instructions if needed"""
        instruction = self._find_instruction(node.mnemonic)
        if not instruction:
            # Try pseudo-instruction expansion
            expanded_nodes = self._expand_pseudo_instruction(node)
            code = bytearray()
            for n in expanded_nodes:
                code.extend(self._assemble_instruction(n))
            return code
        # --- FIX: Capture the address of this instruction before encoding ---
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
        
        # --- PATCH: For multi-field immediates (like LUI), map the same immediate operand to all immediate fields ---
        # If there is exactly one immediate operand and multiple immediate fields, map to all
        immediate_fields = [f for f in fields if f.get("type") == "immediate" and f.get("name") != "opcode"]
        immediate_operands = [op for op in operands if getattr(op, 'type', None) == 'immediate']
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
                # Modular offset calculation: get offset_base from field or encoding
                offset_base = None
                if field and "offset_base" in field:
                    offset_base = field["offset_base"]
                elif instruction and hasattr(instruction, "encoding") and isinstance(instruction.encoding, dict):
                    offset_base = instruction.encoding.get("offset_base", "current")
                else:
                    offset_base = "current"
                target_address = self._resolve_address_operand(operand)
                if offset_base == "current":
                    offset = target_address - instruction_address
                elif offset_base == "next":
                    offset = target_address - (instruction_address + self.instruction_size_bytes)
                elif isinstance(offset_base, int):
                    offset = target_address - (instruction_address + offset_base)
                else:
                    # fallback to current
                    offset = target_address - instruction_address
                return offset
            else:
                # Treat as literal immediate value
                value = self._resolve_immediate_operand(operand)

            # Handle multi-field immediates
            if field and "bits" in field and instruction and hasattr(instruction, "encoding"):
                encoding_fields = instruction.encoding.get("fields", [])
                immediate_fields = [f for f in encoding_fields if f.get("type") == "immediate" and f.get("name") != "opcode"]
                if len(immediate_fields) > 1:
                    # Sort fields by order in encoding (or by width, but order is more robust)
                    field_widths = []
                    for f in immediate_fields:
                        bits = f.get("bits", "")
                        if ":" in bits:
                            high, low = [int(x) for x in bits.split(":")]
                        else:
                            high = low = int(bits)
                        width = high - low + 1
                        field_widths.append((f["name"], width))
                    # Use order in encoding
                    field_widths = [(f["name"], width) for f, width in zip(immediate_fields, [w for _, w in field_widths])]
                    # Compute bit offsets for each field (lowest bits to first field, next bits to next, etc.)
                    bit_offsets = []
                    offset = 0
                    for fname, width in field_widths:
                        bit_offsets.append((fname, offset, width))
                        offset += width
                    # For this field, extract the correct bits from the user immediate
                    for fname, bit_offset, width in bit_offsets:
                        if fname == field_name:
                            extracted_value = (value >> bit_offset) & ((1 << width) - 1)
                            return extracted_value

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
        elif field_type == "address":
            # For address fields, use absolute address
            return self._resolve_address_operand(operand)
        else:
            # Default to immediate value
            return self._resolve_immediate_operand(operand)
    
    def _resolve_register_operand(self, operand: OperandNode) -> int:
        """Resolve register operand to register number (modular, supports register objects and names)"""
        reg_val = operand.value
        syntax = self.isa_definition.assembly_syntax
        # If it's a register object (from OperandParser), match by object
        if hasattr(reg_val, 'name') and hasattr(reg_val, 'alias'):
            for category, registers in self.isa_definition.registers.items():
                for i, register in enumerate(registers):
                    if register is reg_val:
                        return i
        # Otherwise, treat as string (name or alias)
        reg_name = reg_val
        if isinstance(reg_name, str) and reg_name.startswith(syntax.register_prefix):
            reg_name = reg_name[len(syntax.register_prefix):]
        for category, registers in self.isa_definition.registers.items():
            for i, register in enumerate(registers):
                reg_cmp = register.name if syntax.case_sensitive else register.name.upper()
                operand_cmp = reg_name if syntax.case_sensitive else reg_name.upper()
                if reg_cmp == operand_cmp:
                    return i
                for alias in register.alias:
                    alias_cmp = alias if syntax.case_sensitive else alias.upper()
                    if alias_cmp == operand_cmp:
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
        
        syntax = self.isa_definition.assembly_syntax
        
        # Remove immediate prefix if present
        if isinstance(value_str, str) and value_str.startswith(syntax.immediate_prefix):
            value_str = value_str[len(syntax.immediate_prefix):]
        
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
        """Parse number string to integer"""
        syntax = self.isa_definition.assembly_syntax
        
        try:
            # Handle different number formats based on ISA syntax
            if value_str.startswith(syntax.hex_prefix):
                return int(value_str, 16)
            elif value_str.startswith(syntax.binary_prefix):
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
        elif directive_name in ['.word', '.byte']:
            # Calculate space needed
            size = 4 if directive_name == '.word' else 1  # Use word size from ISA
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
                    size = 4  # Use word size from ISA
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

    def _expand_pseudo_instruction(self, node: InstructionNode) -> List[InstructionNode]:
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
                if operand_name == "label":
                    try:
                        if self.context.pass_number == 2:
                            symbol = self.symbol_table.get_symbol(v)
                            value = self._resolve_address_operand(OperandNode(v, "label"))
                        else:
                            # First pass: use 0 as placeholder
                            value = 0
                    except Exception:
                        value = 0
                else:
                    try:
                        value = self._parse_number(v)
                    except Exception:
                        return match.group(0)
                
                bitfield_value = (value >> low) & mask
                return str(bitfield_value)
            except Exception:
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
