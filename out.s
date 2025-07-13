; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    0020: LUI x0, 0xF1
    0022: SLLI x0, 1
    0024: ADDI x0, 44
    0026: LI x5, 1
    0028: SB x5, 0(x0)
    002A: ECALL 10