.text
main:
    lui t0, 0xF1
    slli t0, 1
    ori t0, 0x2C
    lb s0, 0(t0)    #s0 = scoreA
ecall 10