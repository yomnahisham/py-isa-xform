; Disassembly of QuantumCore v2.0
; Word size: 32 bits
; Endianness: little

    1000: ADDI r10, zero, #0
    1004: ADDI r11, zero, #0
    1008: ADDI r12, zero, #0
    100C: NOP ; pseudo: NOP
    1010: SUB r14, r10, r11
    1014: LW r15, 0(r12)
    1018: SW r13
    101C: BEQ r10, r11, 0x102C
    1020: ADDI r9, zero, #0
    1024: BEQ r10, r10, 0x102C
    1028: ADDI r8, zero, #0
L_102C:
    102C: ADDI r7, zero, #0
    1030: QUBIT r5, 0
    1034: QUBIT r6, 0
    1038: CALL 0x1040 ; pseudo: CALL
    103C: JMP 0x1048 ; pseudo: JMP
    1040: NOP ; pseudo: NOP
    1044: RET ; pseudo: RET
    1048: ADDI r10, zero, #0
    104C: ECALL

; Data sections:
    ; Data section at 0x8000
    8000: .ascii "xV4"
    8003: .word 0xCDEF0112
    8007: .word 0xADBEEFAB
    800B: .word 0x6C6548DE
    800F: .word 0x202C6F6C
    8013: .word 0x6E617551
    8017: .word 0x206D7574
    801B: .word 0x6C726F57
    801F: .byte 0x64
    8020: .byte 0x21