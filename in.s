.text
lui t0, 0xF1
slli t0, 1
addi t0, 0x2C
li t1, 1
sb t1, 0(t0)
ecall 10