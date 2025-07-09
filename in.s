.text
.org 0x0020
.global main
main:
    la t0, words
    lw x1, 0(t0)  # Load first word
    lw x3, 4(t0)  # Load second word
    ecall 10

.data
.org 0x0040  # Place data very close to code (only 32 bytes away)
words: .word 0xABCD, 0x1111
name: .ascii "Hello, World!\n"