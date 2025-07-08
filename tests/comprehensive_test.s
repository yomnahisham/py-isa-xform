; Comprehensive test for all features
; Tests: pseudo-instructions, label resolution, data sections, branches, complex scenarios
.org 0x20

main:
    ; Test pseudo-instructions
    NOP                     ; Should expand to ADD x0, x0
    CLR x1                  ; Should expand to XOR x1, x1
    INC x2                  ; Should expand to ADDI x2, 1
    DEC x3                  ; Should expand to ADDI x3, -1
    LA x4, message          ; Should expand to AUIPC + ADDI
    LI x5, 42               ; Load immediate
    LI16 x6, 0x1234         ; Should expand to LUI + ORI
    
    ; Test control flow with labels
    BEQ x1, x2, end         ; Branch to end
    JMP loop                ; Should expand to J loop
    
loop:
    ADD x1, x2              ; Regular instruction
    BEQ x1, x5, end         ; Branch to end
    J loop                  ; Should expand to J loop
    
    ; Test function calls
    CALL function           ; Should expand to JAL x1, function
    
function:
    PUSH x3                 ; Should expand to ADDI x2, -2; SW x3, 0(x2)
    ADD x6, x7              ; Function body
    POP x3                  ; Should expand to LW x3, 0(x2); ADDI x2, 2
    RET                     ; Should expand to JR x1

end:
    ; Test data access
    LW x1, 0(x4)           ; Load from message address
    SW x5, 0(x4)           ; Store to message address
    
    ; Final NOP
    NOP

.data
.org 0x8000

message:
    .asciiz "Hello World"

numbers:
    .word 0x1234, 0x5678, 0x9ABC

buffer:
    .space 16

constants:
    .word 42, 100, 255 