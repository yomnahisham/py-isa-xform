; Disassembly of SimpleRISC16 v1.0
; Word size: 16 bits
; Endianness: little

    1000: [0A 51] LDI R1, #10
    1002: [14 52] LDI R2, #20
    1004: [12 13] ADD R3, R1, R2
    1006: [21 24] SUB R4, R2, R1
    1008: [00 55] LDI R5, #0
    100A: [00 73] ST R3, R0
    100C: [00 66] LD R6, R0
    100E: [00 90] JZ 0x0
    1010: [18 A0] JNZ 0x18
    1012: [1C B0] CALL 0x1C
    1014: [12 37] AND R7, R1, R2
    1016: [12 48] OR R8, R1, R2
    1018: [00 00] NOP
    101A: [18 80] JMP 0x18
    101C: [2A 59] LDI R9, #42
    101E: [00 C0] RET
    1020: [00 00] NOP
    1022: [00 00] NOP
    1024: [00 00] NOP
    1026: [00 00] NOP
    1028: [00 00] NOP
    102A: [00 00] NOP
    102C: [00 00] NOP
    2000: [34 12] ADD R2, R3, R4
    2002: [56 00] NOP
    2004: [00 00] NOP
    2006: [00 00] NOP
    2008: [00 00] NOP
    200A: [00 00] NOP

; Data sections:
    1020: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    200C: 00