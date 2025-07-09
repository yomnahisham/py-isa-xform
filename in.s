
.data
words: .word 0xABCD, 0x1111
name: .ascii "Hello, World!\n"

.text
.global main
main:
    LI16 x1, 0x1234
    la t0, words
    la x0, name
    ecall 10