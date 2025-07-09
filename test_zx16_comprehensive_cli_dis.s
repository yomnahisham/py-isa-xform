; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    LI16 x0, 0 ; pseudo: LI16
    ORI x0, 18
    LI16 x1, 0 ; pseudo: LI16
    ORI x1, 52
    LI16 x2, 0 ; pseudo: LI16
    ORI x2, 48
    ADD x3, x1
    SUB x4, x0
    SLT x5, x2
    AND x6, x1
    OR x7, x2
    CLR x0, x2 ; pseudo: CLR
    SLLI x1, 2
    SLLI x2, 1
    SLLI x3, 3
    CALL x1, 0x7FFFFFF50 ; pseudo: CALL
    POP x4, 4(x0) ; pseudo: POP
    SW x3, 7(x0)
    CALL x1, 0x7FFFFFF50 ; pseudo: CALL
    ECALL 0x3FF
    ADD x5, x1
    SUB x6, x3
    RET x1 ; pseudo: RET
    AND x7, x5
    OR x0, x7
    CLR x1, x2 ; pseudo: CLR
    RET x1 ; pseudo: RET

; Data sections:
    .word 0x0012
    .word 0x0034
    .word 0x0030