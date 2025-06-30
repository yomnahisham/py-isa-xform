; Disassembly of ZX16 v1.0
; Word size: 16 bits
; Endianness: little

    0100: LI x6, 10
    0102: LI x7, 0xFFFFFFFB
    0104: LI x6, 63
    0106: LI x7, 0xFFFFFFC0
    0108: JAL x1
    010A: JAL x1
    010C: BEQ x6, x7
    010E: BNE x6, x7
    0110: J 0, 0
    0112: ADD x6, x7
    0114: LW x6
    0116: SW x7
    0118: ADDI x6, 20
    011A: ADDI x7, 0xFFFFFFF6
    011C: SLTI x6, 50
    011E: ANDI x6, 15
    0120: ORI x7, 63
    0122: XORI x6, 63
    0124: SLLI x6, 2
    0126: SLLI x7, 1
    0128: SLLI x6, 3
    012A: LUI x6, 63
    012C: AUIPC x7, 31
    012E: ECALL 0
    0130: ADD x6, x7
    0132: ADD x6, x7
    0134: JR x1
    0136: SUB x6, x7
    0138: ADDI x6, 5
    013A: JR x1

; Data sections:
    013C: 34 12
    013E: 78 56
    0140: BC 9A
    0142: F0 DE