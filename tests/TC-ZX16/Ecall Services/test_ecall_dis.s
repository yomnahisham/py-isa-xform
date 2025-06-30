; Disassembly of ZX16 v1.0
; Word size: 16 bits
; Endianness: little

    LI x6, 45
    ECALL 0
    LI x6, 10
    ECALL 0
    ECALL 0
    ECALL 0
    LI x6, 10
    ECALL 0
    LI x6, 42
    ECALL 0

; Data sections:
    0034: 48 65
    0036: 6C 6C
    0038: 6F 00