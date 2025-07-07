; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    0020: ADD x3, x0
    0022: SUB x4, x2
    0024: SLT x5, x1
    0026: AND x6, x0
    0028: OR x7, x1
    002A: XOR x0, x0
    002C: SLL x1, x0
    002E: SRL x2, x1
    0030: SRA x3, x2
    0032: JAL x1
    0034: LW x4, 4(x0)
    0036: SW x3, 7(x0)
    0038: JAL x1
    003A: ECALL 0x3FF
    003C: ADD x5, x0
    003E: SUB x6, x2
    0040: AND x7, x4
    0042: OR x0, x6
    0044: XOR x1, x0

; Data sections:
    8000: .word 0x1234
    8002: .word 0x5678
    8004: .word 0x9ABC