"""
ISA Loader: Loads and validates instruction set architecture definitions
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from jsonschema import validate, ValidationError

from ..utils.error_handling import ISALoadError, ISAValidationError


@dataclass
class Register:
    """Represents a register definition"""
    name: str
    size: int
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
    implementation: str  # Required Python code for instruction behavior
    flags_affected: List[str] = field(default_factory=list)


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
    implementation: str  # Required Python code for directive behavior
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


@dataclass
class AddressingMode:
    """Represents an addressing mode definition"""
    name: str
    syntax: str
    description: str
    pattern: Optional[str] = None
    operand_types: List[str] = field(default_factory=list)


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
    validation_rules: Dict[str, Any] = field(default_factory=dict)


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
        if not isa_file:
            raise ISALoadError(f"ISA '{isa_name}' not found")
        
        isa_def = self._load_from_file(isa_file)
        self._cache[isa_name] = isa_def
        return isa_def
    
    def load_isa_from_file(self, file_path: Union[str, Path]) -> ISADefinition:
        """Load an ISA definition from a specific file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise ISALoadError(f"ISA file not found: {file_path}")
        
        return self._load_from_file(file_path)
    
    def _find_isa_file(self, isa_name: str) -> Optional[Path]:
        """Find an ISA file by name"""
        builtin_file = self._builtin_path / f"{isa_name}.json"
        if builtin_file.exists():
            return builtin_file
        
        current_file = Path(f"{isa_name}.json")
        if current_file.exists():
            return current_file
        
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
                    alias=reg_data.get("alias", []),
                    description=reg_data.get("description")
                )
                registers[category].append(register)
        
        # Parse instructions
        instructions = []
        for instr_data in data.get("instructions", []):
            # Validate that implementation is present
            if "implementation" not in instr_data:
                raise ISALoadError(f"Instruction '{instr_data['mnemonic']}' missing required 'implementation' field")
            
            instruction = Instruction(
                mnemonic=instr_data["mnemonic"],
                opcode=instr_data.get("opcode", ""),
                format=instr_data["format"],
                description=instr_data["description"],
                encoding=instr_data["encoding"],
                syntax=instr_data["syntax"],
                semantics=instr_data["semantics"],
                implementation=instr_data["implementation"],
                flags_affected=instr_data.get("flags_affected", [])
            )
            instructions.append(instruction)

        # Parse pseudo-instructions
        pseudo_instructions = []
        for pseudo_data in data.get("pseudo_instructions", []):
            pseudo_instruction = PseudoInstruction(
                mnemonic=pseudo_data["mnemonic"],
                description=pseudo_data["description"],
                syntax=pseudo_data["syntax"],
                expansion=pseudo_data["expansion"]
            )
            pseudo_instructions.append(pseudo_instruction)

        # Parse directives
        directives = {}
        for directive_data in data.get("directives", []):
            if isinstance(directive_data, dict):
                # Validate that implementation is present
                if "implementation" not in directive_data:
                    raise ISALoadError(f"Directive '{directive_data['name']}' missing required 'implementation' field")
                
                directive = Directive(
                    name=directive_data["name"],
                    description=directive_data["description"],
                    action=directive_data["action"],
                    implementation=directive_data["implementation"],
                    argument_types=directive_data.get("argument_types", []),
                    handler=directive_data.get("handler"),
                    syntax=directive_data.get("syntax", ""),
                    examples=directive_data.get("examples", []),
                    validation_rules=directive_data.get("validation_rules", {})
                )
                directives[directive.name] = directive

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
            validation_rules={}
        )
    
    def list_available_isas(self) -> List[str]:
        """List all available ISA definitions"""
        isas = []
        if self._builtin_path.exists():
            for file_path in self._builtin_path.glob("*.json"):
                isas.append(file_path.stem)
        return sorted(isas)
    
    def clear_cache(self):
        """Clear the ISA cache"""
        self._cache.clear() 