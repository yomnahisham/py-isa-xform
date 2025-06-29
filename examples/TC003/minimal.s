.org 0x1000
start:
    LDI R1, #5
    LDI R2, #10
    ADD R3, R1, R2
    SUB R4, R3, R1
    JMP end
end:
    NOP 