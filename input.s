# ZX16 Store and Load Instructions Test Case
# Tests all store/load variants with various data patterns

.org 0x20                    # Start at code section

main:
    # Initialize stack pointer
    LI x2, 0xEFFE           # Set stack pointer to default value
    
    # Initialize base address for data storage
    LI x1, 0x8000           # Base address in data section
    
    
    # ===========================================
    # STORE BYTE (SB) INSTRUCTION TESTS
    # ===========================================
    
    # Test 1: Store positive byte value
    LI x3, 0x42             # Load test value (ASCII 'B')
    SB x3, 0(x1)            # Store byte at base address
    
    # Test 2: Store negative byte value (sign extension test)
    LI x3, 0xFF80           # Load -128 (sign extended)
    SB x3, 1(x1)            # Store at offset 1
    
    # Test 3: Store with positive offset
    LI x3, 0x7F             # Load +127
    SB x3, 5(x1)            # Store at offset 5
    
    # Test 4: Store with negative offset
    LI x3, 0x33             # Load test value
    ADDI x1, 10             # Advance base pointer
    SB x3, -3(x1)           # Store at negative offset (-3)
    ADDI x1, -10            # Restore base pointer
    
    
    # ===========================================
    # STORE WORD (SW) INSTRUCTION TESTS
    # ===========================================
    
    # Test 5: Store 16-bit word (little endian)
    LI x3, 0x1234           # Load test word
    SW x3, 10(x1)           # Store word at offset 10
                            # Memory layout: [0x34, 0x12] (little endian)
    
    # Test 6: Store maximum positive value
    LI x3, 0x7FFF           # Load max positive 16-bit value
    SW x3, 12(x1)           # Store at offset 12
    
    # Test 7: Store maximum negative value
    LI x3, 0x8000           # Load max negative 16-bit value
    SW x3, 14(x1)           # Store at offset 14
    
    
    # ===========================================
    # LOAD BYTE (LB) INSTRUCTION TESTS
    # ===========================================
    
    # Test 8: Load positive byte (no sign extension needed)
    LB x4, 0(x1)            # Load from base address
                            # Expected: x4 = 0x0042 (positive, no extension)
    
    # Test 9: Load negative byte (sign extension)
    LB x4, 1(x1)            # Load from offset 1
                            # Expected: x4 = 0xFF80 (sign extended to 16-bit)
    
    # Test 10: Load with positive offset
    LB x4, 5(x1)            # Load from offset 5
                            # Expected: x4 = 0x007F
    
    # Test 11: Load with negative offset
    ADDI x1, 10             # Advance base pointer
    LB x4, -3(x1)           # Load from negative offset
                            # Expected: x4 = 0x0033
    ADDI x1, -10            # Restore base pointer
    
    
    # ===========================================
    # LOAD BYTE UNSIGNED (LBU) INSTRUCTION TESTS
    # ===========================================
    
    # Test 12: Load byte unsigned (no sign extension)
    LBU x4, 1(x1)           # Load from offset 1
                            # Expected: x4 = 0x0080 (zero extended, not sign extended)
    
    # Test 13: Load high-value byte unsigned
    LI x3, 0xFF             # Load 255
    SB x3, 20(x1)           # Store at offset 20
    LBU x4, 20(x1)          # Load unsigned
                            # Expected: x4 = 0x00FF (zero extended)
    
    
    # ===========================================
    # LOAD WORD (LW) INSTRUCTION TESTS
    # ===========================================
    
    # Test 14: Load 16-bit word (little endian reconstruction)
    LW x4, 10(x1)           # Load word from offset 10
                            # Expected: x4 = 0x1234 (reconstructed from little endian)
    
    # Test 15: Load maximum positive word
    LW x4, 12(x1)           # Load from offset 12
                            # Expected: x4 = 0x7FFF
    
    # Test 16: Load maximum negative word
    LW x4, 14(x1)           # Load from offset 14
                            # Expected: x4 = 0x8000
    
    
    # ===========================================
    # BOUNDARY AND EDGE CASE TESTS
    # ===========================================
    
    # Test 17: Maximum positive offset (15 for 4-bit signed)
    LI x3, 0xAB             # Test value
    SB x3, 7(x1)            # Store at maximum positive offset
    LB x4, 7(x1)            # Load back
                            # Expected: x4 = 0xFFAB (sign extended)
    
    # Test 18: Maximum negative offset (-8 for 4-bit signed)
    ADDI x1, 8              # Advance base pointer
    LI x3, 0xCD             # Test value
    SB x3, -8(x1)           # Store at maximum negative offset
    LB x4, -8(x1)           # Load back
                            # Expected: x4 = 0xFFCD (sign extended)
    ADDI x1, -8             # Restore base pointer
    
    # Test 19: Word alignment test
    LI x3, 0xBEEF           # Test word
    SW x3, 16(x1)           # Store at even address (aligned)
    LW x4, 16(x1)           # Load back
                            # Expected: x4 = 0xBEEF
    
    
    # ===========================================
    # DATA VERIFICATION SECTION
    # ===========================================
    
    # Test 20: Verify byte-word interaction
    LI x3, 0x1122           # Store word
    SW x3, 30(x1)           # Store as word
    
    LBU x4, 30(x1)          # Load low byte unsigned
                            # Expected: x4 = 0x0022 (little endian low byte)
    
    LBU x5, 31(x1)          # Load high byte unsigned
                            # Expected: x5 = 0x0011 (little endian high byte)
    
    
    # ===========================================
    # PROGRAM TERMINATION
    # ===========================================
    
    # Exit program
    LI x6, 0                # Exit code 0
    ECALL 0x00A             # Exit system call
    
    
# ===========================================
# DATA SECTION (for reference)
# ===========================================
.org 0x8000
data_area:
    .space 64               # Reserve 64 bytes for testing
