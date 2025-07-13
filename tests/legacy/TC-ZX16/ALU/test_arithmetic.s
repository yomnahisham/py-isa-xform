# ZX16 Arithmetic Test Case
# Tests basic arithmetic operations: ADD, SUB, ADDI, LI, AND, OR, XOR, SLT, SLTU, SLL, SRL, SRA, MV

    .text
    .globl main

main:
    # Load immediate values
    LI a0, 10          # a0 = 10
    LI a1, 5           # a1 = 5
    LI t1, 3           # t1 = 3
    LI s0, 2           # s0 = 2
    
    # Test addition
    ADD a0, a1         # a0 = a0 + a1 (10 + 5 = 15)
    
    # Test subtraction
    SUB a0, a1         # a0 = a0 - a1 (15 - 5 = 10)
    
    # Test immediate addition
    ADDI a0, 20        # a0 = a0 + 20 (10 + 20 = 30)
    
    # Test immediate subtraction
    ADDI a0, -5        # a0 = a0 + (-5) (30 - 5 = 25)
    
    # Test AND
    AND a0, t1         # a0 = a0 & t1 (25 & 3 = 1)
    
    # Test OR
    OR a0, s0          # a0 = a0 | s0 (1 | 2 = 3)
    
    # Test XOR
    XOR a0, a1         # a0 = a0 ^ a1 (3 ^ 5 = 6)
    
    # Test SLT (set if less than)
    SLT a0, t1         # a0 = (a0 < t1) ? 1 : 0 (6 < 3 = 0)
    
    # Test SLTU (set if less than, unsigned)
    SLTU a0, s0        # a0 = (a0 < s0 unsigned) ? 1 : 0 (0 < 2 = 1)
    
    # Test SLL (shift left logical)
    SLL a0, t1         # a0 = a0 << (t1 & 0xF) (1 << 3 = 8)
    
    # Test SRL (shift right logical)
    SRL a0, s0         # a0 = a0 >> (s0 & 0xF) (8 >> 2 = 2)
    
    # Test SRA (shift right arithmetic)
    SRA a0, t1         # a0 = a0 >> (t1 & 0xF) (2 >> 3 = 0)
    
    # Test MV (move register)
    MV a1, a0          # a1 = a0 (a1 = 0)
    
    # Exit with result in a0
    ECALL 0x3FF        # Exit with code 0 