; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: LUI x1, 36
    0022: ORI x1, 52
    0024: AUIPC x0, 256
    0026: ADDI x0, 0
    0028: AUIPC x0, 256
    002A: ADDI x0, 4
    002C: ECALL 10

; Data sections:
    ; Data section at 0x8000
    8000: .word 0xABCD
    8002: .word 0x1111
    8004: .ascii "Hello, World!\n"