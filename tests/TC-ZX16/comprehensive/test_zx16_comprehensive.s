; Comprehensive ZX16 test with labels, offsets, and immediates
.org 0x100

start:
    LI a0, 10          ; Load immediate 10
    LI a1, -5          ; Load immediate -5
    LI a0, 63          ; Load immediate max positive (63)
    LI a1, -64         ; Load immediate min negative (-64)
    
    ; Test labels and offsets
    JAL ra, func1      ; Jump and link to function
    JAL ra, func2      ; Jump and link to another function
    
    ; Test conditional branches with labels
    BEQ a0, a1, start  ; Branch if equal (should not branch)
    BNE a0, a1, skip1  ; Branch if not equal (should branch)
    J skip2            ; Unconditional jump
skip1:
    ADD a0, a1         ; This should be skipped
skip2:
    ; Test memory operations with offsets
    LW a0, 4(a1)       ; Load word with offset
    SW a1, 8(a0)       ; Store word with offset
    
    ; Test immediate arithmetic
    ADDI a0, 20        ; Add immediate 20
    ADDI a1, -10       ; Add immediate -10
    SLTI a0, 50        ; Set if less than immediate
    
    ; Test logical operations with immediates
    ANDI a0, 0x0F      ; AND immediate
    ORI a1, 0x3F       ; OR immediate (was 0xF0, now 0x3F)
    XORI a0, 0x3F      ; XOR immediate (was 0xFF, now 0x3F)
    
    ; Test shifts with immediates
    SLLI a0, 2         ; Shift left logical immediate
    SRLI a1, 1         ; Shift right logical immediate
    SRAI a0, 3         ; Shift right arithmetic immediate
    
    ; Test upper immediates
    LUI a0, 63         ; Load upper immediate
    AUIPC a1, 31       ; Add upper immediate to PC
    
    ; Test system calls
    ECALL 0x3FF        ; Exit program
    
    ; This should never be reached
    ADD a0, a1

; Function definitions
func1:
    ADD a0, a1         ; Simple function 1
    JR ra              ; Return
    
func2:
    SUB a0, a1         ; Simple function 2
    ADDI a0, 5         ; Add 5 to result
    JR ra              ; Return

; Data section
data_start:
    .word 0x1234       ; Some data
    .word 0x5678       ; More data
    .word 0x9ABC       ; Even more data
    .word 0xDEF0       ; Final data 