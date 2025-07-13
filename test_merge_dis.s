; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    AUIPC x0, 500
    ADDI x0, -32
    LB x5, 0(x0)
    ECALL 10

; Data sections:
    .word 0x1111