.text
.org 0x0020
.global main
main:
ecall 2
loop:
addi x7, 0
ecall 7
bz a1, loop
ecall 10