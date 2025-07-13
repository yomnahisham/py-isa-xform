; Test modular register parsing with different naming schemes
; This should work with any ISA regardless of register naming

; RV32I-style (x0, x1, x2)
addi x1, x0, 42
add x2, x1, x0

; R-style (r0, r1, r2) - should work if ISA supports it
; addi r1, r0, 42
; add r2, r1, r0

; Numeric style (0, 1, 2) - should work if ISA supports it
; addi 1, 0, 42
; add 2, 1, 0

; Mixed style - should work with any combination
; addi x1, 0, 42
; add r2, x1, 0 