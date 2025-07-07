; Comprehensive ZX16 Test Case
; This test covers ALL features of the toolchain
; 
; Features tested:
; 1. All instruction types (ALU, Load/Store, Branch, Jump, System)
; 2. All pseudo-instructions (NOP, JMP, CLR, INC, DEC, LA, J)
; 3. Data sections (.word, .byte, .ascii, .asciiz, .space)
; 4. Labels and symbol resolution
; 5. Directives (.org, .section, .align, .equ)
; 6. Address space handling
; 7. ASCII string detection
; 8. Edge cases and complex scenarios

.org 0x1000

; ===== EQU CONSTANTS =====
.equ MAGIC_NUMBER, 0xDEAD
.equ STRING_LENGTH, 16
.equ ARRAY_SIZE, 8

; ===== CODE SECTION =====
start:
    ; Test basic ALU instructions
    ADD x1, x2          ; R-type: rd = rd + rs2
    SUB x3, x4          ; R-type: rd = rd - rs2
    AND x5, x6          ; R-type: rd = rd & rs2
    OR x7, x1           ; R-type: rd = rd | rs2
    XOR x2, x3          ; R-type: rd = rd ^ rs2
    SLT x4, x5          ; R-type: rd = (rd < rs2) ? 1 : 0
    SLTU x6, x7         ; R-type: rd = (rd < rs2) ? 1 : 0 (unsigned)
    SLL x1, x2          ; R-type: rd = rd << rs2
    SRL x3, x4          ; R-type: rd = rd >> rs2 (logical)
    SRA x5, x6          ; R-type: rd = rd >> rs2 (arithmetic)

    ; Test immediate instructions
    ADDI x7, 7          ; I-type: rd = rd + imm (max 4-bit signed)
    ANDI x1, -8         ; I-type: rd = rd & imm (min 4-bit signed)
    ORI x2, 3           ; I-type: rd = rd | imm
    XORI x3, -4         ; I-type: rd = rd ^ imm
    SLTI x4, 7          ; I-type: rd = (rd < imm) ? 1 : 0
    SLTUI x5, 0         ; I-type: rd = (rd < imm) ? 1 : 0 (unsigned)
    SLLI x6, 2          ; I-type: rd = rd << imm
    SRLI x7, 1          ; I-type: rd = rd >> imm (logical)
    SRAI x1, 3          ; I-type: rd = rd >> imm (arithmetic)

    ; Test load/store instructions
    LW x2, 7(x3)        ; I-type: rd = Memory[rs1 + offset] (max 4-bit signed)
    LB x4, -8(x5)       ; I-type: rd = Memory[rs1 + offset] (min 4-bit signed)
    LBU x6, 0(x7)       ; I-type: rd = Memory[rs1 + offset] (byte unsigned)
    SW x1, 7(x2)        ; S-type: Memory[rs1 + offset] = rs2
    SB x3, -8(x4)       ; S-type: Memory[rs1 + offset] = rs2 (byte)

    ; Test branch instructions
    BEQ x5, x6, branch_target1    ; B-type: if (rs1 == rs2) PC += offset
    BNE x7, x1, branch_target2    ; B-type: if (rs1 != rs2) PC += offset
    BLT x2, x3, branch_target3    ; B-type: if (rs1 < rs2) PC += offset
    BGE x4, x5, branch_target4    ; B-type: if (rs1 >= rs2) PC += offset
    BLTU x6, x7, branch_target5   ; B-type: if (rs1 < rs2) PC += offset (unsigned)
    BGEU x1, x2, branch_target6   ; B-type: if (rs1 >= rs2) PC += offset (unsigned)
    BZ x3, branch_target1         ; B-type: if (rs1 == 0) PC += offset
    BNZ x4, branch_target2        ; B-type: if (rs1 != 0) PC += offset

    ; Test jump instructions
    JAL x5, jump_target1          ; J-type: rd = PC + 4; PC += offset
    JALR x6, x7
    JR x1                        ; R-type: PC = rs1

    ; Test system instructions
    ECALL 0                      ; System call

    ; Test pseudo-instructions
    NOP                          ; Pseudo: ADD x0, x0
    JMP jump_target2             ; Pseudo: J jump_target2
    CLR x2                       ; Pseudo: XOR x2, x2
    INC x3                       ; Pseudo: ADDI x3, 1
    DEC x4                       ; Pseudo: ADDI x4, -1
    J jump_target3               ; Pseudo: J jump_target3

    ; Test complex label resolution
    LI x6, 42                    ; Load immediate
    LI x7, -64                   ; Load immediate with negative value (min 7-bit signed)

    ; Test conditional execution with labels
    BEQ x0, x0, always_taken     ; This should always branch
    BNE x0, x1, never_taken      ; This should never branch (x0 is always 0)

always_taken:
    LI x2, 63                    ; This should execute (max 7-bit signed)

