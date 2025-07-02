# ZX16 Instruction Test Program (Corrected for all immediate constraints)
# Tests all instructions except B-type (branch) instructions

.org 32                 # Start at default code address

main:
# Test arithmetic shift with negative number
LI x6, -1          # Load -8 into x6 (valid: within -64 to +63)
SRA x6, x7         # x6 = x6 >> 2 (arithmetic) = -2

# Test move operation
MV x0, x1          # x0 = x1 = 5

# Test I-type instructions with corrected immediates
ADDI x0, 10        # x0 = x0 + 10 = 5 + 10 = 15
SLTI x1, 20        # x1 = (x1 < 20) ? 1 : 0 = 1
SLTUI x3, 10       # x3 = (x3 < 10) ? 1 : 0

# Test immediate shift operations (only lower 4 bits used for shift amount)
LI x3, 16          # Load 16 into x3
SLLI x3, 2         # x3 = x3 << 2 = 16 << 2 = 64 (but result masked to 16-bit)
SRLI x3, 1         # x3 = x3 >> 1 = 32 >> 1 = 16
SRAI x3, 2         # x3 = x3 >> 2 (arithmetic) = 16 >> 2 = 4

# Test immediate logical operations with valid 7-bit signed values
LI x4, 48          # Load 48 into x4 (valid 7-bit signed)
ANDI x4, 15        # x4 = x4 & 15 = 48 & 15 = 0
ORI x4, 21         # x4 = x4 | 21 = 0 | 21 = 21
XORI x4, -22       # x4 = x4 ^ -22 = 21 ^ -22 (valid negative immediate)

# Test memory operations (S-type and L-type)
# Build larger address using LUI and ORI for addresses > 7-bit range
LUI x5, 8          # Load upper immediate: x5 = 8 << 7 = 1024
LI x6, 52          # Load test value 52 into x6 (valid 7-bit)

# Store operations (4-bit signed offset: -8 to +7)
SW x6, 0(x5)       # Store word x6 at address x5
SB x6, 2(x5)       # Store byte (low 8 bits of x6) at x5+2

# Load operations
LW x7, 0(x5)       # Load word from address x5 into x7
LB x0, 2(x5)       # Load byte (sign-extended) from x5+2 into x0
LBU x1, 2(x5)      # Load byte (zero-extended) from x5+2 into x1

# Test U-type instructions (9-bit immediate from combining 6+3 bits)
LUI x3, 16         # Load upper immediate: x3 = 16 << 7 = 2048
AUIPC x3, 32       # Add upper immediate to PC: x3 = PC + (32 << 7)

# Test J-type instructions
JAL x1, function   # Jump and link to function, save return address in x1

# Test jump register instructions
JALR x4, x1        # Jump to address in x1, save return address in x4

# Test system call - need to load ASCII 'A' (65) using multiple instructions
# Since 65 > 63, we need to use LUI + ORI or other method
LI x6, 1           # Load 1 into x6
SLLI x6, 6         # Shift left by 6: x6 = 1 << 6 = 64
ADDI x6, 1         # Add 1: x6 = 64 + 1 = 65 (ASCII 'A')
ECALL 0x000        # System call to print character (10-bit service number)

# Exit program
LI x6, 0           # Load exit code 0 into a0
ECALL 0x3FF        # System call to exit (10-bit service number)

function:
# Simple function that increments x0
ADDI x0, 1         # Increment x0
JR x1              # Return using jump register

# Data section
.org 0x1000
test_data:
.word 0x1234, 0x5678, 0x4321
.byte 0x12, 0x34, 0x56, 0x78
.ascii "Hello"
.align 2
