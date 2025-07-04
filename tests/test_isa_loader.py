"""
Tests for ISA Loader
"""

import pytest
import tempfile
import json
from pathlib import Path
import shutil

from isa_xform.core.isa_loader import ISALoader, ISADefinition, Register, Instruction
from isa_xform.utils.error_handling import ISALoadError


class TestISALoader:
    """Test cases for ISALoader"""
    
    def setup_method(self):
        """Setup for each test"""
        self.loader = ISALoader()
        
        # Create a simple test ISA
        self.test_isa = {
            "name": "TestISA",
            "version": "1.0",
            "description": "Test ISA for unit testing",
            "word_size": 16,
            "endianness": "little",
            "instruction_size": 16,
            "registers": {
                "general_purpose": [
                    {"name": "R0", "size": 16, "alias": ["ZERO"]},
                    {"name": "R1", "size": 16, "alias": ["AT"]}
                ],
                "special_purpose": [
                    {"name": "PC", "size": 16, "description": "Program Counter"}
                ]
            },
            "instructions": [
                {
                    "mnemonic": "NOP",
                    "opcode": "0000",
                    "format": "R-type",
                    "description": "No operation",
                    "encoding": {
                        "fields": [
                            {"name": "opcode", "bits": "15:12", "value": "0000"},
                            {"name": "unused", "bits": "11:0", "value": "000000000000"}
                        ]
                    },
                    "syntax": "NOP",
                    "semantics": "No operation",
                    "implementation": "# NOP implementation\n# No operation performed",
                    "flags_affected": []
                },
                {
                    "mnemonic": "ADD",
                    "opcode": "0001",
                    "format": "R-type",
                    "description": "Add two registers",
                    "encoding": {
                        "fields": [
                            {"name": "opcode", "bits": "15:12", "value": "0001"},
                            {"name": "rd", "bits": "11:8", "type": "register"},
                            {"name": "rs1", "bits": "7:4", "type": "register"},
                            {"name": "rs2", "bits": "3:0", "type": "register"}
                        ]
                    },
                    "syntax": "ADD $rd, $rs1, $rs2",
                    "semantics": "$rd = $rs1 + $rs2",
                    "implementation": "# ADD implementation\nrd_val = read_register(operands['rd'])\nrs1_val = read_register(operands['rs1'])\nrs2_val = read_register(operands['rs2'])\nresult = (rs1_val + rs2_val) & 0xFFFF\nwrite_register(operands['rd'], result)",
                    "flags_affected": ["Z", "N", "C", "V"]
                }
            ]
        }
    
    def test_load_isa_from_file(self):
        """Test loading ISA from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_isa, f)
            temp_file = f.name
        
        try:
            isa_def = self.loader.load_isa_from_file(temp_file)
            
            assert isinstance(isa_def, ISADefinition)
            assert isa_def.name == "TestISA"
            assert isa_def.version == "1.0"
            assert isa_def.word_size == 16
            assert isa_def.endianness == "little"
            assert isa_def.instruction_size == 16
            assert len(isa_def.instructions) == 2
            assert len(isa_def.registers["general_purpose"]) == 2
            assert len(isa_def.registers["special_purpose"]) == 1
        finally:
            Path(temp_file).unlink()
    
    def test_load_isa_from_file_not_found(self):
        """Test loading ISA from non-existent file"""
        with pytest.raises(ISALoadError, match="ISA file not found"):
            self.loader.load_isa_from_file("nonexistent.json")
    
    def test_load_isa_from_file_invalid_json(self):
        """Test loading ISA from file with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            with pytest.raises(ISALoadError, match="Invalid JSON"):
                self.loader.load_isa_from_file(temp_file)
        finally:
            Path(temp_file).unlink()
    
    def test_load_isa_missing_required_fields(self):
        """Test loading ISA with missing required fields"""
        invalid_isa = {
            "name": "TestISA",
            # Missing version, word_size, endianness, registers, instructions
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_isa, f)
            temp_file = f.name
        
        try:
            with pytest.raises(ISALoadError):
                self.loader.load_isa_from_file(temp_file)
        finally:
            Path(temp_file).unlink()
    
    def test_parse_isa_data(self):
        """Test parsing ISA data"""
        isa_def = self.loader._parse_isa_data(self.test_isa, Path("test.json"))
        
        assert isinstance(isa_def, ISADefinition)
        assert isa_def.name == "TestISA"
        assert isa_def.version == "1.0"
        assert isa_def.description == "Test ISA for unit testing"
        assert isa_def.word_size == 16
        assert isa_def.endianness == "little"
        assert isa_def.instruction_size == 16
        
        # Check registers
        assert "general_purpose" in isa_def.registers
        assert "special_purpose" in isa_def.registers
        
        gp_regs = isa_def.registers["general_purpose"]
        assert len(gp_regs) == 2
        assert gp_regs[0].name == "R0"
        assert gp_regs[0].size == 16
        assert gp_regs[0].alias == ["ZERO"]
        assert gp_regs[1].name == "R1"
        assert gp_regs[1].alias == ["AT"]
        
        sp_regs = isa_def.registers["special_purpose"]
        assert len(sp_regs) == 1
        assert sp_regs[0].name == "PC"
        assert sp_regs[0].description == "Program Counter"
        
        # Check instructions
        assert len(isa_def.instructions) == 2
        
        nop_instr = isa_def.instructions[0]
        assert nop_instr.mnemonic == "NOP"
        assert nop_instr.opcode == "0000"
        assert nop_instr.format == "R-type"
        assert nop_instr.description == "No operation"
        assert nop_instr.syntax == "NOP"
        assert nop_instr.semantics == "No operation"
        assert nop_instr.flags_affected == []
        
        add_instr = isa_def.instructions[1]
        assert add_instr.mnemonic == "ADD"
        assert add_instr.opcode == "0001"
        assert add_instr.format == "R-type"
        assert add_instr.description == "Add two registers"
        assert add_instr.syntax == "ADD $rd, $rs1, $rs2"
        assert add_instr.semantics == "$rd = $rs1 + $rs2"
        assert add_instr.flags_affected == ["Z", "N", "C", "V"]
    
    def test_cache_functionality(self):
        """Test ISA caching"""
        # Create test file in current directory
        cache_test_file = Path("cache_test.json")
        with open(cache_test_file, 'w') as f:
            json.dump(self.test_isa, f)
        
        try:
            # First load by name (this uses cache)
            isa_def1 = self.loader.load_isa("cache_test")
            
            # Second load by name should use cache
            isa_def2 = self.loader.load_isa("cache_test")
            
            # Should be the same object (cached)
            assert isa_def1 is isa_def2
            
            # Clear cache and load again
            self.loader.clear_cache()
            isa_def3 = self.loader.load_isa("cache_test")
            
            # Should be different object after cache clear
            assert isa_def1 is not isa_def3
            
        finally:
            # Clean up
            if cache_test_file.exists():
                cache_test_file.unlink()
    
    def test_list_available_isas(self):
        """Test listing available ISAs"""
        isas = self.loader.list_available_isas()
        
        # Should return a list
        assert isinstance(isas, list)
        
        # Should be sorted
        assert isas == sorted(isas)
    
    def test_find_isa_file(self):
        """Test finding ISA files"""
        # Test with non-existent ISA
        result = self.loader._find_isa_file("nonexistent")
        assert result is None
        
        # Test with built-in ISA (if any exist)
        # This test depends on the actual built-in ISAs
        pass

    def test_load_isa_basic(self):
        """Test basic ISA loading"""
        isa_def = self.loader.load_isa("zx16")
        
        assert isa_def.name == "ZX16"
        assert isa_def.version == "1.0"
        assert isa_def.word_size == 16
        assert isa_def.endianness == "little"
        assert len(isa_def.instructions) > 0
        assert len(isa_def.registers) > 0

    def test_load_isa_with_constants_and_ecall_services(self):
        """Test that constants and ecall services are properly loaded"""
        isa_def = self.loader.load_isa("zx16")
        
        # Test constants
        assert "constants" in isa_def.__dict__
        assert isinstance(isa_def.constants, dict)
        assert len(isa_def.constants) > 0
        
        # Check some expected constants
        expected_constants = ["RESET_VECTOR", "CODE_START", "MMIO_BASE", "STACK_TOP", "MEM_SIZE"]
        for const_name in expected_constants:
            assert const_name in isa_def.constants
            assert hasattr(isa_def.constants[const_name], 'value')
            assert hasattr(isa_def.constants[const_name], 'name')
        
        # Test ecall services
        assert "ecall_services" in isa_def.__dict__
        assert isinstance(isa_def.ecall_services, dict)
        assert len(isa_def.ecall_services) > 0
        
        # Check some expected ecall services
        expected_services = ["0x000", "0x00A"]  # print_char and exit
        for service_id in expected_services:
            assert service_id in isa_def.ecall_services
            service = isa_def.ecall_services[service_id]
            assert hasattr(service, 'name')
            assert hasattr(service, 'description')
            assert hasattr(service, 'parameters')
            assert hasattr(service, 'return_value')
        
        # Verify specific service details
        print_char_service = isa_def.ecall_services["0x000"]
        assert print_char_service.name == "print_char"
        assert "a0" in print_char_service.parameters
        
        exit_service = isa_def.ecall_services["0x00A"]
        assert exit_service.name == "exit"
        assert "a0" in exit_service.parameters

    def test_isa_without_constants_or_ecall_services(self):
        """Test loading ISA that doesn't have constants or ecall services"""
        # This test would need an ISA without these fields
        # For now, we'll just verify the fields exist as empty dicts
        try:
            isa_def = self.loader.load_isa("riscv_rv32i")
            # Should have empty dicts for missing fields
            assert isinstance(isa_def.constants, dict)
            assert isinstance(isa_def.ecall_services, dict)
        except ISALoadError:
            # If RISC-V ISA doesn't exist, that's fine for this test
            pass


