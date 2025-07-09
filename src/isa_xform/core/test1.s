.text
.global main
main:
    lui t0, 0xFA
    slli t0, 1
    li t1, 3
    sb t1, 0(t0)
    NOP
    ecall 10
