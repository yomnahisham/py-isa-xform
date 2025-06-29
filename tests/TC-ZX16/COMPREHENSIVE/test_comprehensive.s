# ZX16 Comprehensive ISA Test
# Tests all instruction format types together with ECALL and pseudo-instructions
# This is a complete test of the ZX16 16-bit RISC-V inspired ISA

.org 0x0020

# === Program Entry Point ===
main:
    # Initialize stack pointer to ZX16 standard location
    LI16 sp, 0xEFFE         # Load 16-bit immediate: sp = 0xEFFE
    
    # === R1-type Instructions Test ===
    NOP                     # No operation
    
    # === I9-type Instructions Test ===
    LI x1, 42               # Load immediate: x1 = 42
    LI x2, -10              # Load immediate: x2 = -10  
    LI x3, 255              # Load immediate: x3 = 255 (max 9-bit)
    LI x4, -256             # Load immediate: x4 = -256 (min 9-bit)
    
    # === R3-type Instructions Test ===
    ADD x5, x1, x2          # x5 = x1 + x2 = 42 + (-10) = 32
    SUB x6, x1, x2          # x6 = x1 - x2 = 42 - (-10) = 52
    AND x7, x1, x3          # x7 = x1 & x3 = 42 & 255 = 42
    OR  t0, x2, x3          # t0 = x2 | x3 = -10 | 255 
    XOR t1, x1, x4          # t1 = x1 ^ x4 = 42 ^ -256
    
    # Shift operations
    LI x1, 8                # Load 8 for shift tests
    LI x2, 2                # Shift amount
    SLL a0, x1, x2          # a0 = 8 << 2 = 32
    SRL a1, a0, x2          # a1 = 32 >> 2 = 8
    SRA s0, x4, x2          # s0 = -256 >>> 2 (arithmetic shift)
    
    # === I6-type Instructions Test ===
    ADDI x1, x1, 15         # x1 = x1 + 15
    ANDI x2, x3, 31         # x2 = x3 & 31
    ORI  x3, x2, 8          # x3 = x2 | 8  
    XORI x4, x1, 7          # x4 = x1 ^ 7
    
    # Shift immediate operations
    SLLI x5, x1, 3          # x5 = x1 << 3
    SRLI x6, x5, 2          # x6 = x5 >> 2
    SRAI x7, x4, 1          # x7 = x4 >>> 1
    
    # === U-type Instructions Test ===
    LUI s1, 0x12            # s1 = 0x12 << 9 = 0x2400
    AUIPC ra, 0x01          # ra = PC + (0x01 << 9)
    
    # Combine for 16-bit constants
    LUI t0, 0x34            # t0 = 0x6800
    ORI t0, t0, 0x56        # t0 = 0x6800 | 0x56 = 0x6856
    
    # === Memory Operations (I6-type) ===
    # Set up memory base
    LUI s0, 0x20            # s0 = 0x4000 (data area)
    
    # Store operations
    SW x1, 0(s0)            # Store x1 at s0+0
    SW x2, 2(s0)            # Store x2 at s0+2  
    SB x3, 4(s0)            # Store x3 low byte at s0+4
    SB x4, 5(s0)            # Store x4 low byte at s0+5
    
    # Load operations
    LW t0, 0(s0)            # Load word from s0+0
    LW t1, 2(s0)            # Load word from s0+2
    LB a0, 4(s0)            # Load byte from s0+4 (sign-extended)
    LB a1, 5(s0)            # Load byte from s0+5 (sign-extended)
    
    # === Pseudo-instructions Test ===
    MOV x1, x2              # Move x2 to x1
    CLR x3                  # Clear x3 (set to 0)
    NOT x4, x5              # Bitwise NOT of x5, store in x4
    NEG x6, x7              # Negate x7, store in x6
    INC x1                  # Increment x1
    DEC x2                  # Decrement x2
    
    # === J-type Instructions Test ===
    JAL ra, subroutine      # Call subroutine
    
    # Return point from subroutine
    NOP
    
    # === B-type Instructions Test ===
    LI x1, 10
    LI x2, 20
    LI x3, 10               # Same as x1
    
branch_tests:
    BEQ x1, x3, equal_path      # Should take (10 == 10)
    EBREAK                      # Should not reach here
    
equal_path:
    BNE x1, x2, not_equal_path  # Should take (10 != 20)
    EBREAK                      # Should not reach here
    
not_equal_path:
    BLT x1, x2, less_path       # Should take (10 < 20)
    EBREAK                      # Should not reach here
    
less_path:
    BGE x2, x1, greater_path    # Should take (20 >= 10)
    EBREAK                      # Should not reach here
    
greater_path:
    # Unsigned comparisons
    BLTU x1, x2, less_unsigned  # Should take
    EBREAK                      # Should not reach here
    
less_unsigned:
    BGEU x2, x1, system_calls   # Should take
    EBREAK                      # Should not reach here
    
    # === System Calls (ECALL) Test ===
system_calls:
    # Test various ECALL instructions with different syscall numbers
    ECALL 0x000             # Print character syscall
    ECALL 0x001             # Read character syscall
    ECALL 0x002             # Print string syscall
    ECALL 0x003             # Print decimal syscall
    
    # Test with larger syscall numbers
    ECALL 0x100             # Custom syscall
    ECALL 0x200             # Another custom syscall
    ECALL 0x3FF             # Maximum 10-bit syscall number
    
    # === Advanced Features Test ===
    # Test load address pseudo-instruction
    LA t0, data_section     # Load address of data_section
    
    # Test 16-bit immediate loading
    LI16 t1, 0x1234         # Load full 16-bit immediate
    LI16 x6, 0xABCD         # Load another 16-bit immediate
    
    # Test function calls with pseudo-instructions
    CALL math_function      # Call function (pseudo for JAL ra, target)
    
    # Return point
    NOP
    
    # === Jump Instructions ===
    JMP program_end         # Unconditional jump to end
    
    EBREAK                  # Should not reach here

# === Subroutines ===
subroutine:
    # Simple subroutine that modifies registers
    ADDI a0, a0, 1          # Increment a0
    ADDI a1, a1, 2          # Increment a1
    RET                     # Return (pseudo for JALR x0, 0(ra))

math_function:
    # Function that performs some calculations
    ADD a0, x1, x2          # a0 = x1 + x2
    SUB a1, x2, x1          # a1 = x2 - x1
    AND t0, a0, a1          # t0 = a0 & a1
    OR  t1, a0, a1          # t1 = a0 | a1
    
    # Test nested calls
    JAL s1, helper_function # Call helper, save return in s1
    
    # Return from math_function
    RET

helper_function:
    # Deeply nested function
    XOR a0, a0, a1          # a0 = a0 ^ a1
    SLLI a0, a0, 1          # a0 = a0 << 1
    JALR x0, 0(s1)          # Return via s1

# === End of Program ===
program_end:
    # Final system call to exit
    LI a0, 0                # Exit code 0
    ECALL 0x3FF             # Exit program syscall
    
    # Should not reach here
    EBREAK

# === Data Section ===
.org 0x4000
data_section:
    .word 0x1234            # Test data
    .word 0x5678
    .word 0xABCD
    .word 0xEF00
    
string_data:
    .string "Hello ZX16!"   # Test string
    
test_bytes:
    .byte 0x12, 0x34, 0x56, 0x78
    
# === Constants ===
.equ STACK_TOP, 0xEFFE
.equ DATA_BASE, 0x4000
.equ MAX_SYSCALL, 0x3FF 