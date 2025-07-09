; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: AUIPC x0, 64
    0022: ADDI x0, 0
    0024: AUIPC x0, 64
    0026: ADDI x0, 4
    0028: ECALL 10

; Data sections:
    ; Data section at 0x8000
    8000: .word 0xABCD
    8002: .word 0x1111
    8004: .ascii "Hello, World!\n"