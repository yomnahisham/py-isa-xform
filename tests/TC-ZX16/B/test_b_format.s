# ZX16 B-type Instruction Format Test
# Tests branch format instructions

.org 0x0020

start:
    # Initialize some test values
    LI x1, 10
    LI x2, 20
    LI x3, 10               # Same as x1 for equality tests
    LI x4, 5                # Less than x1
    
test_branches:
    # B-type branch instructions (opcode 101)
    BEQ x1, x3, equal_label     # Branch if x1 == x3 (should take)
    BNE x1, x2, not_equal      # Branch if x1 != x2 (should take)
    
skip1:
    BLT x4, x1, less_than      # Branch if x4 < x1 (should take)
    BGE x2, x1, greater_eq     # Branch if x2 >= x1 (should take)
    
skip2:
    # Unsigned comparisons
    BLTU x4, x1, less_unsigned  # Branch if x4 < x1 unsigned (should take)
    BGEU x2, x1, greater_eq_u   # Branch if x2 >= x1 unsigned (should take)
    
skip3:
    # Test with negative values
    LI x5, -5
    LI x6, -10
    BLT x6, x5, neg_less       # Branch if -10 < -5 (should take)
    BGE x5, x6, neg_greater    # Branch if -5 >= -10 (should take)
    
    # Test boundary conditions
    BEQ x1, x1, self_equal     # Branch to self (should take)
    BNE x1, x1, should_not_take # This should not take
    
    JMP end                    # Jump to end

equal_label:
    # Arrived here via BEQ
    NOP
    JMP skip1

not_equal:
    # Arrived here via BNE
    NOP
    JMP skip2

less_than:
    # Arrived here via BLT
    NOP
    JMP skip2

greater_eq:
    # Arrived here via BGE
    NOP
    JMP skip3

less_unsigned:
    # Arrived here via BLTU
    NOP
    JMP skip3

greater_eq_u:
    # Arrived here via BGEU
    NOP
    JMP end

neg_less:
    # Arrived here via BLT with negatives
    NOP
    JMP end

neg_greater:
    # Arrived here via BGE with negatives
    NOP
    JMP end

self_equal:
    # Self-equality test
    NOP
    JMP end

should_not_take:
    # This should never be reached
    EBREAK                     # Trigger breakpoint if reached

end:
    NOP 