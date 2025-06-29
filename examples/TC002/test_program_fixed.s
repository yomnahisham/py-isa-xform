; Test program for SimpleRISC16 ISA
; This program demonstrates various assembly features, using only supported instructions

        .org 0x1000          ; Set origin to 0x1000

start:  LDI R1, #10          ; Load immediate value 10 into R1
        LDI R2, #20          ; Load immediate value 20 into R2
        ADD R3, R1, R2       ; R3 = R1 + R2
        SUB R4, R2, R1       ; R4 = R2 - R1
        
        ; Test memory operations
        LDI R5, #0x2000      ; Load base address
        ST R3, 0(R5)         ; Store R3 to memory[R5 + 0]
        LD R6, 0(R5)         ; Load from memory[R5 + 0] to R6
        
        ; Test conditional jumps
        JZ start             ; Jump to start if zero flag is set
        JNZ loop             ; Jump to loop if zero flag is not set
        
        ; Test subroutine call
        CALL subroutine      ; Call subroutine
        
        ; Test bitwise operations
        AND R7, R1, R2       ; R7 = R1 & R2
        OR R8, R1, R2        ; R8 = R1 | R2
        
        ; Infinite loop
loop:   NOP                  ; No operation
        JMP loop             ; Jump back to loop
        
        ; Subroutine
subroutine:
        LDI R9, #42          ; Load magic number
        RET                  ; Return from subroutine 