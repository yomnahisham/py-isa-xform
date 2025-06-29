; Crazy ISA Test Program
; This program tests the flexible field sizes and unusual features

.org 0x1000

start:
    LDI R1, #0x12345        ; Test 20-bit immediate (should work now!)
    LDI R2, #0x67890        ; Another large immediate
    ADD R3, R1, R2          ; Add them together
    
    ; Test memory operations with large offsets
    LDI R5, #0x8000         ; Load base address
    ST R3, 0x100(R5)        ; Store with 16-bit offset
    LD R6, 0x100(R5)        ; Load with 16-bit offset
    
    ; Test conditional jumps with proper label resolution
    JZ start                ; Jump to start if zero
    JNZ loop                ; Jump to loop if not zero
    
    ; Test subroutine call
    CALL subroutine         ; Call subroutine
    
    ; Test the crazy instruction
    CRAZY R7, #0xDEAD       ; Do something crazy!
    
    ; Infinite loop
loop:
    NOP                     ; No operation
    JMP loop                ; Jump back to loop
    
    ; Subroutine
subroutine:
    LDI R9, #0x42           ; Load magic number
    RET                     ; Return from subroutine
    
    ; Data section
    .org 0x8000             ; Set origin for data
data:
    .word 0x12345678        ; Define a 32-bit word
    .byte 0xAB              ; Define a byte
    .space 16               ; Reserve 16 bytes
    .crazy 0xCAFEBABE       ; Define crazy data 