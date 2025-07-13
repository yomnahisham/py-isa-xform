# Minimal LI16 Test for ZX16

.text
.globl main

main:
LUI x6, 0
ORI x6, x6, 65
ECALL 0 