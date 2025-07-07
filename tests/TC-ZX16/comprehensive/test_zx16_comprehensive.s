# Comprehensive ZX16 Test Program
# Tests labels, immediates, and various instruction types

.org 0x100

start:
    # Load immediate values
    li16 x0, 0x1234
    li16 x1, 0x5678
    li16 x2, 0x9ABC
    
    # Arithmetic operations
    add x3, x0, x1
    sub x4, x2, x0
    slt x5, x1, x2
    
    # Logical operations
    and x6, x0, x1
    or x7, x1, x2
    xor x0, x0, x2  # Reuse x0
    
    # Shifts
    sll x1, x0, 2   # Reuse x1
    srl x2, x1, 1   # Reuse x2
    sra x3, x2, 3   # Reuse x3
    
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
    add x5, x0, x1
    sub x6, x2, x3
    ret
    
func2:
    # Function 2 - logical operations
    and x7, x4, x5
    or x0, x6, x7   # Reuse x0
    xor x1, x0, x2  # Reuse x1
    ret

# Data section
.data
.org 0x8000
.word 0x1234
.word 0x5678
.word 0x9ABC 