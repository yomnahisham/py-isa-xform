; Test case for enhanced label resolution
.org 0x20

main:
    LI x1, #5         
    LI x2, #10        
    ADD x3, x1, x2    
    BEQ x1, x2, end   
    JMP loop          

loop:
    ADD x1, x1, x2    
    BEQ x1, x2, end   
    JMP loop          

end:
    ADD x0, x0        

.data
.org 0x8000

message:
    .asciiz "Hello World"

value:
    .word 0x1234
