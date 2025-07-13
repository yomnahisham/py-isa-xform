; Test file for variable-length instructions
; This demonstrates instructions of different sizes: 8-bit, 16-bit, 32-bit, and 64-bit

.org 0x1000

_start:
    ; 8-bit instructions (1 byte each)
    NOP         ; 0x00 - 8 bits
    RET         ; 0x01 - 8 bits
    
    ; 16-bit instructions (2 bytes each)
    ADD r1, r2, r3    ; 0x02 + registers - 16 bits
    
    ; 32-bit instructions (4 bytes each)
    ADDI r4, r5, #42      ; 0x03 + registers + immediate - 32 bits
    LUI r6, #0x1234       ; 0x04 + register + immediate - 32 bits
    JMP _start            ; 0x05 + target address - 32 bits
    
    ; 64-bit instruction (8 bytes)
    COMPLEX r7, r8, r9, r10, #0x12345678  ; 0x06 + 4 registers + immediate - 64 bits
    
    ; Mix of different sizes
    NOP
    ADD r11, r12, r13
    ADDI r14, r15, #-100
    NOP
    RET

; Data section
.org 0x2000
data_start:
    .word 0x12345678
    .word 0xABCDEF01
    .byte 0x42, 0x43, 0x44 