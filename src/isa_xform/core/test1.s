.text
main:
# ========== Set Palette at address 0x01AC ==========
    li t0, 0x0
    li t1, 0x03      # RGB: 00000011 (blue)
    sb t1, 0(t0)
    addi t0, 1

    li t1, 0x1C      # RGB: 00011100 (green)
    sb t1, 0(t0)
    addi t0, 1

# ========== Done ==========
    ecall 10
