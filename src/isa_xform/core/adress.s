; Disassembly of ZX16 v1.1
; Word size: 16 bits
; Endianness: little

main:
    0020: LA x5, 0xFA00 ; pseudo: LA ; label
    0024: LB x0, 0(x5)
    0026: ECALL 10

; Data sections:
    ; Data section at 0x8000
    8000: .word 0x1111