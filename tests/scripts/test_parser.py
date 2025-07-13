"""
Tests for Parser
"""

import pytest
from isa_xform.core.parser import Parser, TokenType, Token, LabelNode, InstructionNode, OperandNode, DirectiveNode, CommentNode
from isa_xform.core.isa_loader import ISALoader, ISADefinition, Register, Instruction
from isa_xform.utils.error_handling import ParseError


class TestParser:
    """Test cases for Parser"""
    
    def setup_method(self):
        """Setup for each test"""
        # Create a simple test ISA
        registers = {
            "general_purpose": [
                Register("R0", 16, ["ZERO"]),
                Register("R1", 16, ["AT"]),
                Register("R2", 16, ["V0"]),
                Register("R3", 16, ["V1"])
            ]
        }
        
        instructions = [
            Instruction("NOP", "0000", "R-type", "No operation", {}, "NOP", "No operation", "# NOP implementation"),
            Instruction("ADD", "0001", "R-type", "Add two registers", {}, "ADD $rd, $rs2", "$rd = $rd + $rs2", "# ADD implementation"),
            Instruction("LDI", "0101", "I-type", "Load immediate", {}, "LDI $rd, #imm", "$rd = imm", "# LDI implementation"),
            Instruction("JMP", "1000", "J-type", "Jump", {}, "JMP address", "PC = address", "# JMP implementation")
        ]
        
        self.isa_def = ISADefinition(
            name="TestISA",
            version="1.0",
            description="Test ISA",
            word_size=16,
            endianness="little",
            instruction_size=16,
            registers=registers,
            instructions=instructions
        )
        
        self.parser = Parser(self.isa_def)
    
    def test_parse_basic_instruction(self):
        """Test parsing basic instruction"""
        text = "ADD R1, R2"
        nodes = self.parser.parse(text)
        
        assert len(nodes) == 1
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].mnemonic == "ADD"
        assert len(nodes[0].operands) == 2
        assert nodes[0].operands[0].type == "register"
        assert nodes[0].operands[0].value == "R1"
        assert nodes[0].operands[1].type == "register"
        assert nodes[0].operands[1].value == "R2"
    
    def test_parse_instruction_with_comments(self):
        """Test parsing instruction with comments"""
        text = "ADD R1, R2 ; This is a comment"
        nodes = self.parser.parse(text)
        
        assert len(nodes) == 1  # Only instruction, comment is stripped
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].mnemonic == "ADD"
        assert len(nodes[0].operands) == 2
        assert nodes[0].operands[0].type == "register"
        assert nodes[0].operands[0].value == "R1"
        assert nodes[0].operands[1].type == "register"
        assert nodes[0].operands[1].value == "R2"
    
    def test_parse_label_with_instruction(self):
        """Test parsing label with instruction"""
        text = "start: ADD R1, R2"
        nodes = self.parser.parse(text)
        
        assert len(nodes) == 2  # Label and instruction
        assert isinstance(nodes[0], LabelNode)
        assert nodes[0].name == "start"
        assert isinstance(nodes[1], InstructionNode)
        assert nodes[1].mnemonic == "ADD"
        assert len(nodes[1].operands) == 2
        assert nodes[1].operands[0].type == "register"
        assert nodes[1].operands[0].value == "R1"
        assert nodes[1].operands[1].type == "register"
        assert nodes[1].operands[1].value == "R2"
    
    def test_parse_immediate_values(self):
        """Test parsing immediate values"""
        text = "LDI R1, #42"
        nodes = self.parser.parse(text)
        
        assert len(nodes) == 1
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].mnemonic == "LDI"
        assert len(nodes[0].operands) == 2
        assert nodes[0].operands[0].type == "register"
        assert nodes[0].operands[0].value == "R1"
        assert nodes[0].operands[1].type == "immediate"
        assert nodes[0].operands[1].value == "42"
    
    def test_parse_hex_numbers(self):
        """Test parsing hex numbers"""
        text = "LDI R1, #0x1234"
        nodes = self.parser.parse(text)
    
        assert len(nodes) == 1
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].mnemonic == "LDI"
        assert len(nodes[0].operands) == 2
        assert nodes[0].operands[0].type == "register"
        assert nodes[0].operands[0].value == "R1"
        assert nodes[0].operands[1].type == "immediate"
        assert nodes[0].operands[1].value == 4660  # 0x1234 converted to decimal
    
    def test_parse_binary_numbers(self):
        """Test parsing binary numbers"""
        text = "LDI R1, #0b1010"
        nodes = self.parser.parse(text)
        
        assert len(nodes) == 1
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].mnemonic == "LDI"
        assert len(nodes[0].operands) == 2
        assert nodes[0].operands[0].type == "register"
        assert nodes[0].operands[0].value == "R1"
        assert nodes[0].operands[1].type == "immediate"
        assert nodes[0].operands[1].value == 10  # 0b1010 converted to decimal
    
    def test_parse_directives(self):
        """Test parsing directives"""
        text = ".org 0x1000"
        nodes = self.parser.parse(text)
        
        assert len(nodes) == 1
        assert isinstance(nodes[0], DirectiveNode)
        assert nodes[0].name == ".org"
        assert len(nodes[0].arguments) == 1
        assert nodes[0].arguments[0] == "0x1000"
    
    def test_parse_identifier_extraction(self):
        """Test identifier parsing in various contexts"""
        # Test label parsing
        text = "start_label: ADD R1, R2"
        nodes = self.parser.parse(text)
        
        assert len(nodes) == 2
        assert isinstance(nodes[0], LabelNode)
        assert nodes[0].name == "start_label"
        assert isinstance(nodes[1], InstructionNode)
        assert nodes[1].mnemonic == "ADD"
    
    def test_parse_number_extraction(self):
        """Test number parsing in various formats"""
        # Test decimal
        text = "LDI R1, #42"
        nodes = self.parser.parse(text)
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].operands[1].value == "42"
        
        # Test hex
        text = "LDI R1, #0x1234"
        nodes = self.parser.parse(text)
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].operands[1].value == 4660  # 0x1234 converted to decimal
        
        # Test binary
        text = "LDI R1, #0b1010"
        nodes = self.parser.parse(text)
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].operands[1].value == 10  # 0b1010 converted to decimal
    
    def test_parse_identifier_classification(self):
        """Test identifier classification through parsing"""
        # Test instruction classification
        text = "ADD R1, R2"
        nodes = self.parser.parse(text)
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].mnemonic == "ADD"
        
        # Test register classification
        text = "LDI R1, #42"
        nodes = self.parser.parse(text)
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].operands[0].type == "register"
        assert nodes[0].operands[0].value == "R1"
        
        # Test directive classification
        text = ".org 0x1000"
        nodes = self.parser.parse(text)
        assert isinstance(nodes[0], DirectiveNode)
        assert nodes[0].name == ".org"
        
        # Test label classification
        text = "start: NOP"
        nodes = self.parser.parse(text)
        assert isinstance(nodes[0], LabelNode)
        assert nodes[0].name == "start"
    
    def test_parse_complex_program(self):
        """Test parsing a complex program"""
        text = """
        ; Test program
        .org 0x1000
        
        start:  LDI R1, #10
                LDI R2, #20
                ADD R3, R2
                JMP start
        """
        
        nodes = self.parser.parse(text)
        
        # Should have 7 nodes: comment, directive, label, instruction (from same line), and 3 more instructions
        assert len(nodes) == 7
        
        # Check comment
        assert isinstance(nodes[0], CommentNode)
        
        # Check directive
        assert isinstance(nodes[1], DirectiveNode)
        assert nodes[1].name == ".org"
        
        # Check label
        assert isinstance(nodes[2], LabelNode)
        assert nodes[2].name == "start"
        
        # Check instruction from same line as label
        assert isinstance(nodes[3], InstructionNode)
        assert nodes[3].mnemonic == "LDI"
        
        # Check remaining instructions
        assert isinstance(nodes[4], InstructionNode)
        assert nodes[4].mnemonic == "LDI"
        
        assert isinstance(nodes[5], InstructionNode)
        assert nodes[5].mnemonic == "ADD"
        
        assert isinstance(nodes[6], InstructionNode)
        assert nodes[6].mnemonic == "JMP"
    
    def test_parse_error_missing_colon(self):
        """Test parsing error with missing colon after label"""
        text = "start ADD R1, R2"  # Missing colon
        
        # The new parser is more forgiving and treats this as an instruction
        nodes = self.parser.parse(text)
        assert len(nodes) == 1
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].mnemonic == "start"
    
    def test_parse_error_invalid_operand(self):
        """Test parsing error with invalid operand"""
        text = "ADD R1, invalid_operand"
        
        # The new parser treats invalid operands as labels
        nodes = self.parser.parse(text)
        assert len(nodes) == 1
        assert isinstance(nodes[0], InstructionNode)
        assert len(nodes[0].operands) == 2  # Both R1 and invalid_operand are parsed
        assert nodes[0].operands[0].type == "register"
        assert nodes[0].operands[1].type == "label"
    
    def test_parser_without_isa(self):
        """Test parser without ISA definition"""
        parser = Parser()  # No ISA definition
        
        text = "ADD R1, R2"
        nodes = parser.parse(text)
        
        # Without ISA, ADD should still be parsed as an instruction
        assert len(nodes) == 1
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].mnemonic == "ADD"
    
    def test_case_insensitive_parsing(self):
        """Test case insensitive parsing"""
        text = "add r1, r2"
        nodes = self.parser.parse(text)
        
        assert len(nodes) == 1
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].mnemonic == "add"  # Parser preserves case
        assert nodes[0].operands[0].value == "R1"  # Register names are normalized
        assert nodes[0].operands[1].value == "R2"
    
    def test_parse_comment(self):
        """Test parsing comment"""
        text = "; This is a comment"
        nodes = self.parser.parse(text)
        
        assert len(nodes) == 1
        assert isinstance(nodes[0], CommentNode)
        assert nodes[0].text == "; This is a comment"
    
    def test_parse_immediate_operand(self):
        """Test parsing immediate operand"""
        text = "LDI R1, #42"
        nodes = self.parser.parse(text)
        
        assert len(nodes) == 1
        assert isinstance(nodes[0], InstructionNode)
        assert nodes[0].mnemonic == "LDI"
        assert len(nodes[0].operands) == 2
        assert nodes[0].operands[0].type == "register"
        assert nodes[0].operands[0].value == "R1"
        assert nodes[0].operands[1].type == "immediate"
        assert nodes[0].operands[1].value == "42"


