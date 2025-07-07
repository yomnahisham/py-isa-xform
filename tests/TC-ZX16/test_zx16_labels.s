# ZX16 Label Definition Test File
# Demonstrates all label types and features

# Global labels (visible across all files)
main:
    LI x6, 10
    CALL my_function
    RET

# Local labels (file scope, start with dot)
.local_label:
    ADD x1, x2
    BNZ x1, .local_label

# Loop labels (common pattern)
loop:
    ADD x1, x2
    BNZ x1, loop
    RET

# Section labels
data_section:
    .word 0x1234
    .word 0x5678

# Data labels with allocation
buffer: .space 64
message: .ascii "Hello, World!"

# Function labels
my_function:
    PUSH x3
    ADD x6, x7
    POP x3
    RET

# Label arithmetic examples (commented out - not supported in current assembler)
start_label:
    NOP
end_label:
    # .word end_label - start_label  # Label arithmetic - not supported yet
    .word 0x0002  # Manual calculation for now

# Bitfield extraction examples (commented out - not supported in current assembler)
high_bits:
    # .word label[15:9]   # Upper 7 bits - not supported yet
    .word 0x0000  # Placeholder
low_bits:
    # .word label[8:0]    # Lower 9 bits - not supported yet
    .word 0x0000  # Placeholder

# Complex expressions (commented out - not supported in current assembler)
complex_expr:
    # .word (buffer + 4)  # Address calculation - not supported yet
    # .word ~0x0F         # Bitwise NOT - not supported yet
    # .word (value << 2) | 0x03  # Shift and OR - not supported yet
    .word 0x0000  # Placeholder

# Forward references (labels used before defined)
    BZ x1, forward_label
    J backward_label
backward_label:
    NOP
forward_label:
    NOP

# Section switching with labels
.text
code_section:
    LI x1, 42
    J data_section2

.data
data_section2:
    .word 0xDEAD
    .word 0xBEEF

# Local label with scope
.scope1:
    ADD x1, x2
    BNZ x1, .scope1    # References local label
    J main             # References global label 