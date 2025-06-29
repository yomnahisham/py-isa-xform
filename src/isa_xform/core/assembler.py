"""
Assembler: Converts assembly language to machine code
"""

import struct
from enum import Enum
from typing import List, Optional, Dict, Any, Union, Tuple
from dataclasses import dataclass, field

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


@dataclass 
class AssembledCode:
    """Result of assembly process"""
    machine_code: bytearray
    symbol_table: SymbolTable
    entry_point: Optional[int] = None
    sections: Optional[Dict[str, Tuple[int, int]]] = None  # section_name: (start_addr, size)


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
            entry_point=self._find_entry_point()
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
        """Second pass: generate machine code"""
        machine_code = bytearray()
        # Start at the address set by .org in the first pass
        self.context.current_address = self.symbol_table.current_address if self.context.origin_set else 0

        for node in nodes:
            if isinstance(node, LabelNode):
                # Labels don't generate code, just update address
                pass
            elif isinstance(node, InstructionNode):
                code = self._assemble_instruction(node)
                machine_code.extend(code)
            elif isinstance(node, DirectiveNode):
                code = self._handle_directive_second_pass(node)
                if code:
                    machine_code.extend(code)
        
        return machine_code
    
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
        self.symbol_table.define_label(node.name, node.line, node.column, node.file)
    
    def _advance_address_for_instruction(self, node: InstructionNode):
        """Advance address for instruction during first pass"""
        instruction = self._find_instruction(node.mnemonic)
        if instruction:
            self.context.current_address += self.instruction_size_bytes
            self.symbol_table.set_current_address(self.context.current_address)
    
    def _assemble_instruction(self, node: InstructionNode) -> bytearray:
        """Assemble a single instruction"""
        instruction = self._find_instruction(node.mnemonic)
        if not instruction:
            raise AssemblerError(f"Unknown instruction: {node.mnemonic}")
        
        # Encode the instruction based on its format
        encoded = self._encode_instruction(instruction, node.operands)
        
        # Convert to bytes using bit utilities
        endianness = 'little' if self.isa_definition.endianness.lower().startswith('little') else 'big'
        instruction_bytes = int_to_bytes(encoded, self.instruction_size_bytes, endianness)
        
        # Update address
        self.context.current_address += self.instruction_size_bytes
        self.symbol_table.set_current_address(self.context.current_address)
        
        return bytearray(instruction_bytes)
    
    def _encode_instruction(self, instruction: Instruction, operands: List[OperandNode]) -> int:
        """Encode instruction with operands"""
        encoding = instruction.encoding
        instruction_word = 0
        
        if isinstance(encoding, dict) and "fields" in encoding:
            # Modern field-based encoding
            instruction_word = self._encode_with_fields(encoding["fields"], operands)
        else:
            # Legacy encoding format - handle as best we can
            instruction_word = self._encode_legacy_format(instruction, operands)
        
        return instruction_word
    
    def _encode_with_fields(self, fields: List[Dict[str, Any]], operands: List[OperandNode]) -> int:
        """Encode instruction using field definitions"""
        instruction_word = 0
        
        # Map operands to fields based on instruction syntax and field names
        field_values = {}
        operand_mapping = self._map_operands_to_fields(fields, operands)
        
        for field in fields:
            field_name = field.get("name", "")
            bits = field.get("bits", "")
            field_type = field.get("type", "")
            
            try:
                # Parse bit range using bit utilities
                high, low = parse_bit_range(bits)
                bit_width = high - low + 1
                
                # Get field value
                if "value" in field:
                    # Fixed value field (like opcode)
                    value = field["value"]
                    if isinstance(value, str):
                        field_value = int(value, 2) if value else 0
                    else:
                        field_value = int(value)
                    field_values[field_name] = field_value
                else:
                    # Variable field (operand) - get from mapping
                    if field_name in operand_mapping:
                        operand = operand_mapping[field_name]
                        field_value = self._resolve_operand_value(operand, field_type, bit_width, field.get("signed", False))
                        field_values[field_name] = field_value
                    else:
                        field_values[field_name] = 0
                
                # Set bits using bit utilities
                instruction_word = set_bits(instruction_word, high, low, field_values[field_name])
            except ValueError:
                # Skip invalid bit ranges
                continue
        
        return instruction_word
    
    def _map_operands_to_fields(self, fields: List[Dict[str, Any]], operands: List[OperandNode]) -> Dict[str, OperandNode]:
        """Map operands to field names based on instruction syntax"""
        mapping = {}
        
        # Get field names that expect operands
        operand_fields = [f for f in fields if "type" in f and f.get("name") != "opcode"]
        
        # For memory instructions, we need to map operands to specific fields
        # based on the instruction syntax and field names
        if len(operands) == 2 and any(op.type == "mem" for op in operands):
            # This is likely a memory instruction like ST or LD
            for field in operand_fields:
                field_name = field.get("name", "")
                field_type = field.get("type", "")
                
                if field_name == "rd" and len(operands) > 0:
                    # First operand is the register (for LD)
                    mapping[field_name] = operands[0]
                elif field_name == "rs2" and len(operands) > 0:
                    # First operand is the value to store (for ST)
                    mapping[field_name] = operands[0]
                elif field_name in ["rs1", "offset"] and len(operands) > 1:
                    # Second operand is the memory operand
                    mem_operand = operands[1]
                    if mem_operand.type == "mem":
                        offset_node, reg_node = mem_operand.value
                        if field_name == "rs1":
                            mapping[field_name] = reg_node
                        elif field_name == "offset":
                            mapping[field_name] = offset_node
        else:
            # Handle different instruction formats
            # Check if this is a B-type instruction (3 operands: rs1, rs2, offset)
            if len(operands) == 3 and any(f.get("name") == "imm" for f in operand_fields):
                # B-type instruction: BEQ rs1, rs2, offset
                for field in operand_fields:
                    field_name = field.get("name", "")
                    if field_name == "rs1" and len(operands) > 0:
                        mapping[field_name] = operands[0]  # First operand
                    elif field_name == "rs2" and len(operands) > 1:
                        mapping[field_name] = operands[1]  # Second operand
                    elif field_name == "imm" and len(operands) > 2:
                        mapping[field_name] = operands[2]  # Third operand
            else:
                # Handle ZX16 two-operand format: rd = rd op rs2
                # For R-type instructions: ADD rd, rs2 -> rd = rd + rs2
                # For I-type instructions: ADDI rd, imm -> rd = rd + imm
                
                # Map operands based on field names and instruction format
                for field in operand_fields:
                    field_name = field.get("name", "")
                    field_type = field.get("type", "")
                    
                    if field_name == "rd" and len(operands) > 0:
                        # First operand is destination register
                        mapping[field_name] = operands[0]
                    elif field_name == "rs1" and len(operands) > 0:
                        # For ZX16, rs1 is the same as rd (two-operand format)
                        # Use the same operand as rd
                        if "rd" in mapping:
                            mapping[field_name] = mapping["rd"]
                        else:
                            mapping[field_name] = operands[0]
                    elif field_name == "rs2" and len(operands) > 1:
                        # Second operand is source register
                        mapping[field_name] = operands[1]
                    elif field_name in ["imm", "offset"] and len(operands) > 1:
                        # Second operand is immediate or offset
                        mapping[field_name] = operands[1]
                    elif field_name in ["imm2", "svc"] and len(operands) > 2:
                        # Additional immediate fields (third operand)
                        mapping[field_name] = operands[2]
        
        return mapping
    
    def _encode_legacy_format(self, instruction: Instruction, operands: List[OperandNode]) -> int:
        """Encode instruction using legacy format"""
        # Try to extract opcode from instruction
        opcode = 0
        if hasattr(instruction, 'opcode') and instruction.opcode:
            try:
                opcode = int(instruction.opcode, 2)
            except ValueError:
                opcode = 0
        
        # Simple encoding based on instruction format
        if instruction.format == "R-type":
            # R-type: opcode | rd | rs1 | rs2
            instruction_word = opcode << 12
            if len(operands) >= 1:
                rd = self._resolve_register_operand(operands[0])
                instruction_word = set_bits(instruction_word, 11, 8, rd)
            if len(operands) >= 2:
                rs1 = self._resolve_register_operand(operands[1])
                instruction_word = set_bits(instruction_word, 7, 4, rs1)
            if len(operands) >= 3:
                rs2 = self._resolve_register_operand(operands[2])
                instruction_word = set_bits(instruction_word, 3, 0, rs2)
        elif instruction.format == "I-type":
            # I-type: opcode | rd | rs1 | immediate
            instruction_word = opcode << 12
            if len(operands) >= 1:
                rd = self._resolve_register_operand(operands[0])
                instruction_word = set_bits(instruction_word, 11, 8, rd)
            if len(operands) >= 2:
                rs1 = self._resolve_register_operand(operands[1])
                instruction_word = set_bits(instruction_word, 7, 4, rs1)
            if len(operands) >= 3:
                imm = self._resolve_immediate_operand(operands[2])
                instruction_word = set_bits(instruction_word, 3, 0, imm)
        elif instruction.format == "J-type":
            # J-type: opcode | address
            instruction_word = opcode << 12
            if len(operands) >= 1:
                addr = self._resolve_address_operand(operands[0])
                instruction_word = set_bits(instruction_word, 11, 0, addr)
        
        return instruction_word
    
    def _resolve_operand_value(self, operand: OperandNode, field_type: str, bit_width: int, signed: bool = False) -> int:
        """Resolve operand value based on field type"""
        if field_type == "register":
            return self._resolve_register_operand(operand)
        elif field_type == "immediate":
            value = self._resolve_immediate_operand(operand)
            # Validate immediate fits in bit width
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
            return self._resolve_address_operand(operand)
        else:
            raise AssemblerError(f"Unknown field type: {field_type}")
    
    def _resolve_register_operand(self, operand: OperandNode) -> int:
        """Resolve register operand to register number"""
        reg_name = operand.value
        
        # Remove register prefix if present
        syntax = self.isa_definition.assembly_syntax
        if reg_name.startswith(syntax.register_prefix):
            reg_name = reg_name[len(syntax.register_prefix):]
        
        # Search all register categories
        for category, registers in self.isa_definition.registers.items():
            for i, register in enumerate(registers):
                # Check main name
                reg_cmp = register.name if syntax.case_sensitive else register.name.upper()
                operand_cmp = reg_name if syntax.case_sensitive else reg_name.upper()
                if reg_cmp == operand_cmp:
                    return i
                
                # Check aliases
                for alias in register.alias:
                    alias_cmp = alias if syntax.case_sensitive else alias.upper()
                    if alias_cmp == operand_cmp:
                        return i
        
        raise AssemblerError(f"Unknown register: {operand.value}")
    
    def _resolve_immediate_operand(self, operand: OperandNode) -> int:
        """Resolve immediate operand to integer value"""
        value_str = operand.value
        syntax = self.isa_definition.assembly_syntax
        
        # Remove immediate prefix if present
        if value_str.startswith(syntax.immediate_prefix):
            value_str = value_str[len(syntax.immediate_prefix):]
        
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
        elif action == "allocate_crazy":
            return self._handle_crazy_directive(node)
        
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
