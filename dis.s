; Disassembly of ZX16 v1.0
; Word size: 16 bits
; Endianness: little

    LI x0, 10
    ADDI x0, 0xFFFFFFFF
    BNZ x0, 0
    LI x6, 0
    ECALL 0x3FF