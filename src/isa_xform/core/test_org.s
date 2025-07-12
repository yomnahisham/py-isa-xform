.text
main:
    li t0, 63
    lui t1, 0xFF
    li s0, -5   #s0 = PC + imm -> should jump to I-type address
    jr s0        #implements PC = offset
    addi t0, 5
    andi t0, 3
    ori t0, 7
I-type:
    ecall 10