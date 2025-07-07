; Test LA instruction only
.org 0x20

main:
    LA x1, message    ; Load address of message into x1
    ADD x0, x0        ; NOP

.data
.org 0x8000

message:
    .asciiz "Test" 