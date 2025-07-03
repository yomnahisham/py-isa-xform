# ZX16 Instruction Test Program (Corrected for all immediate constraints)
# Tests all instructions except B-type (branch) instructions

.org 32                 # Start at default code address

main:

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
