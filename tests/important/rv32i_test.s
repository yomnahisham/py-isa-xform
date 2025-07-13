.section .text
.globl _start
_start:
    addi x1, x0, 42      # x1 = 42
    addi x2, x1, 8       # x2 = x1 + 8
    add x3, x1, x2       # x3 = x1 + x2
    sub x4, x2, x1       # x4 = x2 - x1
    sw x3, 0(x0)         # store x3 to memory[0]
    lw x5, 0(x0)         # load from memory[0] to x5
    beq x3, x5, _start   # branch if equal
    jal x6, _start       # jump and link 