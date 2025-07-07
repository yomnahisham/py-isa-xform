; Disassembly of ZX16 v1.0
; Word size: 16 bits
; Endianness: little

    LI x6, 10
    LI x7, 0xFFFFFFFB
    LI x6, 63
    LI x7, 0xFFFFFFC0
    JAL x1
    JAL x1
    BEQ x6, x7, 4
    BNE x6, x7, 4
    J
    ADD x6, x7
    LW x6, 4(x7)
    SW x7, 4(x6)
    ADDI x6, 20
    ADDI x7, 0xFFFFFFF6
    SLTI x6, 50
    ANDI x6, 15
    ORI x7, 63
    XORI x6, 63
    SLLI x6, 2
    SLLI x7, 1
    SLLI x6, 3
    LUI x6, 63
    AUIPC x7, 31
    ECALL 0x3FF
    ADD x6, x7
    ADD x6, x7
    JR x1
    SUB x6, x7
    ADDI x6, 5
    JR x1

; Data sections:
    .word 0x1234
    .word 0x5678
    .word 0x9ABC
    .word 0xDEF0