; Test program with custom instructions
.org 0x100

start:
    LI x6, 10          ; Load immediate 10
    LI x7, 5           ; Load immediate 5
    ADD x6, x7         ; Standard add: x6 = 10 + 5 = 15
    MULT x6, x7        ; Custom multiply: x6 = 15 * 5 = 75
    SWAP x6, x7        ; Custom swap: x6=5, x7=75
    CRC16 x6, x7       ; Custom CRC16 calculation 