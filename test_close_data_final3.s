; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: LA x0, 0x40 ; pseudo: LA ; words
    0024: LA x0, 0x44 ; pseudo: LA ; name
    0028: ECALL 10

; Data sections:
    ; Data section at 0x0040
    0040: .word 0xABCD
    0042: .word 0x1111
    0044: .ascii "Hello, World!\n"