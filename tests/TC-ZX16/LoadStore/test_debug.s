# Debug test for offset encoding
.org 32

main:
LI x5, 42
SW x6, 2(x5)  # This should encode offset=2, rs2=x6, rs1=x5 