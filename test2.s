#
# ZX16 Assembly Code: Simple Countdown Loop
#
# This program initializes a counter to 10 and loops until the counter
# reaches zero. The program then exits.
#

# -- Directives --
# Set the origin address for the code. 32 is the default start.
.org 32

# -- Main Program --

LI t0, 10           # Set t0 = 10

loop_start:
DEC t0              # t0 = t0 - 1
BNZ t0, loop_start
LI a0, 0            # Set exit code in a0
ECALL 0x3FF         # Terminate the program


