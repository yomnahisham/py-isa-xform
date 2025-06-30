; Disassembly of ZX16 v1.0
; Word size: 16 bits
; Endianness: little

    LI x6, 10
    LI x7, 0xFFFFFFFB
    LI x6, 63
    LI x7, 0xFFFFFFC0
    JAL x1
    JAL x1
    BEQ x6, x7
    BNE x6, x7
    J 0, 0
    ADD x6, x7
    LW x6
    SW x7
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
    ECALL 0
    ADD x6, x7
    ADD x6, x7
    JR x1
    SUB x6, x7
    ADDI x6, 5
    JR x1

; Data sections:
    005C: 34 12
    005E: 78 56
    0060: BC 9A
    0062: F0 DE