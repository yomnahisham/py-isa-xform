; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

    0020: LI t0, 0
    0022: BZ t0, 0x26
    0024: LI t0, 5
skip:
    0026: LI t0, 20
    0028: ECALL 10