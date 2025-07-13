; Clean LA test - no data sections
.org 0x1000

start:
    LA x1, 0x1234
    LA x2, 0x5678
    NOP 