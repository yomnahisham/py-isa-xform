; Main program file for multi-file assembly demonstration
; Uses SimpleRISC16 ISA

        .org 0x1000          ; Set program origin

; Entry point
_start: LDI R1, #10          ; Load test value
        CALL init_system     ; Initialize system (defined in system.s)
        CALL process_data    ; Process data (defined in data.s)
        
        ; Test arithmetic operations
        ADD R3, R1, R2       ; Add values
        SUB R4, R3, R1       ; Subtract values
        
        ; Test memory operations
        LDI R5, #data_section ; Load data section address
        ST R3, 0(R5)         ; Store result
        LD R6, 0(R5)         ; Load it back
        
        ; Test conditional logic
        JZ error_handler     ; Jump if zero
        JNZ success_handler  ; Jump if not zero
        
        JMP main_loop        ; Infinite loop

; Main processing loop
main_loop:
        NOP                  ; Wait
        CALL check_status    ; Check system status
        JMP main_loop        ; Continue loop

; Success handler
success_handler:
        LDI R7, #0x42        ; Success code
        JMP finish

; Error handler  
error_handler:
        LDI R7, #0xFF        ; Error code
        JMP finish

; Program termination
finish: NOP                  ; End program
        RET                  ; Return (or halt)

; Data section
        .org 0x2000          ; Data starts at 0x2000
data_section:
        .word 0x1234         ; Test data
        .word 0x5678         ; More test data
        .space 16            ; Reserved space
        .ascii "Hello"       ; String data
        .byte 0              ; Null terminator 