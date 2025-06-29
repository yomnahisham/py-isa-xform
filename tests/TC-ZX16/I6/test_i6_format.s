# ZX16 I6-type Instruction Format Test
# Tests 6-bit immediate format instructions

.org 0x0020

start:
    # I6-type immediate ALU operations (opcode 011)
    ADDI x1, x2, 15         # Add immediate: x1 = x2 + 15
    ANDI x2, x1, 31         # AND immediate: x2 = x1 & 31
    ORI  x3, x2, 8          # OR immediate: x3 = x2 | 8
    XORI x4, x3, 7          # XOR immediate: x4 = x3 ^ 7
    
    # Shift immediate operations
    SLLI x5, x1, 3          # Shift left logical immediate: x5 = x1 << 3
    SRLI x6, x2, 2          # Shift right logical immediate: x6 = x2 >> 2
    SRAI x7, x3, 1          # Shift right arithmetic immediate: x7 = x3 >>> 1
    
    # Load/Store operations
    LB   x1, 4(x2)          # Load byte: x1 = sign_extend(Memory[x2 + 4][7:0])
    LW   x3, 8(x4)          # Load word: x3 = Memory[x4 + 8]
    SB   x5, 2(x6)          # Store byte: Memory[x6 + 2][7:0] = x5[7:0]
    SW   x7, 6(x1)          # Store word: Memory[x1 + 6] = x7
    
    # Jump and link register
    JALR ra, 0(x1)          # Jump and link register: ra = PC + 2; PC = x1 + 0
    
    # Test with negative offsets/immediates
    ADDI x2, x3, -8         # Test negative immediate
    LB   x4, -2(sp)         # Test negative offset
    SW   x5, -4(x6)         # Test negative store offset
    
    # Test boundary values (6-bit immediate: -32 to +31)
    ADDI x1, x2, 31         # Maximum positive
    ADDI x3, x4, -32        # Maximum negative
    
end:
    NOP 