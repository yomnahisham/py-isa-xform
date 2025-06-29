#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.parser import Parser, DirectiveNode, InstructionNode

# Load ISA
loader = ISALoader()
isa = loader.load_isa('simple_risc')

# Create parser
parser = Parser(isa)

# Test different lines
test_lines = [
    ".org 0x1000",
    ".word 0x1234", 
    "LDI R1, #10",
    "data: .word 0x1234"
]

print("Testing parser node types:")
for line in test_lines:
    result = parser._parse_line(line, 1, "test.s")
    if result:
        if isinstance(result, list):
            for node in result:
                print(f"'{line}' -> {type(node).__name__}: {node}")
        else:
            print(f"'{line}' -> {type(result).__name__}: {result}")
    else:
        print(f"'{line}' -> None") 