# Test ASCII data detection
.text
.globl main

main:
    LI a0, 45          # ASCII 'A' (fits in 7-bit signed range)
    ECALL 0            # Print character
    
    LI a0, 10          # ASCII newline
    ECALL 0            # Print character
    
    LI a0, 46          # ASCII 'B' (fits in 7-bit signed range)
    ECALL 0            # Print character
    
    LI a0, 10          # ASCII newline
    ECALL 0            # Print character
    
    LI a0, 42          # Exit code
    ECALL 0x3F         # Exit program (fits in 10-bit field)

.data
hello_str:
    .ascii "Hello, World!\n"
    .byte 0

; Test ASCII string detection in disassembler
.org 0x100

start:
    LI a0, 10
    ADD a0, a1
    JR ra

; Data section with mixed content
data_start:
    .word 0x1234
    .ascii "Hello, World!"
    .word 0x5678
    .ascii "Test String"
    .byte 0xFF, 0x00 