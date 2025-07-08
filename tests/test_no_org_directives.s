# Test demonstrating that users can write assembly without .org directives
# The assembler should automatically use the ISA's default addresses

.data
# Data section should start at 0x8000 (ZX16 default)
data_label: .word 0x1234, 0x5678
string_data: .ascii "Hello, World!"
constant_data: .word 42

.text
# Code section should start at 0x20 (ZX16 default)
start:
    # Load addresses of data labels
    la x0, data_label      # Should load 0x8000
    la x1, string_data     # Should load 0x8008 (after 2 words)
    la x2, constant_data   # Should load 0x8014 (after string)
    
    # Load the actual data
    lw x3, data_label      # Load 0x1234
    lw x4, data_label+2    # Load 0x5678
    
    # System call
    ecall 10 