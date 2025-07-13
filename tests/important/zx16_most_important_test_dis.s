; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    LI x0, 63
    LUI x5, 0xFF
    LA x3, 28 ; pseudo: LA
    RET ; pseudo: RET
    ADD x0, x5
    SUB x0, x5
    AND x0, x5
    OR x0, x5
    CLR ; pseudo: CLR
    MV x0, x5
    SLT x0, x5
    SLTU x0, x5
    LI x5, 1
    SLL x0, x5
    SRL x0, x5
    SRA x0, x5
    JALR x1, x3
    CALL 0x44 ; pseudo: CALL
    ADDI x0, 5
    ANDI x0, 3
    ORI x0, 7
    XORI x0, 2
    SLTI x0, 10
    SLTUI x0, 5
    LI x5, 1
    SRLI x0, 1
    SRAI x0, 1
    SLLI x0, 1
    CALL 0x5A ; pseudo: CALL
    LI x0, 5
    LI x5, 5
    BEQ x0, x5, short_branch_target
    LI x0, 0
    BNE x0, x5, short_branch_target2
    LI x0, 0
    BZ x0, short_branch_target3
    LI x0, 0
    CALL 0x6C ; pseudo: CALL
    BNZ x0, label
    BLT x0, x5, label
    BGE x0, x5, label
    SB x0, 0(x0)
    SW x0, 0(x0)
    LB x0, 0(x0)
    LW x0, 0(x0)
    LBU x0, 0(x0)
    ECALL 10