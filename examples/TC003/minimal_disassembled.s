; Disassembly of SimpleRISC16 v1.0
; Word size: 16 bits
; Endianness: little

    1000: [05 51] LDI R1, #5
    1002: [0A 52] LDI R2, #10
    1004: [12 13] ADD R3, R1, R2
    1006: [31 24] SUB R4, R3, R1
    1008: [0A 80] JMP 0xA
    100A: [00 00] NOP