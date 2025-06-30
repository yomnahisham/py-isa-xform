"""
Core module for ISA transformation
"""

from .isa_loader import (
    ISALoader, ISADefinition, Instruction, Register, Directive, 
    PseudoInstruction, AddressingMode, AssemblySyntax, AddressSpace,
    OperandPattern, InstructionFormat
)
from .assembler import Assembler, AssemblyContext, AssembledCode
from .disassembler import Disassembler, DisassembledInstruction, DisassemblyResult
from .parser import Parser, ASTNode, LabelNode, InstructionNode, DirectiveNode, CommentNode, OperandNode
from .symbol_table import SymbolTable, Symbol, SymbolType, SymbolScope
from .operand_parser import OperandParser, ParsedOperand
from .directive_handler import DirectiveHandler, DirectiveContext, DirectiveResult

__all__ = [
    # ISA Loading
    'ISALoader', 'ISADefinition', 'Instruction', 'Register', 'Directive',
    'PseudoInstruction', 'AddressingMode', 'AssemblySyntax', 'AddressSpace',
    'OperandPattern', 'InstructionFormat',
    
    # Assembly
    'Assembler', 'AssemblyContext', 'AssembledCode',
    
    # Disassembly
    'Disassembler', 'DisassembledInstruction', 'DisassemblyResult',
    
    # Parsing
    'Parser', 'ASTNode', 'LabelNode', 'InstructionNode', 'DirectiveNode', 'CommentNode', 'OperandNode',
    
    # Symbol Management
    'SymbolTable', 'Symbol', 'SymbolType', 'SymbolScope',
    
    # Modular Components
    'OperandParser', 'ParsedOperand',
    'DirectiveHandler', 'DirectiveContext', 'DirectiveResult',

    # Simulator
    'Simulator', 'SimulationResult', 'SimulationContext',
] 