; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    0020: LI16 x0, 0x12 ; pseudo: LI16
    0024: LI16 x1, 0x34 ; pseudo: LI16
    0028: LI16 x2, 0x30 ; pseudo: LI16
    002C: ADD x3, x1
    002E: SUB x4, x0
    0030: SLT x5, x2
    0032: AND x6, x1
    0034: OR x7, x2
    0036: CLR ; pseudo: CLR
    0038: SLLI x1, 2
    003A: SRLI x2, 1
    003C: SRAI x3, 3
    003E: CALL 0x48 ; pseudo: CALL
    0040: LW x4, 4(x0)
    0042: SW x3, 7(x0)
    0044: CALL 0x4E ; pseudo: CALL
    0046: ECALL 1023
    0048: ADD x5, x1
    004A: SUB x6, x3
    004C: RET ; pseudo: RET
    004E: AND x7, x5
    0050: OR x0, x7
    0052: CLR ; pseudo: CLR
    0054: RET ; pseudo: RET

; Data sections:
    ; Data section at 0x8000
    8000: .word 0x0012, 0x0034, 0x0030