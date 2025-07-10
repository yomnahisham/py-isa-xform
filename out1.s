; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: LA x0, 0x40 ; pseudo: LA ; words
    0024: INC x7, 51 ; pseudo: INC
    0026: SW x7, 0(x0)
    0028: POP x1, 0(x0) ; pseudo: POP
    002A: ECALL 10

; Data sections:
    ; Data section at 0x0040
    0040: .word 0xABCD
    0042: .word 0x1111
    0044: .ascii "Hello, World!\n"