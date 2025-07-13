    .org 32      # Start code at default code section

main:
    BGE x0, x0, 0
    # Load address of myint into x3
    LA x3, myint         # x3 = address of myint

    # Read original value into x4
    LW x4, 0(x3)         # x4 = [myint]

    # Change value: add 5
    LI x5, 5
    ADD x4, x5           # x4 = x4 + 5

    # Store new value back to myint
    SW x4, 0(x3)         # [myint] = x4

    # Read back to x6 to verify
    LW x6, 0(x3)         # x6 = [myint] (should be original + 5)

    # Exit program
    LI x6, 0
    ECALL 0x00A

.data
myint:  .word 123        # Initial value: 123