class TestISADefinition:
    """Test cases for ISADefinition"""
    
    def test_isa_definition_creation(self):
        """Test creating ISADefinition"""
        registers = {
            "general_purpose": [
                Register("R0", 16, ["ZERO"]),
                Register("R1", 16, ["AT"])
            ]
        }
        
        instructions = [
            Instruction("NOP", "0000", "R-type", "No operation", {}, "NOP", "No operation", "# NOP implementation")
        ]
        
        isa_def = ISADefinition(
            name="TestISA",
            version="1.0",
            description="Test ISA",
            word_size=16,
            endianness="little",
            instruction_size=16,
            registers=registers,
            instructions=instructions
        )
        
        assert isa_def.name == "TestISA"
        assert isa_def.version == "1.0"
        assert isa_def.description == "Test ISA"
        assert isa_def.word_size == 16
        assert isa_def.endianness == "little"
        assert isa_def.instruction_size == 16
        assert len(isa_def.registers["general_purpose"]) == 2
        assert len(isa_def.instructions) == 1


class TestRegister:
    """Test cases for Register"""
    
    def test_register_creation(self):
        """Test creating Register"""
        reg = Register("R0", 16, ["ZERO"], "Always zero")
        
        assert reg.name == "R0"
        assert reg.size == 16
        assert reg.alias == ["ZERO"]
        assert reg.description == "Always zero"
    
    def test_register_defaults(self):
        """Test Register with default values"""
        reg = Register("R1", 16)
        
        assert reg.name == "R1"
        assert reg.size == 16
        assert reg.alias == []
        assert reg.description is None


