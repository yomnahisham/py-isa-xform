; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: LI x0, 63
    0022: LUI x5, 0xFF
    0024: AUIPC x3, 28
    #0026: JR x3
    0028: ADD x0, x5
    002A: SUB x0, x5
    002C: AND x0, x5
    002E: OR x0, x5
    0030: XOR x0, x5
    0032: MV x0, x5
    0034: SLT x0, x5
    0036: SLTU x0, x5
    0038: LI x5, 1
    003A: SLL x0, x5
    003C: SRL x0, x5
    003E: SRA x0, x5
    #0040: JALR x1, x3
    #0042: JAL x1, 0x44
I-type:
    0044: ADDI x0, 5
    0046: ANDI x0, 3
    0048: ORI x0, 7
    004A: XORI x0, 2
    004C: SLTI x0, 10
    004E: SLTUI x0, 5
    0050: LI x5, 1
    0052: SRLI x0, 33
    0054: SRAI x0, 65
    0056: SLLI x0, 17
    #0058: JAL x1, 0x5A
B-type:
    005A: LI x0, 5
    005C: LI x5, 5
    #005E: BEQ x0, x5, 0x62
    0060: LI x0, 0
short_branch_target:
    #0062: BNE x0, x5, 0x66
    0064: LI x0, 0
short_branch_target2:
    #0066: BZ x0, 0x6A
    0068: LI x0, 0
short_branch_target3:
    #006A: JAL x1, 0x6C
label:
    #006C: BNZ x0, 0x6C
    #006E: BLT x0, x5, 0x6C
    #0070: BGE x0, x5, 0x6C
Load/store:
    0072: SB x0, 0(x0)
    0074: SW x0, 0(x0)
    0076: LB x0, 0(x0)
    0078: LW x0, 0(x0)
    007A: LBU x0, 0(x0)
    007C: ECALL 10