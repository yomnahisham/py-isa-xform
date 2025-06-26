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
    flags_affected: List[str] = field(default_factory=list)


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
            instruction = Instruction(
                mnemonic=instr_data["mnemonic"],
                opcode=instr_data["opcode"],
                format=instr_data["format"],
                description=instr_data["description"],
                encoding=instr_data["encoding"],
                syntax=instr_data["syntax"],
                semantics=instr_data["semantics"],
                flags_affected=instr_data.get("flags_affected", [])
            )
            instructions.append(instruction)
        
        return ISADefinition(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            word_size=data["word_size"],
            endianness=data["endianness"],
            instruction_size=data.get("instruction_size", data["word_size"]),
            registers=registers,
            instructions=instructions
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