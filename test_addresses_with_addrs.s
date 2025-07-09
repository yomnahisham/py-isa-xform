; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: LA x0, 0x8000 ; pseudo: LA ; words
    0024: LA x0, 0x8004 ; pseudo: LA ; name
    0028: ECALL 10

; Data sections:
    ; Data section at 0x8000
    8000: .word 0xABCD
    8002: .word 0x1111
    8004: .ascii "Hello, World!\n"