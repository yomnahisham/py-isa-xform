.text
main:
    li t0, 1
    j loop
    li t0, 50  # should be skipped
loop:
    li t0, 2
    j main     # jump back to main (infinite loop) 