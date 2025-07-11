.text
main:
    li t0, 1
    j skip
    li t0, 50  # should be skipped
skip:
    li t0, 2
    j main     # negative offset jump (backwards) 