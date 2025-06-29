# ZX16 I9-type Instruction Format Test
# Tests 9-bit immediate format instructions

.org 0x0020

start:
    # I9-type Load Immediate (opcode 100)
    LI x1, 127              # Load immediate: x1 = sign_extend(127)
    LI x2, -128             # Load immediate: x2 = sign_extend(-128)
    LI x3, 255              # Load immediate: x3 = sign_extend(255)
    LI x4, 0                # Load immediate: x4 = 0
    LI x5, 42               # Load immediate: x5 = 42
    
    # Test with different registers and ABI names
    LI t0, 100              # Load to x0 (t0)
    LI ra, 200              # Load to x1 (ra)
    LI sp, 300              # Load to x2 (sp)
    LI s0, 400              # Load to x3 (s0/fp)
    LI s1, 500              # Load to x4 (s1)
    LI t1, 600              # Load to x5 (t1)
    LI a0, 700              # Load to x6 (a0)
    LI a1, 800              # Load to x7 (a1)
    
    # Test boundary values (9-bit signed: -256 to +255)
    LI x6, 255              # Maximum positive
    LI x7, -256             # Maximum negative
    
    # System calls using ECALL with 9-bit immediate
    ECALL 0x000             # Print character syscall
    ECALL 0x001             # Read character syscall
    ECALL 0x002             # Print string syscall
    ECALL 0x003             # Print decimal syscall
    ECALL 0x3FF             # Exit program syscall (max value)
    
    # More ECALL variations
    ECALL 0x100             # Custom syscall
    ECALL 0x200             # Another custom syscall
    
end:
    NOP 