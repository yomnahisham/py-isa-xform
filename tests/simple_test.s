; Simple test for ZX16
.org 0x1000

start:
    ADD x1, x2
    SUB x3, x4
    ADDI x5, 42
    LW x6, 4(x7)
    SW x1, 4(x2)
    BEQ x3, x4, branch_target
    JAL x4, branch_target
    NOP
    JMP branch_target
    CLR x5
    INC x6
    DEC x7
    LA x1, data_label
    J branch_target
    ECALL 0

branch_target:
    LI x2, 63
    JR x3

.org 0x2000

data_label:
    .word 0x5678
    .byte 0xAA, 0xBB
    .ascii "Hello"
    .asciiz "World" 