; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    AUIPC x3, 0
    ADDI x3, 46
    LW x4, 0(x3)
    LI x5, 5
    ADD x4, x5
    SW x4, 0(x3)
    LW x6, 0(x3)
    LI x6, 0
    ECALL 10

; Data sections:
    .word 0x007B