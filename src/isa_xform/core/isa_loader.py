"""
ISA Loader: Loads and validates instruction set architecture definitions
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from jsonschema import validate, ValidationError
import importlib.resources

from isa_xform.utils.error_handling import ISALoadError, ISAValidationError
from isa_xform.utils.bit_utils import (
    extract_bits, set_bits, sign_extend, parse_bit_range,
    create_mask, bytes_to_int, int_to_bytes
)


@dataclass
class Register:
    """Represents a register definition"""
    name: str
    size: int
    number: int = 0
    alias: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class Instruction:
    """Represents an instruction definition"""
    mnemonic: str
    opcode: str
    format: str
    description: str
    encoding: Dict[str, Any]
    syntax: str
    semantics: str
    flags_affected: List[str] = field(default_factory=list)
    length: Optional[int] = None  # Optional explicit instruction length in bits
    implementation: str = "" # Added implementation field


@dataclass
class OperandPattern:
    """Represents an operand pattern for parsing"""
    name: str
    type: str  # register, immediate, address, label, etc.
    pattern: str  # regex pattern for matching
    description: str
    examples: List[str] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InstructionFormat:
    """Represents an instruction format definition"""
    name: str
    description: str
    operand_patterns: List[OperandPattern]
    encoding_template: Dict[str, Any]
    examples: List[str] = field(default_factory=list)


@dataclass
class Directive:
    """Represents a directive definition"""
    name: str
    description: str
    action: str
    argument_types: List[str] = field(default_factory=list)
    handler: Optional[str] = None
    syntax: str = ""
    examples: List[str] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PseudoInstruction:
    """Represents a pseudo-instruction definition"""
    mnemonic: str
    description: str
    syntax: str
    expansion: str
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    disassembly: Dict[str, Any] = field(default_factory=dict)
    smart_expansion: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AddressingMode:
    """Represents an addressing mode definition"""
    name: str
    syntax: str
    description: str
    pattern: Optional[str] = None
    operand_types: List[str] = field(default_factory=list)


@dataclass
class ECallService:
    """Represents an ecall service definition"""
    name: str
    description: str
    parameters: Dict[str, str] = field(default_factory=dict)
    return_value: str = "None"


@dataclass
class Constant:
    """Represents a constant definition"""
    name: str
    value: int
    description: Optional[str] = None


@dataclass
class AssemblySyntax:
    """Represents assembly syntax rules"""
    comment_char: str = ";"
    comment_chars: List[str] = field(default_factory=list)  # For multiple comment characters
    label_suffix: str = ":"
    register_prefix: str = "$"
    immediate_prefix: str = "#" 
    hex_prefix: str = "0x"
    binary_prefix: str = "0b"
    case_sensitive: bool = False
    directives: List[str] = field(default_factory=list)
    operand_separators: List[str] = field(default_factory=lambda: [",", " "])
    whitespace_handling: str = "flexible"  # strict, flexible, minimal
    
    def __post_init__(self):
        """Ensure comment_chars includes comment_char for compatibility"""
        if not self.comment_chars:
            self.comment_chars = [self.comment_char]
        elif self.comment_char not in self.comment_chars:
            # If comment_chars is specified but doesn't include comment_char, use the first one
            self.comment_char = self.comment_chars[0]


@dataclass
class AddressSpace:
    """Represents address space configuration"""
    default_code_start: int = 0
    default_data_start: int = 0
    default_stack_start: int = 0
    memory_layout: Dict[str, Dict[str, int]] = field(default_factory=dict)
    alignment_requirements: Dict[str, int] = field(default_factory=dict)


@dataclass
class ISADefinition:
    """Complete ISA definition"""
    name: str
    version: str
    description: str
    word_size: int
    endianness: str
    instruction_size: int
    registers: Dict[str, List[Register]]
    instructions: List[Instruction]
    instruction_formats: Dict[str, InstructionFormat] = field(default_factory=dict)
    operand_patterns: Dict[str, OperandPattern] = field(default_factory=dict)
    pseudo_instructions: List[PseudoInstruction] = field(default_factory=list)
    directives: Dict[str, Directive] = field(default_factory=dict)
    addressing_modes: List[AddressingMode] = field(default_factory=list)
    assembly_syntax: AssemblySyntax = field(default_factory=AssemblySyntax)
    address_space: AddressSpace = field(default_factory=AddressSpace)
    pc_behavior: Dict[str, Any] = field(default_factory=dict)
    instruction_architecture: Dict[str, Any] = field(default_factory=dict)
    register_formatting: Dict[str, Any] = field(default_factory=dict)
    operand_formatting: Dict[str, Any] = field(default_factory=dict)
    instruction_categories: Dict[str, Any] = field(default_factory=dict)
    pseudo_instruction_fallbacks: Dict[str, Any] = field(default_factory=dict)
    data_detection: Dict[str, Any] = field(default_factory=dict)
    symbol_resolution: Dict[str, Any] = field(default_factory=dict)
    error_messages: Dict[str, Any] = field(default_factory=dict)
    constants: Dict[str, Constant] = field(default_factory=dict)
    ecall_services: Dict[str, ECallService] = field(default_factory=dict) 
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Universal ISA support fields
    variable_length_instructions: bool = False
    instruction_length_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize ISA-derived constants and validate configuration"""
        self._init_isa_constants()
        self._validate_isa_config()
    
    def _init_isa_constants(self):
        """Initialize ISA-derived constants for modular operation"""
        # Word size derived constants
        self.word_mask = (1 << self.word_size) - 1
        self.sign_bit_mask = 1 << (self.word_size - 1)
        self.max_signed_value = (1 << (self.word_size - 1)) - 1
        self.min_signed_value = -(1 << (self.word_size - 1))
        
        # Instruction size derived constants
        self.instruction_size_bytes = self.instruction_size // 8
        
        # Variable-length instruction support
        self.variable_length_instructions = self.instruction_length_config.get('enabled', False)
        if self.variable_length_instructions:
            self.length_determination = self.instruction_length_config.get('length_determination', {})
            self.length_table = self.instruction_length_config.get('length_table', {})
            self.max_instruction_length = self.instruction_length_config.get('max_instruction_length', self.instruction_size)
        else:
            self.max_instruction_length = self.instruction_size
        
        # Address space derived constants
        if hasattr(self, 'address_space') and self.address_space:
            # Check if address_space has a size attribute (from instruction_architecture)
            if hasattr(self, 'instruction_architecture') and self.instruction_architecture:
                addr_bits = self.instruction_architecture.get('address_bits', self.word_size)
                self.address_space_size = 1 << addr_bits
                self.address_mask = (1 << addr_bits) - 1
            else:
                # Default to word_size if not specified
                self.address_space_size = 1 << self.word_size
                self.address_mask = self.word_mask
        
        # Register count derived constants
        self.register_count = 0
        if self.registers:
            for reg_list in self.registers.values():
                self.register_count += len(reg_list)
        
        # Immediate widths from instruction_architecture
        self.immediate_widths = self.instruction_architecture.get('immediate_widths', {})
        self.shift_config = self.instruction_architecture.get('shift_config', {})
        
        # PC behavior constants
        self.pc_increment = self.instruction_architecture.get('pc_increment', self.instruction_size_bytes)
        
        # Initialize constants if not already present
        if not self.constants:
            self.constants = {}
        
        # Add ISA-derived constants
        self.constants.update({
            'word_mask': Constant('word_mask', self.word_mask, 'Word size mask'),
            'sign_bit_mask': Constant('sign_bit_mask', self.sign_bit_mask, 'Sign bit mask'),
            'max_signed_value': Constant('max_signed_value', self.max_signed_value, 'Maximum signed value'),
            'min_signed_value': Constant('min_signed_value', self.min_signed_value, 'Minimum signed value'),
            'address_mask': Constant('address_mask', self.address_mask, 'Address space mask'),
            'register_count': Constant('register_count', self.register_count, 'Number of registers')
        })
    
    def get_instruction_length(self, instruction: Instruction, encoded_value: int = 0) -> int:
        """Get the length of an instruction in bits"""
        if not self.variable_length_instructions:
            return self.instruction_size
        
        # Check if instruction has explicit length
        if hasattr(instruction, 'length') and instruction.length:
            return instruction.length
        
        # Check length table based on opcode
        if self.length_table:
            # Extract opcode from encoded value or instruction
            opcode = self._extract_opcode_for_length(instruction, encoded_value)
            if opcode in self.length_table:
                return self.length_table[opcode]
        
        # Default to base instruction size
        return self.instruction_size
    
    def _extract_opcode_for_length(self, instruction: Instruction, encoded_value: int = 0) -> str:
        """Extract opcode for length determination"""
        # Try to get opcode from instruction definition first
        if hasattr(instruction, 'opcode') and instruction.opcode:
            return instruction.opcode
        
        # Try to extract from encoding fields
        if hasattr(instruction, 'encoding') and isinstance(instruction.encoding, dict):
            fields = instruction.encoding.get('fields', [])
            for field in fields:
                if field.get('name') == 'opcode' and 'value' in field:
                    return field['value']
        
        # Try to extract from encoded value if provided
        if encoded_value > 0:
            # This is a simplified extraction - in practice, you'd need to know the opcode field position
            # For now, return a default
            return "0x00"
        
        return "0x00"
    
    def _validate_isa_config(self):
        """Validate ISA configuration for consistency"""
        # Validate word size and instruction size
        if self.word_size <= 0:
            raise ValueError(f"Invalid word_size: {self.word_size}")
        if self.instruction_size <= 0:
            raise ValueError(f"Invalid instruction_size: {self.instruction_size}")
        if self.instruction_size % 8 != 0:
            raise ValueError(f"Instruction size must be multiple of 8: {self.instruction_size}")
        
        # Validate variable-length configuration
        if self.variable_length_instructions:
            if not self.instruction_length_config:
                raise ValueError("Variable-length instructions enabled but no length configuration provided")
            
            length_determination = self.instruction_length_config.get('length_determination', {})
            if not length_determination:
                raise ValueError("Variable-length instructions require length_determination configuration")
            
            # Validate length table if provided
            length_table = self.instruction_length_config.get('length_table', {})
            for opcode, length in length_table.items():
                if length <= 0 or length % 8 != 0:
                    raise ValueError(f"Invalid instruction length for opcode {opcode}: {length}")
        
        # Validate endianness
        if self.endianness.lower() not in ['little', 'big']:
            raise ValueError(f"Invalid endianness: {self.endianness}")
        
        # Validate register count
        if self.register_count == 0:
            raise ValueError("ISA must have at least one register")
        
        # Validate address space
        if hasattr(self, 'address_space_size') and self.address_space_size <= 0:
            raise ValueError(f"Invalid address space size: {self.address_space_size}")
    
    def get_immediate_sign_bit(self, immediate_width: int) -> int:
        """Get sign bit mask for immediate of given width"""
        return 1 << (immediate_width - 1)
    
    def get_immediate_sign_extend(self, immediate_width: int) -> int:
        """Get sign extension mask for immediate of given width"""
        return ((1 << (self.word_size - immediate_width)) - 1) << immediate_width
    
    def get_shift_type_width(self) -> int:
        """Get shift type bit width from ISA configuration"""
        return self.shift_config.get('type_width', 3)  # Default to 3 for ZX16 compatibility
    
    def get_shift_amount_width(self) -> int:
        """Get shift amount bit width from ISA configuration"""
        return self.shift_config.get('amount_width', 4)  # Default to 4 for ZX16 compatibility
    
    def get_immediate_width(self, instruction_type: str) -> int:
        """Get immediate width for instruction type"""
        return self.immediate_widths.get(instruction_type, 7)  # Default to 7 for ZX16 compatibility


