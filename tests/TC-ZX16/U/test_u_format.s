# ZX16 U-type Instruction Format Test
# Tests upper immediate format instructions

.org 0x0020

start:
    # U-type Upper Immediate instructions (opcode 111)
    
    # LUI - Load Upper Immediate (shifts immediate left by 9 bits)
    LUI x1, 0x01            # x1 = 0x01 << 9 = 0x0200
    LUI x2, 0x02            # x2 = 0x02 << 9 = 0x0400
    LUI x3, 0x7F            # x3 = 0x7F << 9 = 0xFE00 (max 7-bit value)
    LUI x4, 0x00            # x4 = 0x00 << 9 = 0x0000
    
    # AUIPC - Add Upper Immediate to PC
    AUIPC x5, 0x01          # x5 = PC + (0x01 << 9)
    AUIPC x6, 0x02          # x6 = PC + (0x02 << 9)
    AUIPC x7, 0x00          # x7 = PC + (0x00 << 9) = PC
    
    # Test with all registers using ABI names
    LUI t0, 0x10            # Load 0x2000 into t0 (x0)
    LUI ra, 0x20            # Load 0x4000 into ra (x1)
    LUI sp, 0x30            # Load 0x6000 into sp (x2)
    LUI s0, 0x40            # Load 0x8000 into s0 (x3)
    LUI s1, 0x50            # Load 0xA000 into s1 (x4)
    LUI t1, 0x60            # Load 0xC000 into t1 (x5)
    LUI a0, 0x70            # Load 0xE000 into a0 (x6)
    LUI a1, 0x7F            # Load 0xFE00 into a1 (x7)
    
    # Test AUIPC with different registers
    AUIPC t0, 0x01          # t0 = PC + 0x200
    AUIPC ra, 0x02          # ra = PC + 0x400
    AUIPC sp, 0x03          # sp = PC + 0x600
    
    # Combine LUI and ORI to create 16-bit constants
    LUI x1, 0x12            # x1 = 0x2400
    ORI x1, x1, 0x34        # x1 = 0x2400 | 0x34 = 0x2434
    
    LUI x2, 0x56            # x2 = 0xAC00  
    ORI x2, x2, 0x78        # x2 = 0xAC00 | 0x78 = 0xAC78
    
    # Test AUIPC for position-independent addressing
data_location:
    AUIPC x3, 0x00          # x3 = current PC (points to this instruction)
    ADDI x3, x3, 16         # x3 points 16 bytes ahead
    LW x4, 0(x3)            # Load word from calculated address
    
    # Test maximum and minimum values
    LUI x5, 0x7F            # Maximum 7-bit immediate
    AUIPC x6, 0x7F          # Maximum with PC addition
    
    LUI x7, 0x00            # Minimum immediate (zero)
    AUIPC x1, 0x00          # Zero addition to PC
    
    # Create large addresses using AUIPC
    AUIPC x2, 0x3E          # Create address in upper memory region
    ADDI x2, x2, 0x00       # Fine-tune the address
    
end:
    NOP

# Data section for testing
.org 0x0100
test_data:
    .word 0x1234
    .word 0x5678
    .word 0xABCD
    .word 0xEF00 