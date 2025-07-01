# --- Print integer 42 ---
ADDI x6, 42       # x6 (a0) = 0 + 42
ECALL 1           # ecall 1: print int

# --- Print string "Hello" ---
AUIPC x6, 0       # x6 = PC (current address)
ADDI  x6, msg # x6 = x6 + offset to msg
ECALL 2           # ecall 2: print string

# --- Exit ---
ECALL 3           # ecall 3: exit

# --- Data section ---
.data
msg: .ascii "Hello"
.byte 0           # zero-terminated
