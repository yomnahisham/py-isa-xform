; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    LI x3, 0
    LW x1, 0(x3)
    LI x4, 18
    SW x1, 0(x4)
    LW x5, 0(x4)
    SUB x6, x5
    BNZ x6, 0xFFFFFFFA
    LI x3, 12
    LW x1, 0(x3)
    LW x2, 2(x3)
    LI x4, 18
    SW x1, 2(x4)
    SW x2, 4(x4)
    LW x5, 2(x4)
    SUB x6, x5
    BNZ x6, 0xFFFFFFFA
    LW x5, 4(x4)
    SUB x6, x5
    BNZ x6, 0xFFFFFFFA
    LI x0, 0
    J
    LI x0, 1
    MV x6, x0
    ECALL 8
    ECALL 10
    SLTUI x4, 8
    JAL x7
    UNKNOWN ; 0x5678
    UNKNOWN ; 0x6948
    ADD x0, x0
    ADD x0, x0
    ADD x0, x0
    ADD x0, x0
    ADD x0, x0