.text
main:
    li t0, 1
    j far_label
    li t0, 50  # should be skipped
    li t0, 40  # should be skipped
    li t0, 30  # should be skipped
far_label:
    li t0, 42
    ecall 10 