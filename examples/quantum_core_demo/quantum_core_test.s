# QuantumCore ISA Test Program
# Tests arithmetic, control flow, memory operations, and quantum features

.org 0x1000

# Data section
.data:
    .word 0x12345678, 0xABCDEF01, 0xDEADBEEF
    .ascii "Hello, Quantum World!"

.text:
main:
    # Initialize registers
    LI r10, #42          # Load immediate
    LI r11, #10          # Load immediate
    LI r12, #0x1000      # Load address for data access
    
    # Test arithmetic operations
    ADD r13, r10, r11    # r13 = 42 + 10 = 52
    SUB r14, r10, r11    # r14 = 42 - 10 = 32
    
    # Test memory operations
    LW r15, 0(r12)       # Load first word from data section
    SW r13, 16(r12)      # Store result to memory
    
    # Test control flow
    BEQ r10, r11, equal_branch  # Should not branch (42 != 10)
    LI r9, #100          # This should execute (using r9 instead of r16)
    
not_equal:
    BEQ r10, r10, equal_branch  # Should branch (42 == 42)
    LI r8, #200          # This should NOT execute (using r8 instead of r17)
    
equal_branch:
    LI r7, #300          # This should execute (using r7 instead of r18)
    
    # Test quantum features
    QUBIT r5, #0         # Initialize qubit in |0> state (using r5)
    QUBIT r6, #1         # Initialize qubit in |1> state (using r6)
    
    # Test function call
    CALL quantum_function
    
    # Test jump
    JMP final_test
    
quantum_function:
    # Function body
    ADD r4, r5, r6       # Add qubit IDs (using r4)
    RET                  # Return from function
    
final_test:
    # Final test - system call
    LI r10, #0           # Exit code 0
    ECALL                # System call to exit
    
# Expected behavior:
# 1. r10 = 42, r11 = 10, r12 = 0x1000
# 2. r13 = 52 (42 + 10), r14 = 32 (42 - 10)
# 3. r15 = 0x12345678 (loaded from memory)
# 4. Memory at 0x1010 = 52 (stored value)
# 5. r9 = 100 (executed), r8 = undefined (not executed)
# 6. r7 = 300 (executed after branch)
# 7. r5 = qubit_id_0, r6 = qubit_id_1
# 8. r4 = qubit_id_0 + qubit_id_1
# 9. Program exits with code 0 