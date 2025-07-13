; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    LUI x0, 0x0
    ORI x0, 18
    LUI x1, 0x0
    ORI x1, 52
    LUI x2, 0x0
    ORI x2, 48
    ADD x3, x1
    SUB x4, x0
    SLT x5, x2
    AND x6, x1
    OR x7, x2
    XOR x0, x2
    SLLI x1, 2
    SRLI x2, 1
    SRAI x3, 3
    JAL x1, 0x48
    LW x4, 4(x0)
    SW x3, 7(x0)
    JAL x1, 0x4E
    ECALL 1023
    ADD x5, x1
    SUB x6, x3
    JR x1
    AND x7, x5
    OR x0, x7
    XOR x1, x2
    JR x1

; Data sections:
    .word 0x0012, 0x0034, 0x0030