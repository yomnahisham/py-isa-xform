; Disassembly of RV32I v2.1
; Word size: 32 bits
; Endianness: little

    ADDI ra, zero, 42
    ADDI sp, ra, 8
    ADD gp, ra, sp
    SUB tp, sp, ra
    SW gp, zero
    LW t0, 0(zero)
    BEQ gp, t0, 0xFC0020
    JAL t1, 0x7FF00