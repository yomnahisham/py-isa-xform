; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    0020: LI16 x0, 0 ; pseudo: LI16
    0022: ORI x0, 18
    0024: LI16 x1, 0 ; pseudo: LI16
    0026: ORI x1, 52
    0028: LI16 x2, 0 ; pseudo: LI16
    002A: ORI x2, 48
    002C: ADD x3, x1
    002E: SUB x4, x0
    0030: SLT x5, x2
    0032: AND x6, x1
    0034: OR x7, x2
    0036: CLR x0, x2 ; pseudo: CLR
    0038: SLLI x1, 2
    003A: SLLI x2, 1
    003C: SLLI x3, 3
    003E: CALL x1, 0x7FFFFFF50 ; pseudo: CALL
    0040: POP x4, 4(x0) ; pseudo: POP
    0042: SW x3, 7(x0)
    0044: CALL x1, 0x7FFFFFF50 ; pseudo: CALL
    0046: ECALL 0x3FF
    0048: ADD x5, x1
    004A: SUB x6, x3
    004C: RET x1 ; pseudo: RET
    004E: AND x7, x5
    0050: OR x0, x7
    0052: CLR x1, x2 ; pseudo: CLR
    0054: RET x1 ; pseudo: RET

; Data sections:
    ; Data section at 0x8000
    8000: .word 0x0012
    8002: .word 0x0034
    8004: .word 0x0030