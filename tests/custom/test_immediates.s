; Test program with immediate values for ZX16
.org 0x100

start:
    LI a0, 10          ; Load immediate 10
    LI a1, -5          ; Load immediate -5
    LI a0, 63          ; Load immediate max positive (63)
    LI a1, -64         ; Load immediate min negative (-64)
    ADDI a0, 20        ; Add immediate 20
    ADDI a1, -10       ; Add immediate -10
    LUI a0, 63         ; Load upper immediate (max 6-bit)
    AUIPC a0, 31       ; Add upper immediate to PC (max 5-bit) 