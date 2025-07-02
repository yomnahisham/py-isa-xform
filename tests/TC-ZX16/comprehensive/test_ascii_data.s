; Test ASCII string detection in disassembler
.org 0x100

start:
    LI a0, 10
    ADD a0, a1
    JR ra

; Data section with mixed content
data_start:
    .word 0x1234
    .ascii "Hello, World!"
    .word 0x5678
    .ascii "Test String"
    .byte 0xFF, 0x00 