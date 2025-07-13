; Simple test for AUIPC and ADDI instructions
.org 0x20
 
main:
    AUIPC x1, 0x10    ; Add upper immediate to PC
    ADDI x2, 5        ; Add immediate
    ADD x3, x1, x2    ; Add registers 