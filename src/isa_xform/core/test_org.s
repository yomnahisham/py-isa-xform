.data
.org 0xFA00
label: .word 0x1111

.text
main:
la t1, label
lb t0, 0(t1)
ecall 10
