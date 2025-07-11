; Disassembly of ZX16 v1.0
; Word size: 16 bits
; Endianness: little

    LI x6, 10
    LI x7, 10
    LI x5, 5
    BEQ x6, x7
    LI x6, 50
    BNE x6, x5
    LI x6, 40
    XOR x4, x4
    BZ x4
    LI x6, 30
    LI x4, 1
    BNZ x4
    LI x6, 20
    J 0, 0
    LI x6, 10
    LI x6, 42
    ECALL 0