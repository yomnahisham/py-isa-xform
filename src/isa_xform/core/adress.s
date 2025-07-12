; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: LI x0, 63
    0022: LUI x5, 0xFF
    0024: LI x3, 123
    0026: JR x3
    0028: ADDI x0, 5
    002A: ANDI x0, 3
    002C: ORI x0, 7
I-type:
    002E: ECALL 10