; Test LA (Load Address) pseudo-instruction
.org 0x1000

start:
    LA x1, data_label    ; Load address of data_label into x1
    LA x2, 0x1234        ; Load immediate address 0x1234 into x2
    LA x3, 0x5678        ; Load immediate address 0x5678 into x3

.org 0x2000

data_label:
    .word 0xABCD
    .byte 0x42 