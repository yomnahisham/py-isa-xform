; Disassembly of CrazyISA v2.0
; Word size: 32 bits
; Endianness: little

L_1000:
    LDI R1, #0x12345
    LDI R2, #0x67890
    ADD R3, R1, R2
    LDI R5, #0x8000
    ST R3, 0x100(R5)
    LD R6, 0x100(R5)
    JZ 0x1000
    JNZ 0x1028
    CALL 0x1030
    CRAZY R7, #0xDEAD
L_1028:
    NOP
    JMP 0x1028
L_1030:
    LDI R9, #66
    RET
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP

; Data sections:
    1038: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    8000: 78 56 34 12
    8018: 00