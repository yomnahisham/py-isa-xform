; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    LA x0, 0x8000 ; pseudo: LA ; words
    LA x0, 0x8004 ; pseudo: LA ; name
    ECALL 10

; Data sections:
    .word 0xABCD
    .word 0x1111
    .ascii "Hello, World!\n"