class TestToken:
    """Test cases for Token"""
    
    def test_token_creation(self):
        """Test creating Token"""
        token = Token(TokenType.INSTRUCTION, "ADD", 1, 1, "test.s")
        
        assert token.type == TokenType.INSTRUCTION
        assert token.value == "ADD"
        assert token.line == 1
        assert token.column == 1
        assert token.file == "test.s"


class TestASTNodes:
    """Test cases for AST nodes"""
    
    def test_label_node(self):
        """Test LabelNode"""
        node = LabelNode("start", 1, 1, "test.s")
        
        assert node.line == 1
        assert node.column == 1
        assert node.file == "test.s"
        assert node.name == "start"
    
    def test_instruction_node(self):
        """Test InstructionNode"""
        operands = [OperandNode("R1", "register", 1, 5, "test.s")]
        node = InstructionNode("ADD", operands, 1, 1, "test.s")
        
        assert node.line == 1
        assert node.column == 1
        assert node.file == "test.s"
        assert node.mnemonic == "ADD"
        assert len(node.operands) == 1
        assert node.operands[0].type == "register"
        assert node.operands[0].value == "R1"
    
    def test_operand_node(self):
        """Test OperandNode"""
        node = OperandNode("R1", "register", 1, 5, "test.s")
        
        assert node.line == 1
        assert node.column == 5
        assert node.file == "test.s"
        assert node.type == "register"
        assert node.value == "R1"
    
    def test_directive_node(self):
        """Test DirectiveNode"""
        node = DirectiveNode(".org", ["0x1000"], 1, 1, "test.s")
        
        assert node.line == 1
        assert node.column == 1
        assert node.file == "test.s"
        assert node.name == ".org"
        assert node.arguments == ["0x1000"]
    
    def test_comment_node(self):
        """Test CommentNode"""
        node = CommentNode(" This is a comment", 1, 1, "test.s")
        
        assert node.line == 1
        assert node.column == 1
        assert node.file == "test.s"
        assert node.text == " This is a comment" 