; Test LA + LB combination
.org 0x1000

start:
    LA x1, 0x1234
    LB x2, 0(x1)
    NOP 