; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: LI x0, 1
    0022: JMP 0x26 ; pseudo: JMP
    0024: LI x0, 20
done:
    0026: ECALL 10