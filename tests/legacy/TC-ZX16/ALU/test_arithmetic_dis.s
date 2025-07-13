; Disassembly of ZX16 v1.0
; Word size: 16 bits
; Endianness: little

    LI x6, 10
    LI x7, 5
    LI x5, 3
    LI x3, 2
    ADD x6, x7
    SUB x6, x7
    ADDI x6, 20
    ADDI x6, 0xFFFFFFFB
    AND x6, x5
    OR x6, x3
    XOR x6, x7
    SLT x6, x5
    SLTU x6, x3
    SLL x6, x5
    SRL x6, x3
    SRA x6, x5
    MV x7, x6
    ECALL 0