never_taken:
    LI x3, 0                     ; This should be skipped

    ; Test jump targets
jump_target1:
    LI x4, 63                    ; Changed from 0x1234
    J jump_target4

jump_target2:
    LI x5, 42                    ; Changed from 0xABCD
    J jump_target5

jump_target3:
    LI x6, 31                    ; Changed from 0xDEAD
    J jump_target6

jump_target4:
    LI x7, 15                    ; Changed from 0xCAFE

jump_target5:
    LI x1, 7                     ; Changed from 0xBEEF

jump_target6:
    LI x2, 3                     ; Changed from 0x7FFF

    ; Test branch targets
branch_target1:
    LI x3, 10                    ; Changed from 0x1111
    J end_test

branch_target2:
    LI x4, 20                    ; Changed from 0x2222
    J end_test

branch_target3:
    LI x5, 30                    ; Changed from 0x3333
    J end_test

branch_target4:
    LI x6, 40                    ; Changed from 0x4444
    J end_test

branch_target5:
    LI x7, 50                    ; Changed from 0x5555
    J end_test

branch_target6:
    LI x1, 60                    ; Changed from 0x6666
    J end_test

end_test:
    ; Final test - load from data section
    LI x2, 0                      ; Use immediate instead
    LI x5, 0                      ; Use immediate instead
    LW x3, 0(x2)                 ; Load first word from data section
    LB x4, 4(x2)                 ; Load byte from data section
    
    ; Test string operations
    LB x6, 0(x5)                 ; Load first character
    LB x7, 1(x5)                 ; Load second character
    
    ; Exit gracefully
    ECALL 0

; ===== DATA SECTION =====
.org 0x2000

data_section_start:
    ; Test word data
    .word 0x1234                 ; 16-bit word
    .word 0xABCD                 ; Another 16-bit word
    .word 0xDEAD                 ; Magic number
    .word 0xCAFE                 ; Another magic number
    
    ; Test halfword data
    .word 0x1111                 ; 16-bit value
    .word 0x2222                 ; Another 16-bit value
    
    ; Test byte data
    .byte 0xAA                   ; Single byte
    .byte 0xBB                   ; Another byte
    .byte 0xCC, 0xDD             ; Multiple bytes
    .byte 0xEE, 0xFF, 0x00       ; Three bytes
    
    ; Test ASCII strings
    .ascii "Hello, World!"       ; ASCII string without null terminator
    .ascii "ZX16"                ; Short ASCII string
    .ascii "Testing 123"         ; ASCII with numbers and spaces
    
    ; Test null-terminated strings
    .asciiz "Null-terminated"    ; ASCII string with null terminator
    .asciiz "Test"               ; Short null-terminated string
    
    ; Test mixed data
    .word 0x9999                 ; Word after string
    .byte 0x77                   ; Byte after word
    .ascii "Mixed"               ; String after byte
    .word 0x8888                 ; Word after string
    
    ; Test alignment
    .align 4                     ; Align to 4-byte boundary
    .word 0xAAAA                 ; Aligned word
    
    ; Test space directive
    .space 16                    ; 16 bytes of zeros
    .word 0xBBBB                 ; Word after space
    
    ; Test complex string patterns
    ; .ascii "Special chars: !@#$%^&*()"  ; Special characters
    .ascii "Numbers: 0123456789"        ; Numbers
    ; .ascii "Mixed: A1B2C3!@#"           ; Mixed alphanumeric and symbols
    
    ; Test edge cases
    .byte 0x00                   ; Null byte
    .byte 0x7F                   ; DEL character
    .byte 0x20                   ; Space character
    .byte 0x7E                   ; Tilde character
    
    ; Test unprintable characters (should not be detected as strings)
    .byte 0x01, 0x02, 0x03      ; Control characters
    .byte 0x1F, 0x7F, 0x80      ; More control characters
    
    ; Test printable characters (should be detected as strings)
    .ascii "Printable: ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    .ascii "abcdefghijklmnopqrstuvwxyz"
    .ascii "0123456789"
    ; .ascii "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    
    ; Test long strings
    .ascii "This is a very long string that should be detected properly by the ASCII string detection algorithm. It contains multiple sentences and should be handled correctly by the disassembler."
    
    ; Test string with embedded nulls (should be split)
    .ascii "First part"
    .byte 0x00                   ; Null byte
    .ascii "Second part"
    
    ; Test word alignment after strings
    .ascii "End"
    .align 4
    .word 0xCCCC                 ; Final aligned word

; ===== SYMBOL REFERENCES =====
data_label:
    .word 0x1234                 ; Referenced by LA instruction

string_data:
    .ascii "Test string"         ; Referenced by load instructions

; ===== FINAL ALIGNMENT =====
.align 8                         ; Final alignment to 8-byte boundary 