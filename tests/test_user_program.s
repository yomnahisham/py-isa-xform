.data
words: .word 0xABCD, 0x1111
name: .ascii "Hello, World!\n"

.text
.global main
main:
    la x0, words
    la x0, name
    ecall 3 