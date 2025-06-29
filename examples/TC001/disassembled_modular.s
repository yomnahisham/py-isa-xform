; Disassembly of SimpleRISC16 v1.0
; Word size: 16 bits
; Endianness: little

    1000: NOP
    1002: NOP
    1004: NOP
    1006: NOP
    1008: NOP
    100A: NOP
    100C: NOP
    2000: LDI AT, #10
    2002: CALL 0x1A
    2004: CALL 0x28
    2006: ADD V1, AT, V0
    2008: SUB A0, V1, AT
    200A: LDI A1, #0
    200C: ST V1, ZERO, 0x0
    200E: LD A2, ZERO, 0x0
    2010: JZ 0x20
    2012: JNZ 0x1C
    2014: JMP 0x16
    2016: NOP
    2018: CALL 0x22
    201A: JMP 0x16
    201C: LDI A3, #66
    201E: JMP 0x24
    2020: LDI A3, #255
    2022: JMP 0x24
    2024: NOP
    2026: RET
    2028: NOP
    202A: NOP
    202C: NOP
    202E: NOP
    2030: NOP
    2032: NOP
    2034: NOP
    3000: ADD V0, V1, A0
    3002: LDI A2, #120
    3004: NOP
    3006: NOP
    3008: NOP
    300A: NOP
    300C: NOP
    300E: NOP
    3010: NOP
    3014: LD A1, A0, 0x-8
    3016: LD T4, A2, 0x-4
    3018: NOP
    301A: LDI T0, #0
    301C: LDI T1, #0
    301E: LDI T2, #1
    3020: RET
    3022: LD T3, ZERO, 0x0
    3024: AND T4, T3, T2
    3026: RET
    3028: LDI V0, #20
    302A: ADD T5, AT, V0
    302C: SUB S0, T5, AT
    302E: AND S1, T5, S0
    3030: OR ZERO, T5, S0
    3032: RET
    3034: LDI AT, #0
    3036: JZ 0x3C
    3038: LDI AT, #1
    303A: RET
    303C: LDI AT, #0
    303E: RET

; Data sections:
    1000: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    2028: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    3004: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00