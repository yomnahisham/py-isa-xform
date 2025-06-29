# ZX16 R1-type Instruction Format Test
# Tests single register format instructions

.org 0x0020

start:
    # R1-type instructions (opcode 000)
    NOP                     # No operation - encoding: 000_0000_000_000000
    EBREAK                  # Environment break - encoding: 000_0001_000_000000
    
    # More NOPs to test consecutive handling
    NOP
    NOP
    NOP
    
end:
    # End marker
    NOP 