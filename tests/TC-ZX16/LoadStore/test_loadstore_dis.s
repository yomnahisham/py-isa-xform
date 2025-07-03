; Disassembly of ZX16 v1.0
; Word size: 16 bits
; Endianness: little

    LI x5, 42
    LI x6, 18
    SW x6, 0(x5)
    SB x6, 2(x5)
    LW x7, 0(x5)
    LB x0, 2(x5)
    SW x6, 0xFFFFFFFC(x5)
    LW x1, 0xFFFFFFFC(x5)