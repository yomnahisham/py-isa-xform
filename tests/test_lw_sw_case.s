# ZX16 Simple LW/SW Test with Data Section
# Tests basic load/store operations with predefined data

.org 32                    # Start at code section

main:    
    # Test 1: Load from data section and store to new location
    LI x3, test_data      # Load address of test data
    LW x1, 0(x3)          # Load first word from test_data
    
    # Store the loaded value to a different location
    LI x4, buffer         # Load buffer address
    SW x1, 0(x4)          # Store to buffer
    
    # Test 2: Verify the store operation
    LW x5, 0(x4)          # Load back from buffer
    SUB x6, x5, x1        # Compare values (should be 0)
    BNZ x6, test_fail     # Branch if not equal
    
    # Test 3: Load and manipulate string data
    LI x3, message        # Load message address
    LW x1, 0(x3)          # Load first two characters
    LW x2, 2(x3)          # Load next two characters
    
    # Store string data to buffer with offset
    LI x4, buffer         # Buffer address
    SW x1, 2(x4)          # Store at buffer + 2
    SW x2, 4(x4)          # Store at buffer + 4
    
    # Verify string data transfer
    LW x5, 2(x4)          # Load back first part
    SUB x6, x5, x1        # Compare
    BNZ x6, test_fail
    
    LW x5, 4(x4)          # Load back second part
    SUB x6, x5, x2        # Compare
    BNZ x6, test_fail
    
    # All tests passed
    LI x0, 0              # Success code
    J test_end

test_fail:
    LI x0, 1              # Failure code

test_end:
    # Print results and exit
    MV x6, x0             # Move result to a0
    ECALL 0x008           # Dump registers
    ECALL 0x00A           # Exit

# Data section
.org 32768              # Data section start

test_data:
    .word 0x1111         # Test value 1
    .word 0xABCD         # Test value 2
    .word 0x5678         # Test value 3

message:
    .ascii "Hi"          # Simple 2-character message
    .word 0x0000         # Null terminator as word

buffer:
    .word 0x0000         # Buffer space
    .word 0x0000
    .word 0x0000
    .word 0x0000 