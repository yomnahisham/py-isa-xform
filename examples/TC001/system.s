; System initialization module
; Provides system setup and status checking functions

; System initialization function
init_system:
        LDI R8, #0x100       ; Initialize stack pointer
        LDI R9, #0           ; Clear status register
        LDI R10, #1          ; Set system ready flag
        RET                  ; Return to caller

; Check system status
check_status:
        LD R11, 0(R10)       ; Load system status
        AND R12, R11, R10    ; Check ready flag
        RET                  ; Return with status in R12

; System constants
.equ STACK_BASE, 0x100
.equ STATUS_READY, 1
.equ STATUS_ERROR, 0xFF 