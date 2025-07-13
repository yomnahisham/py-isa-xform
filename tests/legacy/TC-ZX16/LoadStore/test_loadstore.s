# ZX16 Load/Store Instruction Test Program
# Tests load and store instructions with 4-bit signed offsets

.org 32                 # Start at default code address

main:

# Setup: Load some values into registers
LI x5, 42               # Base address for memory operations (fits in 7-bit signed field)
LI x6, 0x12             # Test value to store (fits in 7-bit signed field)

# Store operations (4-bit signed offset: -8 to +7)
SW x6, 0(x5)           # Store word x6 at address x5
SB x6, 2(x5)           # Store byte (low 8 bits of x6) at x5+2

# Load operations
LW x7, 0(x5)           # Load word from address x5 into x7
LB x0, 2(x5)           # Load byte (sign-extended) from x5+2 into x0

# Test negative offset
SW x6, -4(x5)          # Store word at x5-4
LW x1, -4(x5)          # Load word from x5-4 