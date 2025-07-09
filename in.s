.text
.org 0x0020
.global main
main:
    la t0, words
    addi x7, 51
    sw x7, 0(t0)  # Store value 151 at address of words
    lw x1, 0(t0)  # Load first word
    ecall 10

.data
.org 0x0040  # Place data very close to code (only 32 bytes away)
words: .word 0xABCD, 0x1111
name: .ascii "Hello, World!\n"