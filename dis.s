.org 0x20
.data
array: .space 10

.text

main:
    # Initialize counter to 10
    LI x0, 10       # i = 10
    LI x1, 5        # j = 5
    ADD  x0, x1     # i = i + j
    SUB x0, x1      # i = i - j
    ECALL 10       # system call to exit