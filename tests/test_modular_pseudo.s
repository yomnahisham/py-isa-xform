; Test case for modular pseudo-instruction handling
.org 0x20

main:
    LI x1, #5         ; Load immediate 5 into x1
    LI x2, #10        ; Load immediate 10 into x2
    ADD x3, x1, x2    ; Add x1 and x2, store in x3
    LA x4, message    ; Load address of message into x4
    JMP loop          ; Jump to loop

loop:
    ADD x1, x1, x2    ; Add x2 to x1
    BEQ x1, x2, end   ; Branch to end if x1 == x2
    J loop            ; Jump back to loop (using J pseudo-instruction)

end:
    ADD x0, x0        ; NOP (add zero to zero)

.data
.org 0x8000

message:
    .asciiz "Hello World"

value:
    .word 0x1234 