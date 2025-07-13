.data
.org 0xFA00
label: .word 0x1111

.text
la t0, label
lb t1, 0(t0)
ecall 10 