class ISALoader:
    """Loads and validates ISA definitions"""
    
    def __init__(self):
        self._cache: Dict[str, ISADefinition] = {}
        self._builtin_path = Path(__file__).parent.parent.parent / "isa_definitions"
    
    def load_isa(self, isa_name: str) -> ISADefinition:
        """Load an ISA definition by name"""
        if isa_name in self._cache:
            return self._cache[isa_name]
        
        isa_file = self._find_isa_file(isa_name)
        if isa_file:
            isa_def = self._load_from_file(isa_file)
            self._cache[isa_name] = isa_def
            return isa_def
        # Try to load from package resources
        try:
            import importlib.resources
            with importlib.resources.files("isa_definitions").joinpath(f"{isa_name}.json").open("r") as f:
                data = json.load(f)
            isa_def = self._parse_isa_data(data, Path(f"isa_definitions/{isa_name}.json"))
            self._cache[isa_name] = isa_def
            return isa_def
        except Exception as e:
            pass
        raise ISALoadError(f"ISA '{isa_name}' not found")
    
    def load_isa_from_file(self, file_path: Union[str, Path]) -> ISADefinition:
        """Load an ISA definition from a specific file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise ISALoadError(f"ISA file not found: {file_path}")
        
        return self._load_from_file(file_path)
        return self._load_from_file(file_path)
    
    def _find_isa_file(self, isa_name: str) -> Optional[Path]:
        """Find an ISA file by name"""
        # Try builtin path first (relative to this file)
        builtin_file = self._builtin_path / f"{isa_name}.json"
        if builtin_file.exists():
            return builtin_file
        
        # Try current directory
        current_file = Path(f"{isa_name}.json")
        if current_file.exists():
            return current_file
        
        # Fallback: try src/isa_xform/isa_definitions/ (for development/testing)
        src_isa_file = Path(__file__).parent.parent / "isa_definitions" / f"{isa_name}.json"
        if src_isa_file.exists():
            return src_isa_file
        
        return None
    
    def _load_from_file(self, file_path: Path) -> ISADefinition:
        """Load ISA definition from a file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ISALoadError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise ISALoadError(f"Error reading {file_path}: {e}")
        
        return self._parse_isa_data(data, file_path)
    
    def _parse_isa_data(self, data: Dict[str, Any], file_path: Path) -> ISADefinition:
        """Parse JSON data into ISADefinition object"""
        # Validate required fields
        required_fields = ["name", "version", "word_size", "endianness"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ISALoadError(f"Missing required fields in ISA definition: {', '.join(missing_fields)}")
        
        # Parse registers
        registers = {}
        for category, reg_list in data.get("registers", {}).items():
            registers[category] = []
            for reg_data in reg_list:
                register = Register(
                    name=reg_data["name"],
                    size=reg_data["size"],
                    number=reg_data.get("number", 0),
                    alias=reg_data.get("alias", []),
                    description=reg_data.get("description")
                )
                registers[category].append(register)
        
        # Parse instructions
        instructions = []
        for instr_data in data.get("instructions", []):
            instruction = Instruction(
                mnemonic=instr_data["mnemonic"],
                opcode=instr_data.get("opcode", ""),
                format=instr_data["format"],
                description=instr_data["description"],
                encoding=instr_data["encoding"],
                syntax=instr_data["syntax"],
                semantics=instr_data["semantics"],
                implementation=instr_data.get("implementation", ""),
                flags_affected=instr_data.get("flags_affected", []),
                length=instr_data.get("length")
            )
            instructions.append(instruction)

        # Parse pseudo-instructions
        pseudo_instructions = []
        for pseudo_data in data.get("pseudo_instructions", []):
            pseudo_instruction = PseudoInstruction(
                mnemonic=pseudo_data["mnemonic"],
                description=pseudo_data["description"],
                syntax=pseudo_data["syntax"],
                expansion=pseudo_data["expansion"],
                disassembly=pseudo_data.get("disassembly", {}),
                smart_expansion=pseudo_data.get("smart_expansion", {})
            )
            pseudo_instructions.append(pseudo_instruction)

        # Parse directives
        directives = {}
        for directive_data in data.get("directives", []):
            if isinstance(directive_data, dict):
                directive = Directive(
                    name=directive_data["name"],
                    description=directive_data["description"],
                    argument_types=directive_data.get("argument_types", []),
                    action=directive_data["action"],
                    handler=directive_data.get("handler"),
                    syntax=directive_data.get("syntax", ""),
                    examples=directive_data.get("examples", []),
                    validation_rules=directive_data.get("validation_rules", {})
                )

        # Parse addressing modes
        addressing_modes = []
        for mode_data in data.get("addressing_modes", []):
            mode = AddressingMode(
                name=mode_data["name"],
                syntax=mode_data["syntax"],
                description=mode_data["description"],
                pattern=mode_data.get("pattern"),
                operand_types=mode_data.get("operand_types", [])
            )
            addressing_modes.append(mode)

        # Parse assembly syntax
        syntax_data = data.get("assembly_syntax", {})
        assembly_syntax = AssemblySyntax(
            comment_char=syntax_data.get("comment_char", ";"),
            comment_chars=syntax_data.get("comment_chars", []),
            label_suffix=syntax_data.get("label_suffix", ":"),
            register_prefix=syntax_data.get("register_prefix", "$"),
            immediate_prefix=syntax_data.get("immediate_prefix", "#"),
            hex_prefix=syntax_data.get("hex_prefix", "0x"),
            binary_prefix=syntax_data.get("binary_prefix", "0b"),
            case_sensitive=syntax_data.get("case_sensitive", False),
            directives=syntax_data.get("directives", []),
            operand_separators=syntax_data.get("operand_separators", lambda: [",", " "]),
            whitespace_handling=syntax_data.get("whitespace_handling", "flexible")
        )
        
        # Parse address space
        address_space_data = data.get("address_space", {})
        address_space = AddressSpace(
            default_code_start=address_space_data.get("default_code_start", 0),
            default_data_start=address_space_data.get("default_data_start", 0),
            default_stack_start=address_space_data.get("default_stack_start", 0),
            memory_layout=address_space_data.get("memory_layout", {}),
            alignment_requirements=address_space_data.get("alignment_requirements", {})
        )
        
        # Parse PC behavior configuration
        pc_behavior = data.get("pc_behavior", {})
        
        # Parse new modularity fields
        instruction_architecture = data.get("instruction_architecture", {})
        register_formatting = data.get("register_formatting", {})
        operand_formatting = data.get("operand_formatting", {})
        instruction_categories = data.get("instruction_categories", {})
        pseudo_instruction_fallbacks = data.get("pseudo_instruction_fallbacks", {})
        data_detection = data.get("data_detection", {})
        symbol_resolution = data.get("symbol_resolution", {})
        error_messages = data.get("error_messages", {})
        
        # Parse constants
        constants = {}
        for const_name, const_value in data.get("constants", {}).items():
            if isinstance(const_value, dict):
                # Handle constant with description
                constant = Constant(
                    name=const_name,
                    value=const_value.get("value", const_value),
                    description=const_value.get("description")
                )
            else:
                # Handle simple constant value
                constant = Constant(
                    name=const_name,
                    value=const_value
                )
            constants[const_name] = constant
        
        # Parse ecall services
        ecall_services = {}
        for service_id, service_data in data.get("ecall_services", {}).items():
            ecall_service = ECallService(
                name=service_data["name"],
                description=service_data["description"],
                parameters=service_data.get("parameters", {}),
                return_value=service_data.get("return", "None")
            )
            ecall_services[service_id] = ecall_service
        
        return ISADefinition(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            word_size=data["word_size"],
            endianness=data["endianness"],
            instruction_size=data.get("instruction_size", data["word_size"]),
            registers=registers,
            instructions=instructions,
            instruction_formats={},
            operand_patterns={},
            pseudo_instructions=pseudo_instructions,
            directives=directives,
            addressing_modes=addressing_modes,
            assembly_syntax=assembly_syntax,
            address_space=address_space,
            pc_behavior=pc_behavior,
            instruction_architecture=instruction_architecture,
            register_formatting=register_formatting,
            operand_formatting=operand_formatting,
            instruction_categories=instruction_categories,
            pseudo_instruction_fallbacks=pseudo_instruction_fallbacks,
            data_detection=data_detection,
            symbol_resolution=symbol_resolution,
            error_messages=error_messages,
            constants=constants,
            ecall_services=ecall_services,
            validation_rules={},
            variable_length_instructions=data.get('variable_length_instructions', False),
            instruction_length_config=data.get('instruction_length_config', {})
        )
    
    def list_available_isas(self) -> List[str]:
        """List all available ISA definitions"""
        isas = set()
        # Try importlib.resources first
        try:
            for file_path in importlib.resources.files("isa_xform.isa_definitions").iterdir():
                path_obj = file_path if isinstance(file_path, Path) else Path(str(file_path))
                if path_obj.suffix == ".json":
                    isas.add(path_obj.stem)
        except Exception:
            pass
        # Fallback to filesystem (dev mode)
        if self._builtin_path.exists():
            for file_path in self._builtin_path.glob("*.json"):
                isas.add(file_path.stem)
        return sorted(isas)
    
    def clear_cache(self):
        """Clear the ISA cache"""
        self._cache.clear() 