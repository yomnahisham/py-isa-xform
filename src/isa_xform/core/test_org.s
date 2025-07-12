.text
main:
    li t0, 63
    lui t1, 0xFF
    auipc s0, 28   #s0 = PC + imm -> should jump to I-type address
    #jr s0        #implements PC = offset
    add t0, t1
    sub t0, t1
    and t0, t1
    or t0, t1
    xor t0, t1
    mv t0, t1
    slt t0, t1
    #sltu t0, t1
    li t1, 1
    sll t0, t1
    srl t0, t1
    sra t0, t1
    #jalr ra, s0
    # Use JAL for longer jumps instead of branches
    jal ra, I-type
I-type:
    addi t0, 5
    andi t0, 3
    ori t0, 7
    xori t0, 2
    slti t0, 10
    #sltui t0, 5
    li t1, 1
    srli t0, 1
    srai t0, 1
    slli t0, 1
    # Use JAL for longer jumps
    jal ra, B-type
B-type:
    # Use very short branches that fit in 4-bit range
    # First, set up a condition that will be true
    li t0, 5
    li t1, 5
    # Now branch with very short distance
    #beq t0, t1, short_branch_target
    # This should never execute
    li t0, 0
short_branch_target:
    # Continue with more short branches
    #bne t0, t1, short_branch_target2
    li t0, 0
short_branch_target2:
    #bz t0, short_branch_target3
    li t0, 0
short_branch_target3:
    # Use JAL for longer jumps
    jal ra, label
label:
    #bnz t0, label  # This is a self-loop, fits in 4-bit range
    #blt t0, t1, label  # This also fits
    #bge t0, t1, label  # This also fits
Load/store:
    sb t0, 0(t0)
    sw t0, 0(t0)
    lb t0, 0(t0)
    lw t0, 0(t0)
    lbu t0, 0(t0)
ecall 10