class TestInstruction:
    """Test cases for Instruction"""
    
    def test_instruction_creation(self):
        """Test creating Instruction"""
        instr = Instruction(
            mnemonic="ADD",
            opcode="0001",
            format="R-type",
            description="Add two registers",
            encoding={"fields": []},
            syntax="ADD $rd, $rs1, $rs2",
            semantics="$rd = $rs1 + $rs2",
            implementation="# ADD implementation",
            flags_affected=["Z", "N", "C", "V"]
        )
        
        assert instr.mnemonic == "ADD"
        assert instr.opcode == "0001"
        assert instr.format == "R-type"
        assert instr.description == "Add two registers"
        assert instr.encoding == {"fields": []}
        assert instr.syntax == "ADD $rd, $rs1, $rs2"
        assert instr.semantics == "$rd = $rs1 + $rs2"
        assert instr.flags_affected == ["Z", "N", "C", "V"]
    
    def test_instruction_defaults(self):
        """Test Instruction with default values"""
        instr = Instruction(
            mnemonic="NOP",
            opcode="0000",
            format="R-type",
            description="No operation",
            encoding={},
            syntax="NOP",
            semantics="No operation",
            implementation="# NOP implementation"
        )
        
        assert instr.mnemonic == "NOP"
        assert instr.flags_affected == [] 