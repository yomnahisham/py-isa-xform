; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    LI x6, 10
    LI x7, 10
    LI x5, 5
    BEQ x6, x7, 0x4
    LI x6, 50
equal_test:
    BNE x6, x5, 0x4
    LI x6, 40
not_equal_test:
    CLR x4, x4 ; pseudo: CLR
    BZ x4, 4
    LI x6, 30
zero_test:
    LI x4, 1
    BNZ x4, 4
    LI x6, 20
not_zero_test:
    JMP 0x5C ; pseudo: JMP
    LI x6, 10
final_test:
    LI x6, 42
    ECALL 0x3FF