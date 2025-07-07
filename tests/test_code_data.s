.org 0x1000

start:
    LI x1, 5
    J start
 
data_section:
    .word 0x1234, 0xABCD
    .ascii "Hello" 