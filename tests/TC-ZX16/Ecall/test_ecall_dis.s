; Disassembly of ZX16 v1.0
; Word size: 16 bits
; Endianness: little

    LI x6, 45
    ECALL 0
    LI x6, 10
    ECALL 0
    ECALL 1
    ECALL 0
    LI x6, 10
    ECALL 0
    LI x6, 42
    ECALL 0x3FF

; Data sections:
    .word 0x6548
    .word 0x6C6C
    .word 0x006F