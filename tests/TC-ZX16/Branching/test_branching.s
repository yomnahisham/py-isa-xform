# ZX16 Branching Test Case
# Tests branching instructions: BEQ, BNE, BZ, BNZ, J

    .text
    .globl main

main:
    # Initialize registers
    LI a0, 10          # a0 = 10
    LI a1, 10          # a1 = 10
    LI t1, 5           # t1 = 5 (using t1 instead of a2)
    
    # Test BEQ (Branch if Equal)
    BEQ a0, a1, equal_test  # Should branch since a0 == a1
    
    # This should not execute
    LI a0, 50          # This should be skipped (changed from 999)
    
equal_test:
    # Test BNE (Branch if Not Equal)
    BNE a0, t1, not_equal_test  # Should branch since a0 != t1
    
    # This should not execute
    LI a0, 40          # This should be skipped (changed from 888)
    
not_equal_test:
    # Test BZ (Branch if Zero)
    CLR s1             # s1 = 0 (using s1 instead of a3)
    BZ s1, zero_test   # Should branch since s1 == 0
    
    # This should not execute
    LI a0, 30          # This should be skipped (changed from 777)
    
zero_test:
    # Test BNZ (Branch if Not Zero)
    LI s1, 1           # s1 = 1
    BNZ s1, not_zero_test  # Should branch since s1 != 0
    
    # This should not execute
    LI a0, 20          # This should be skipped (changed from 666)
    
not_zero_test:
    # Test unconditional jump
    J final_test       # Unconditional jump
    
    # This should not execute
    LI a0, 10          # This should be skipped (changed from 555)
    
final_test:
    # Set final result
    LI a0, 42          # Final result: 42
    
    # Exit
    ECALL 0x3FF        # Exit with code 42 