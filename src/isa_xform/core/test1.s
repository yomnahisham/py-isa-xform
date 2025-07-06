.text    
main:
# ========== Set Color Palette ==========
    li t0, 60        # 60 × 1024 = 61440 = 0xF000
    slli t0, 10      # t0 = 60 << 10 = 0xF000

    addi t0, 63      # t0 = 0xF000 + 63 = 0xF03F
    addi t0, 63      # t0 = 0xF03F + 63 = 0xF07E
    addi t0, 63      # t0 = 0xF07E + 63 = 0xF0BD
    addi t0, 63      # ...
    addi t0, 63
    addi t0, 63
    addi t0, 63
    addi t0, 63
    addi t0, 56      # Now t0 = 0xFA00

    li t1, 3           # RGB = 00000011 - blue
    sb t1, 0(t0)       # palette[0] = blue

# ========== Set Tile Definition ==========
li t0, -14        # -14 = 0xF2 (two's complement, signed 7-bit OK)
slli t0, 8        # t0 = 0xF200
   li t1, 63
addi t1, 63       # t1 = 64 + 64 = 128
addi t1, 2

    li s0, 0           # each byte = two of palette[0] - 00

fill_tile_data:
    sb s0, 0(t0)
    addi t0, 1
    addi t1, -1
    bnz t1, fill_tile_data

# ========== Set Tile Map ==========
    li t0, 60        # 60 << 10 = 61440 = 0xF000
slli t0, 10    # t0 = 0xF000

    li t1, 63          # t1 = 64
    addi t1, 63
    addi t1, 63
    addi t1, 63
addi t1, 48

    li s0, 0           # blue -> tile[0]

fill_tile_map:
    sb s0, 0(t0)       # store tile index 0
    addi t0, 1
    addi t1, -1
    bnz t1, fill_tile_map

# ========== Done ==========
    ecall 10   