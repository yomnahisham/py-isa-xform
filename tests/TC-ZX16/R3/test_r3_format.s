# ZX16 R3-type Instruction Format Test
# Tests three register format instructions

# R3-type ALU instructions (opcode 010)
ADD x1, x2, x3          # Add: x1 = x2 + x3
SUB x4, x1, x2          # Subtract: x4 = x1 - x2
AND x5, x1, x3          # Bitwise AND: x5 = x1 & x3
OR  x6, x2, x4          # Bitwise OR: x6 = x2 | x4
XOR x7, x1, x5          # Bitwise XOR: x7 = x1 ^ x5

# Shift operations
SLL x1, x2, x3          # Shift left logical: x1 = x2 << (x3 & 0xF)
SRL x2, x3, x4          # Shift right logical: x2 = x3 >> (x4 & 0xF)
SRA x3, x4, x5          # Shift right arithmetic: x3 = x4 >>> (x5 & 0xF)

# Test with different register combinations
ADD x0, x7, x6          # Use x0 (zero register)
SUB x1, x2, x3          # Basic subtract
AND x4, x5, x6          # Basic AND
XOR x7, x0, x1          # XOR with zero register

# Final instruction
NOP 