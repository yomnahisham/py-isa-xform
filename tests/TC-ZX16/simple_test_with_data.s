; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    LI x1, 10
    BNE x4, x4, 7
    BEQ x0, x0, 0
    BZ x0, 0
    ECALL 10

; Data sections:
    .word 0xBEEF
    .ascii "*Hi"
    .word 0x000A
    .word 0x1234
    .asciiz ""