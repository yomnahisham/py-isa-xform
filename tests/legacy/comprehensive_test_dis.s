; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: NOP x0, x0 ; pseudo: NOP
    0022: CLR x1, x1 ; pseudo: CLR
    0024: INC x2, 1 ; pseudo: INC
    0026: INC x3, 0xFFFFFFFF ; pseudo: INC
    0028: LA x4, 0x8000 ; pseudo: LA ; message
    002C: LI x5, 42
    002E: LI16 x6, 9 ; pseudo: LI16
    0030: ORI x6, 52
    0032: BEQ x1, x2, 0xFFFFFFF8
    0034: JMP 0x7FFFFFF10 ; pseudo: JMP
loop:
    0036: ADD x1, x2
    0038: BEQ x1, x5, 0x2
    003A: JMP 0xE0 ; pseudo: JMP
    003C: CALL x1, 0x7FFFFFF10 ; pseudo: CALL
function:
    003E: INC x2, 0xFFFFFFFE ; pseudo: INC
    0040: SW x3, 0(x2)
    0042: ADD x6, x7
    0044: POP x3, 0(x2) ; pseudo: POP
    0046: INC x2, 2 ; pseudo: INC
    0048: RET x1 ; pseudo: RET
end:
    004A: POP x1, 0(x4) ; pseudo: POP
    004C: SW x5, 0(x4)
    004E: NOP x0, x0 ; pseudo: NOP

; Data sections:
    ; Data section at 0x8000
    8000: .ascii "Hello World"
    800B: .word 0x3400
    800D: .word 0x7812
    800F: .word 0xBC56
    8011: .word 0x009A
    8013: .word 0x0000
    8015: .word 0x0000
    8017: .word 0x0000
    8019: .word 0x0000
    801B: .word 0x0000
    801D: .word 0x0000
    801F: .word 0x0000
    8021: .word 0x2A00
    8023: .word 0x6400
    8025: .word 0xFF00
    8027: .byte 0x00