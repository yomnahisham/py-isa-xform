# ZX16 Test Cases

This directory contains comprehensive test cases for the ZX16 ISA implementation, demonstrating instruction coverage, ECALL services, and control flow operations.

## Test Cases Overview

### 1. test_arithmetic.s
Comprehensive arithmetic and logical operations test covering:
- **Load Operations**: `LI` (Load Immediate)
- **Arithmetic Operations**: `ADD`, `SUB`, `ADDI` (Add/Subtract registers and immediate)
- **Logical Operations**: `AND`, `OR`, `XOR` (Bitwise operations)
- **Comparison Operations**: `SLT`, `SLTU` (Set if less than, signed/unsigned)
- **Shift Operations**: `SLL`, `SRL`, `SRA` (Logical and arithmetic shifts)
- **Data Movement**: `MV` (Move register)

This test demonstrates the full range of arithmetic and logical instructions available in ZX16, using only valid registers (x0-x7) and immediate values within the 7-bit signed range (-64 to 63).

Expected result: Exit code 0 (final value in a0 after all operations)

### 2. test_ecall.s
System call services demonstration:
- `ECALL 0x002` - Print string service
- `ECALL 0x001` - Read character service  
- `ECALL 0x000` - Print character service
- `ECALL 0x3FF` - Exit program service

This test validates the ECALL system call mechanism and demonstrates proper service invocation. The test uses immediate values that fit within ZX16's 7-bit signed immediate constraints.

### 3. test_branching.s
Control flow and branching operations test:
- `BEQ` (Branch if Equal) - Conditional branching based on register equality
- `BNE` (Branch if Not Equal) - Conditional branching based on register inequality
- `BZ` (Branch if Zero) - Conditional branching when register is zero
- `BNZ` (Branch if Not Zero) - Conditional branching when register is non-zero
- `J` (Unconditional Jump) - Direct control flow transfer

This test demonstrates proper control flow execution and validates that skipped instructions are not executed during branching operations.

Expected result: Exit code 42 (final value in a0 after successful branching)

## ZX16 ISA Features Demonstrated

### Register Set
- 8 general-purpose registers (x0-x7)
- Register aliases: t0, ra, sp, s0, s1, t1, a0, a1
- 16-bit register width

### Instruction Formats
- **R-type**: Two-operand register operations (e.g., `ADD rd, rs2`)
- **I-type**: Register-immediate operations (e.g., `ADDI rd, imm`)
- **J-type**: Jump instructions with address fields

### Immediate Constraints
- 7-bit signed immediate values (-64 to 63)
- Proper handling of immediate overflow detection
- Sign extension for negative values

### System Services
- Multiple ECALL service numbers
- String printing capabilities
- Character I/O operations
- Program termination

## Running the Tests

### Assembly Process
```bash
# Assemble arithmetic test
python3 -m isa_xform.cli assemble --isa zx16 --input tests/TC-ZX16/test_arithmetic.s --output test_arithmetic.bin

# Assemble ECALL test
python3 -m isa_xform.cli assemble --isa zx16 --input tests/TC-ZX16/test_ecall.s --output test_ecall.bin

# Assemble branching test
python3 -m isa_xform.cli assemble --isa zx16 --input tests/TC-ZX16/test_branching.s --output test_branching.bin
```

### Disassembly Verification
```bash
# Disassemble to verify correct instruction encoding
python3 -m isa_xform.cli disassemble --isa zx16 --input test_arithmetic.bin --output test_arithmetic_dis.s
python3 -m isa_xform.cli disassemble --isa zx16 --input test_ecall.bin --output test_ecall_dis.s
python3 -m isa_xform.cli disassemble --isa zx16 --input test_branching.bin --output test_branching_dis.s
```

### Expected Disassembly Output
The disassembler correctly outputs operands in the order specified by the instruction syntax (e.g., `ADD rd, rs2`), not the encoding field order, ensuring readability and consistency with assembly source code.

## Test Coverage

These test cases provide comprehensive coverage of:
- **Instruction Types**: Arithmetic, logical, control flow, and system operations
- **Register Usage**: All available registers and their aliases
- **Immediate Handling**: Proper immediate value constraints and sign extension
- **Control Flow**: Conditional and unconditional branching
- **System Services**: Multiple ECALL service implementations
- **Assembly/Disassembly**: Round-trip verification of instruction encoding

## Validation Criteria

Each test case validates:
1. **Correct Assembly**: All instructions assemble without errors
2. **Proper Disassembly**: Disassembled output matches expected syntax
3. **Operand Order**: Disassembly maintains correct operand order per instruction syntax
4. **Register Constraints**: Only valid ZX16 registers are used
5. **Immediate Constraints**: All immediate values fit within 7-bit signed range
6. **Control Flow**: Branching instructions execute correctly
7. **System Services**: ECALL services are properly encoded

This test suite demonstrates the ZX16 ISA implementation meets the requirements for instruction coverage, ECALL services, and comprehensive testing capabilities. 