; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: LI x2, -2
    0022: LI x1, 0
    0024: LI x3, -62
    0026: SB x3, 0(x1)
    0028: LI x3, 0
    002A: SB x3, 1(x1)
    002C: LI x3, -1
    002E: SB x3, 5(x1)
    0030: LI x3, 51
    0032: ADDI x1, 10
    0034: SB x3, -3(x1)
    0036: ADDI x1, -10
    0038: LI x3, 52
    003A: SW x3, -6(x1)
    003C: LI x3, -1
    003E: SW x3, -4(x1)
    0040: LI x3, 0
    0042: SW x3, -2(x1)
    0044: LB x4, 0(x1)
    0046: LB x4, 1(x1)
    0048: LB x4, 5(x1)
    004A: ADDI x1, 10
    004C: LB x4, -3(x1)
    004E: ADDI x1, -10
    0050: LBU x4, 1(x1)
    0052: LI x3, -1
    0054: SB x3, 4(x1)
    0056: LBU x4, 4(x1)
    0058: LW x4, -6(x1)
    005A: LW x4, -4(x1)
    005C: LW x4, -2(x1)
    005E: LI x3, 43
    0060: SB x3, 7(x1)
    0062: LB x4, 7(x1)
    0064: ADDI x1, 8
    0066: LI x3, -51
    0068: SB x3, -8(x1)
    006A: LB x4, -8(x1)
    006C: ADDI x1, -8
    006E: LI x3, -17
    0070: SW x3, 0(x1)
    0072: LW x4, 0(x1)
    0074: LI x3, 34
    0076: SW x3, -2(x1)
    0078: LBU x4, -2(x1)
    007A: LBU x5, -1(x1)
    007C: LI x6, 0
    007E: ECALL 10

; Data sections:
    ; Data section at 0x8000
    8000: .word 0x0000
    8002: .word 0x0000
    8004: .word 0x0000
    8006: .word 0x0000
    8008: .word 0x0000
    800A: .word 0x0000
    800C: .word 0x0000
    800E: .word 0x0000
    8010: .word 0x0000
    8012: .word 0x0000
    8014: .word 0x0000
    8016: .word 0x0000
    8018: .word 0x0000
    801A: .word 0x0000
    801C: .word 0x0000
    801E: .word 0x0000
    8020: .word 0x0000
    8022: .word 0x0000
    8024: .word 0x0000
    8026: .word 0x0000
    8028: .word 0x0000
    802A: .word 0x0000
    802C: .word 0x0000
    802E: .word 0x0000
    8030: .word 0x0000
    8032: .word 0x0000
    8034: .word 0x0000
    8036: .word 0x0000
    8038: .word 0x0000
    803A: .word 0x0000
    803C: .word 0x0000
    803E: .word 0x0000