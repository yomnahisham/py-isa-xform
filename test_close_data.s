.text
.org 0x0020
.global main
main:
    la t0, words
    la x0, name
    ecall 10

.data
.org 0x0040  # Place data very close to code (only 32 bytes away)
words: .word 0xABCD, 0x1111
name: .ascii "Hello, World!\n" 