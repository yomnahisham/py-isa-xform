<<<<<<< HEAD
# ZX16 Instruction Test Program (Corrected for all immediate constraints)
# Tests all instructions except B-type (branch) instructions

.org 32                 # Start at default code address

main:
# Test R-type instructions with valid immediates
LI x0, 10          # Load immediate 10 into x0 (valid: within -64 to +63)
LI x1, 5           # Load immediate 5 into x1

# Test ADD
ADD x0, x1         # x0 = x0 + x1 = 10 + 5 = 15

# Test SUB  
SUB x0, x1         # x0 = x0 - x1 = 15 - 5 = 10

# Test SLT (Set Less Than)
SLT x3, x1         # x3 = (x3 < x1) ? 1 : 0

# Test SLTU (Set Less Than Unsigned)
SLTU x3, x1        # x3 = (x3 < x1) ? 1 : 0

# Test logical operations with valid immediates
LI x4, 63          # Load 63 (max positive 7-bit signed) into x4
LI x5, 15          # Load 15 into x5

AND x4, x5         # x4 = x4 & x5 = 63 & 15 = 15
OR x4, x0          # x4 = x4 | x0 = 15 | 10 = 15
XOR x4, x5         # x4 = x4 ^ x5 = 15 ^ 15 = 0

# Test shift operations
LI x6, 8           # Load 8 into x6
LI x7, 2           # Load 2 into x7 (shift amount)

SLL x6, x7         # x6 = x6 << 2 = 8 << 2 = 32
SRL x6, x7         # x6 = x6 >> 2 = 32 >> 2 = 8

# Test arithmetic shift with negative number
LI x6, -8          # Load -8 into x6 (valid: within -64 to +63)
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
=======
# --- Print integer 42 ---
ADDI x6, 42       # x6 (a0) = 0 + 42
ECALL 1           # ecall 1: print int

# --- Print string "Hello" ---
AUIPC x6, 0       # x6 = PC (current address)
ADDI  x6, msg # x6 = x6 + offset to msg
ECALL 2           # ecall 2: print string

# --- Exit ---
ECALL 3           # ecall 3: exit

# --- Data section ---
.data
msg: .ascii "Hello"
.byte 0           # zero-terminated
>>>>>>> 1faeca9 (fixing ecalls in simulator)
