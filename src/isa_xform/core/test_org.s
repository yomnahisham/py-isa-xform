.text
main:
    li t0, 63
    lui t1, 0xFF
    li s0, 0x2E   
    jal ra, I-type        #implements PC = offset
    addi t0, 5
    andi t0, 3
    ori t0, 7
I-type:
    ecall 10