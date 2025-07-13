; Test LB instruction only
.org 0x1000

start:
    LB x1, 0(x2)
    NOP 