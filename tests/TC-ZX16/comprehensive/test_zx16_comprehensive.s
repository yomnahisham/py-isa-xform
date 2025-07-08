# Comprehensive ZX16 Test Program
# Tests labels, immediates, and various instruction types

.org 0x100

start:
    # Load immediate values
    li16 x0, 0x12
    li16 x1, 0x34
    li16 x2, 0x30
    
    # Arithmetic operations
    add x3, x1
    sub x4, x0
    slt x5, x2
    
    # Logical operations
    and x6, x1
    or x7, x2
    xor x0, x2  # Reuse x0
    
    # Shifts
    slli x1, 2   # Reuse x1
    srli x2, 1   # Reuse x2
    srai x3, 3   # Reuse x3
    
    # Branch to function
    jal x1, func1
    
    # Load/store operations
    lw x4, 4(x0)  # Use small offset
    sw x3, 7(x0)  # Use max positive offset
    
    # Jump to second function
    jal x1, func2
    
    # Exit
    ecall 0x3FF

func1:
    # Function 1 - simple arithmetic
    add x5, x1
    sub x6, x3
    ret
    
func2:
    # Function 2 - logical operations
    and x7, x5
    or x0, x7   # Reuse x0
    xor x1, x2  # Reuse x1
    ret

# Data section
.data
.org 0x8000
.word 0x12
.word 0x34
.word 0x30 