; Disassembly of ZX16 v1.0
; Word size: 16 bits
; Endianness: little

    LI x6, 10
    ADD x6, x7
    JR x1
    LUI x1, 170
    BLTU x5, x4, 6
    LUI x5, 371

; Data sections:
    .word 0x1234
    .word 0x6548
    .word 0x6C6C
    .word 0x786F
    .word 0x7365
    .word 0x2074
    .word 0x7453
    .word 0x00FF