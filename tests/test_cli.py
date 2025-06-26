"""
Tests for CLI
"""

import pytest
import tempfile
import json
from pathlib import Path
from click.testing import CliRunner

from isa_xform.cli import main


class TestCLI:
    """Test cases for CLI"""
    
    def setup_method(self):
        """Setup for each test"""
        self.runner = CliRunner()
        
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
                    "flags_affected": ["Z", "N", "C", "V"]
                }
            ]
        }
        
        # Create a simple test assembly file
        self.test_assembly = """
        ; Test assembly program
        .org 0x1000
        
        start:  NOP
                ADD R1, R2, R3
                JMP start
        """
    
    def test_help(self):
        """Test help command"""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "py-isa-xform" in result.output
        assert "assemble" in result.output
        assert "disassemble" in result.output
        assert "validate" in result.output
    
    def test_version(self):
        """Test version command"""
        result = self.runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
    
    def test_assemble_with_isa_file(self):
        """Test assemble command with ISA file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create ISA file
            isa_file = Path(temp_dir) / "test_isa.json"
            with open(isa_file, 'w') as f:
                json.dump(self.test_isa, f)
            
            # Create assembly file
            assembly_file = Path(temp_dir) / "test.s"
            with open(assembly_file, 'w') as f:
                f.write(self.test_assembly)
            
            # Run assemble command
            result = self.runner.invoke(main, [
                'assemble',
                '--isa', str(isa_file),
                '--input', str(assembly_file),
                '--verbose'
            ])
            
            assert result.exit_code == 0
            assert "Loaded ISA: TestISA" in result.output
            assert "Assembly complete" in result.output
            
            # Check that output file was created
            output_file = assembly_file.with_suffix('.bin')
            assert output_file.exists()
    
    def test_assemble_with_builtin_isa(self):
        """Test assemble command with built-in ISA"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create assembly file
            assembly_file = Path(temp_dir) / "test.s"
            with open(assembly_file, 'w') as f:
                f.write(self.test_assembly)
            
            # Try to assemble with non-existent built-in ISA
            result = self.runner.invoke(main, [
                'assemble',
                '--isa', 'nonexistent',
                '--input', str(assembly_file)
            ])
            
            # Should fail because ISA doesn't exist
            assert result.exit_code != 0
            assert "not found" in result.output
    
    def test_assemble_missing_input(self):
        """Test assemble command with missing input file"""
        result = self.runner.invoke(main, [
            'assemble',
            '--isa', 'test_isa.json'
        ])
        
        assert result.exit_code != 0
        assert "Missing option" in result.output
    
    def test_assemble_missing_isa(self):
        """Test assemble command with missing ISA"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create assembly file
            assembly_file = Path(temp_dir) / "test.s"
            with open(assembly_file, 'w') as f:
                f.write(self.test_assembly)
            
            result = self.runner.invoke(main, [
                'assemble',
                '--input', str(assembly_file)
            ])
            
            assert result.exit_code != 0
            assert "Missing option" in result.output
    
    def test_disassemble(self):
        """Test disassemble command"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create ISA file
            isa_file = Path(temp_dir) / "test_isa.json"
            with open(isa_file, 'w') as f:
                json.dump(self.test_isa, f)
            
            # Create a simple binary file
            binary_file = Path(temp_dir) / "test.bin"
            with open(binary_file, 'wb') as f:
                f.write(b'ISA\x00')  # Magic number
                f.write(b'\x07')     # ISA name length
                f.write(b'TestISA')  # ISA name
                f.write(b'\x00\x00\x00\x00')  # Code size (0)
            
            # Run disassemble command
            result = self.runner.invoke(main, [
                'disassemble',
                '--isa', str(isa_file),
                '--input', str(binary_file),
                '--verbose'
            ])
            
            assert result.exit_code == 0
            assert "Loaded ISA: TestISA" in result.output
            assert "Disassembly complete" in result.output
            
            # Check that output file was created
            output_file = binary_file.with_suffix('.s')
            assert output_file.exists()
    
    def test_validate_isa_file(self):
        """Test validate command with ISA file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create ISA file
            isa_file = Path(temp_dir) / "test_isa.json"
            with open(isa_file, 'w') as f:
                json.dump(self.test_isa, f)
            
            # Run validate command
            result = self.runner.invoke(main, [
                'validate',
                '--isa-file', str(isa_file),
                '--verbose'
            ])
            
            assert result.exit_code == 0
            assert "Validating file:" in result.output
            assert "ISA loaded successfully" in result.output
            assert "Validation passed" in result.output
    
    def test_validate_invalid_isa(self):
        """Test validate command with invalid ISA"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create invalid ISA file
            invalid_isa = {"name": "InvalidISA"}  # Missing required fields
            isa_file = Path(temp_dir) / "invalid_isa.json"
            with open(isa_file, 'w') as f:
                json.dump(invalid_isa, f)
            
            # Run validate command
            result = self.runner.invoke(main, [
                'validate',
                '--isa-file', str(isa_file)
            ])
            
            assert result.exit_code != 0
            assert "Missing required fields" in result.output
    
    def test_validate_missing_arguments(self):
        """Test validate command with missing arguments"""
        result = self.runner.invoke(main, ['validate'])
        
        assert result.exit_code != 0
        assert "Must specify either" in result.output
    
    def test_list_isas(self):
        """Test list-isas command"""
        result = self.runner.invoke(main, ['list-isas'])
        
        assert result.exit_code == 0
        assert "Available ISA definitions:" in result.output
    
    def test_list_isas_verbose(self):
        """Test list-isas command with verbose output"""
        result = self.runner.invoke(main, ['list-isas', '--verbose'])
        
        assert result.exit_code == 0
        assert "Available ISA definitions:" in result.output
    
    def test_parse(self):
        """Test parse command"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create ISA file
            isa_file = Path(temp_dir) / "test_isa.json"
            with open(isa_file, 'w') as f:
                json.dump(self.test_isa, f)
            
            # Create assembly file
            assembly_file = Path(temp_dir) / "test.s"
            with open(assembly_file, 'w') as f:
                f.write(self.test_assembly)
            
            # Run parse command
            result = self.runner.invoke(main, [
                'parse',
                '--isa', str(isa_file),
                '--input', str(assembly_file),
                '--verbose'
            ])
            
            assert result.exit_code == 0
            assert "Loaded ISA: TestISA" in result.output
            assert "Parsed" in result.output
            assert "LABEL: start" in result.output
            assert "INSTR: NOP" in result.output
            assert "INSTR: ADD" in result.output
            assert "INSTR: JMP" in result.output
    
    def test_parse_without_isa(self):
        """Test parse command without ISA definition"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create assembly file
            assembly_file = Path(temp_dir) / "test.s"
            with open(assembly_file, 'w') as f:
                f.write(self.test_assembly)
            
            # Run parse command with non-existent ISA
            result = self.runner.invoke(main, [
                'parse',
                '--isa', 'nonexistent',
                '--input', str(assembly_file)
            ])
            
            assert result.exit_code != 0
            assert "not found" in result.output
    
    def test_assemble_with_symbols(self):
        """Test assemble command with symbol listing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create ISA file
            isa_file = Path(temp_dir) / "test_isa.json"
            with open(isa_file, 'w') as f:
                json.dump(self.test_isa, f)
            
            # Create assembly file with labels
            assembly_file = Path(temp_dir) / "test.s"
            with open(assembly_file, 'w') as f:
                f.write("""
                start:  NOP
                        ADD R1, R2, R3
                        JMP start
                """)
            
            # Run assemble command with symbol listing
            result = self.runner.invoke(main, [
                'assemble',
                '--isa', str(isa_file),
                '--input', str(assembly_file),
                '--list-symbols'
            ])
            
            assert result.exit_code == 0
            assert "Symbols:" in result.output
            assert "start:" in result.output
    
    def test_assemble_with_custom_output(self):
        """Test assemble command with custom output file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create ISA file
            isa_file = Path(temp_dir) / "test_isa.json"
            with open(isa_file, 'w') as f:
                json.dump(self.test_isa, f)
            
            # Create assembly file
            assembly_file = Path(temp_dir) / "test.s"
            with open(assembly_file, 'w') as f:
                f.write(self.test_assembly)
            
            # Custom output file
            output_file = Path(temp_dir) / "custom_output.bin"
            
            # Run assemble command
            result = self.runner.invoke(main, [
                'assemble',
                '--isa', str(isa_file),
                '--input', str(assembly_file),
                '--output', str(output_file)
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()
            assert "Assembly complete" in result.output
            assert str(output_file) in result.output
    
    def test_disassemble_with_custom_output(self):
        """Test disassemble command with custom output file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create ISA file
            isa_file = Path(temp_dir) / "test_isa.json"
            with open(isa_file, 'w') as f:
                json.dump(self.test_isa, f)
            
            # Create a simple binary file
            binary_file = Path(temp_dir) / "test.bin"
            with open(binary_file, 'wb') as f:
                f.write(b'ISA\x00')
                f.write(b'\x07')
                f.write(b'TestISA')
                f.write(b'\x00\x00\x00\x00')
            
            # Custom output file
            output_file = Path(temp_dir) / "custom_output.s"
            
            # Run disassemble command
            result = self.runner.invoke(main, [
                'disassemble',
                '--isa', str(isa_file),
                '--input', str(binary_file),
                '--output', str(output_file)
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()
            assert "Disassembly complete" in result.output
            assert str(output_file) in result.output 