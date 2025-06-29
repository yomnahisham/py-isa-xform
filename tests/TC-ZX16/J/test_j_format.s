# ZX16 J-type Instruction Format Test
# Tests jump format instructions

.org 0x0020

start:
    # J-type Jump and Link (opcode 110)
    JAL ra, function1       # Jump to function1, save return address in ra
    
    # Should return here after function1
    NOP
    
    # Test JAL with different registers
    JAL x1, function2       # Jump to function2, save return address in x1
    
    # Should return here after function2
    NOP
    
    # Test JAL to x0 (discards return address - like unconditional jump)
    JAL x0, function3       # Jump to function3, discard return address
    
    # This should not be reached
    EBREAK
    
after_function3:
    # Continue execution after function3
    JAL ra, nested_calls    # Test nested function calls
    
    # Final instructions
    NOP
    JMP program_end

function1:
    # Simple function that returns
    NOP
    ADDI x2, x2, 1          # Increment x2
    JALR x0, 0(ra)          # Return via ra

function2:
    # Function that uses saved return address in x1
    NOP
    ADDI x3, x3, 2          # Increment x3
    JALR x0, 0(x1)          # Return via x1

function3:
    # Function with no return (jumps elsewhere)
    NOP
    ADDI x4, x4, 3          # Increment x4
    JMP after_function3     # Jump to continue execution

nested_calls:
    # Test nested function calls
    JAL x5, inner_function  # Call inner function, save return in x5
    # Return point from inner_function
    ADDI x6, x6, 10         # Mark that we returned
    JALR x0, 0(ra)          # Return to caller

inner_function:
    # Deeply nested function
    NOP
    ADDI x7, x7, 5          # Increment x7
    JALR x0, 0(x5)          # Return via x5

# Test forward and backward jumps
backward_target:
    NOP
    JAL ra, program_end     # Jump forward to end

program_end:
    # Test backward jump
    LI x1, 1
    BEQ x1, x1, backward_target  # This creates a backward branch
    
final_end:
    NOP                     # Final instruction 