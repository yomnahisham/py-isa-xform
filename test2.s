#
# ZX16 Assembly Code: Simple Countdown Loop
#
# This program initializes a counter to 10 and loops until the counter
# reaches zero. The program then exits.
#

# -- Directives --
# Set the origin address for the code. 32 is the default start.
.org 32

.data
array: .space 100

# -- Main Program --
.global main
main:
LA x6, array
ECALL 1
LA x6, array
ECALL 3
ECALL 0xA

