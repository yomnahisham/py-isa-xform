; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: NOP ; pseudo: NOP
    0022: CLR x1 ; pseudo: CLR
    0024: INC x2 ; pseudo: INC
    0026: INC x3 ; pseudo: INC
    0028: LA x4, 0x40 ; pseudo: LA
L_002C:
    002C: LI x5, 42
    002E: LI16 x6, 9 ; pseudo: LI16
    0032: BEQ x1, x2, 0x2C
    0034: JMP label ; pseudo: JMP
loop:
    0036: NOP ; pseudo: NOP
    0038: BEQ x1, x5, 0x3C
    003A: JMP label ; pseudo: JMP
L_003C:
    003C: CALL x1 ; pseudo: CALL
function:
    003E: INC x2 ; pseudo: INC
    0040: SW x3, 0(x2)
    0042: NOP ; pseudo: NOP
    0044: POP x3, 0(x2) ; pseudo: POP
    0048: RET x1 ; pseudo: RET
end:
    004A: LW x1, 0(x4)
    004C: SW x5, 0(x4)
    004E: NOP ; pseudo: NOP

; Data sections:
    ; Data section at 0x8000
    8000: .asciiz "Hello World"
    800C: .word 0x1234
    800E: .word 0x5678
    8010: .word 0x9ABC
    8012: .word 0x0000
    8014: .word 0x0000
    8016: .word 0x0000
    8018: .word 0x0000
    801A: .word 0x0000
    801C: .word 0x0000
    801E: .word 0x0000
    8020: .word 0x0000
    8022: .word 0x002A
    8024: .word 0x0064
    8026: .word 0x00FF