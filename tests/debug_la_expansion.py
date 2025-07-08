#!/usr/bin/env python3

from src.isa_xform.core.isa_loader import ISALoader
from src.isa_xform.core.parser import Parser
from src.isa_xform.core.assembler import Assembler

# Load ISA
loader = ISALoader()
isa = loader.load_isa('zx16')

# Find LA pseudo-instruction
la_pseudo = None
for pseudo in isa.pseudo_instructions:
    if pseudo.mnemonic == 'LA':
        la_pseudo = pseudo
        break

print("LA pseudo-instruction:")
print(f"  Mnemonic: {la_pseudo.mnemonic}")
print(f"  Syntax: {la_pseudo.syntax}")
print(f"  Expansion: {la_pseudo.expansion}")

# Parse LA instruction
parser = Parser(isa)
nodes = parser.parse("LA x1, message")

print("\nParsed nodes:")
for node in nodes:
    print(f"  {type(node).__name__}: {node}")

# Create assembler
assembler = Assembler(isa)

# Test pseudo-instruction expansion
if nodes and hasattr(nodes[0], 'mnemonic'):
    print(f"\nTesting expansion of: {nodes[0].mnemonic}")
    
    # Check if it's a real instruction
    real_instruction = assembler._find_instruction(nodes[0].mnemonic)
    print(f"Is real instruction: {real_instruction is not None}")
    
    if not real_instruction:
        print("Attempting pseudo-instruction expansion...")
        try:
            expanded = assembler._expand_pseudo_instruction(nodes[0])
            print(f"Expanded to {len(expanded)} instructions:")
            for i, instr in enumerate(expanded):
                print(f"  {i}: {instr.mnemonic} {[op.value for op in instr.operands]}")
        except Exception as e:
            print(f"Expansion failed: {e}")
    else:
        print("Found as real instruction, no expansion needed")

# Test with symbol table
print("\nTesting with symbol table...")
assembler.symbol_table.define_label("message", 0x8000)
assembler.context.pass_number = 2

print(f"Symbol table has 'message' at address: {assembler.symbol_table.get_symbol('message').value}")

if nodes and hasattr(nodes[0], 'mnemonic'):
    try:
        expanded = assembler._expand_pseudo_instruction(nodes[0])
        print(f"Second pass expansion to {len(expanded)} instructions:")
        for i, instr in enumerate(expanded):
            print(f"  {i}: {instr.mnemonic} {[op.value for op in instr.operands]}")
    except Exception as e:
        print(f"Second pass expansion failed: {e}")

# Test bitfield extraction manually
print("\nTesting bitfield extraction manually...")
message_addr = 0x8000
print(f"Message address: 0x{message_addr:X}")
print(f"label[15:9] = {(message_addr >> 9) & 0x7F} (0x{(message_addr >> 9) & 0x7F:X})")
print(f"label[8:0] = {message_addr & 0x1FF} (0x{message_addr & 0x1FF:X})") 