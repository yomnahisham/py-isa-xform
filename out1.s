; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: LA x0, 0x40 ; pseudo: LA ; words
    0024: POP x1, 0(x0) ; pseudo: POP
    0026: POP x3, 4(x0) ; pseudo: POP
    0028: ECALL 10

; Data sections:
    ; Data section at 0x0040
    0040: .word 0xABCD
    0042: .word 0x1111
    0044: .ascii "Hello, World!\n"