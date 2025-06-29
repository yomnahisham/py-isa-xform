# ZX16 R2-type Instruction Format Test
# Tests two register format instructions
# Note: Currently no instructions in ZX16 use R2-type format

.org 0x0020

start:
    # R2-type format is defined but no instructions currently use it
    # This test serves as a placeholder for future R2-type instructions
    # Format: opcode(2:0) + funct(6:3) + rd(9:7) + rs(12:10) + unused(15:13)
    
    # For now, use instructions that approximate R2-type behavior
    # These are actually other formats but test two-register operations
    
    # Pseudo R2-type operations using available instructions
    NOP                     # Placeholder
    
    # Examples of what R2-type instructions might look like:
    # MOV rd, rs             # Move rs to rd (could be R2-type)
    # NEG rd, rs             # Negate rs, store in rd (could be R2-type)
    # NOT rd, rs             # Bitwise NOT of rs, store in rd (could be R2-type)
    
    # Using pseudo-instructions that expand to available formats
    MOV x1, x2              # Move x2 to x1 (expands to ADD x1, x2, x0)
    NEG x3, x4              # Negate x4, store in x3 (expands to SUB x3, x0, x4)
    NOT x5, x6              # Bitwise NOT x6, store in x5 (expands to XORI x5, x6, -1)
    CLR x7                  # Clear x7 (expands to XOR x7, x7, x7)
    
    # Test with ABI register names
    MOV ra, sp              # Move sp to ra
    NEG t0, t1              # Negate t1, store in t0
    NOT a0, a1              # Bitwise NOT a1, store in a0
    CLR s0                  # Clear s0
    
end:
    NOP

# Note: If true R2-type instructions are added to ZX16 in the future,
# this test should be updated with actual R2-type instruction examples. 