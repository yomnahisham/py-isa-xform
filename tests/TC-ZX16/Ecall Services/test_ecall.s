# ZX16 Simple ECALL Test Case
# Demonstrates ECALL services without problematic pseudo-instructions

.text
.globl main

main:
    # --- Print a single character ('A') ---
    LI a0, 45          # ASCII 'A' (fits in 7-bit signed range)
    ECALL 0            # Print character in a0

    # --- Print a newline ---
    LI a0, 10          # ASCII newline '\n'
    ECALL 0            # Print character in a0

    # --- Read a character from user ---
    ECALL 1            # Read char into a0

    # --- Echo the character back ---
    ECALL 0            # Print character in a0

    # --- Print a newline ---
    LI a0, 10
    ECALL 0

    # --- Exit with code 42 ---
    LI a0, 42
    ECALL 1023         # Exit program with code in a0

.data
hello_str:
    .ascii "Hello, ZX16!\n"
    .byte 0 