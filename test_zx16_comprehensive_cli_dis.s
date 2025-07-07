; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    ADD x3, x0
    SUB x4, x2
    SLT x5, x1
    AND x6, x0
    OR x7, x1
    XOR x0, x0
    SLL x1, x0
    SRL x2, x1
    SRA x3, x2
    JAL x1
    LW x4, 4(x0)
    SW x3, 7(x0)
    JAL x1
    ECALL 0x3FF
    ADD x5, x0
    SUB x6, x2
    AND x7, x4
    OR x0, x6
    XOR x1, x0

; Data sections:
    .word 0x1234
    .word 0x5678
    .word 0x9ABC