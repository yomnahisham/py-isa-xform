# Test file for ASCII string detection
.org 0x100

# Some instructions
li16 x0, 0x12
li16 x1, 0x34
add x2, x1

# Data section with ASCII strings
.data
.org 0x8000
.asciiz "Hello World"
.asciiz "Test String"
.asciiz "Another string with spaces"
.word 0x34
.asciiz "End of strings" 