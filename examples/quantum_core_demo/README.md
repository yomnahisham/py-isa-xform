# QuantumCore ISA Demo

This demo showcases a custom 32-bit RISC-inspired architecture called "QuantumCore" with quantum-inspired features, demonstrating the full capabilities of the py-isa-xform toolkit.

## Overview

**QuantumCore** is a 32-bit RISC-style architecture featuring:
- 16 general-purpose registers (r0-r15)
- Quantum computing instructions (QUBIT)
- Standard RISC operations (ADD, SUB, LW, SW, etc.)
- Control flow instructions (BEQ, J, JAL, etc.)
- Pseudo-instructions (CALL, RET, JMP, NOP, MV)
- System calls (ECALL)

## Files

- `quantum_core_isa.json` - Complete ISA definition
- `quantum_core_test.s` - Assembly test program
- `quantum_core_test.bin` - Assembled binary output
- `quantum_core_test_dis.s` - Disassembled output
- `README.md` - This documentation

## Test Program Features

The test program demonstrates:

1. **Register Operations**
   - Load immediate values (LI)
   - Arithmetic operations (ADD, SUB)
   - Register-to-register operations

2. **Memory Operations**
   - Load word (LW)
   - Store word (SW)
   - Data section with words and ASCII strings

3. **Control Flow**
   - Conditional branching (BEQ)
   - Unconditional jumps (JMP)
   - Function calls (CALL)
   - Function returns (RET)

4. **Quantum Features**
   - QUBIT instruction for quantum bit initialization
   - Quantum state manipulation

5. **System Integration**
   - Environment calls (ECALL)
   - System service integration

## Usage

### Assembling
```bash
python -m src.isa_xform.cli assemble \
  --isa quantum_core_isa.json \
  --input quantum_core_test.s \
  --output quantum_core_test.bin \
  --verbose
```

### Disassembling
```bash
python -m src.isa_xform.cli disassemble \
  --isa quantum_core_isa.json \
  --input quantum_core_test.bin \
  --show-addresses \
  --output quantum_core_test_dis.s \
  --verbose
```

## ISA Features Demonstrated

### Register Set
- **r0**: Always zero (zero register)
- **r1**: Return address (ra)
- **r2**: Stack pointer (sp)
- **r3**: Frame pointer (fp)
- **r4**: Global pointer (gp)
- **r5-r7**: Temporaries (t0-t2)
- **r8-r9**: Saved registers (s0-s1)
- **r10-r15**: Arguments/returns (a0-a5)

### Instruction Formats
- **R-type**: Register operations (ADD, SUB)
- **I-type**: Immediate operations (ADDI, LI, LW)
- **S-type**: Store operations (SW)
- **B-type**: Branch operations (BEQ)
- **J-type**: Jump operations (J, JAL)
- **Q-type**: Quantum operations (QUBIT)

### Pseudo-Instructions
- `NOP` → `ADD r0, r0, r0`
- `MV rd, rs` → `ADD rd, rs, r0`
- `CALL label` → `JAL r1, label`
- `RET` → `JALR r0, r1, 0`
- `JMP label` → `J label`

## Expected Behavior

The test program should:
1. Initialize registers with values
2. Perform arithmetic operations
3. Load and store memory
4. Execute conditional branching
5. Initialize quantum bits
6. Call and return from functions
7. Exit via system call

## Architecture Details

- **Word Size**: 32 bits
- **Endianness**: Little-endian
- **Address Space**: 32-bit (4GB)
- **Instruction Size**: 32 bits
- **Alignment**: 4-byte aligned
- **PC Behavior**: Points to next instruction, offset=4 for jumps

## Memory Layout

- **Code Section**: 0x1000 - 0x7FFF
- **Data Section**: 0x8000 - 0xFFFF
- **Stack Section**: 0xFFFF0000 - 0xFFFFFFFF
- **MMIO**: 0x10000 - 0x1FFFF

## Quantum Features

The ISA includes quantum computing primitives:
- `QUBIT rd, state` - Initialize quantum bit in specified state
- Quantum state registers for qubit management
- Foundation for quantum algorithm implementation

## System Services

ECALL services defined:
- **0x000**: Print character (a0 = character)
- **0x001**: Print string (a0 = string address)
- **0x002**: Exit program (a0 = exit code)

## Toolkit Integration

This demo showcases the toolkit's ability to:
- Load custom ISA definitions from JSON
- Assemble programs with complex instruction sets
- Handle pseudo-instructions and expansions
- Disassemble with address reconstruction
- Support quantum computing concepts
- Manage complex memory layouts
- Handle multiple instruction formats

## Customization

To extend this ISA:
1. Add new instructions to the `instructions` array
2. Define new pseudo-instructions in `pseudo_instructions`
3. Add registers to the `registers` section
4. Extend quantum features in the `quantum` category
5. Add new system services to `ecall_services`

The toolkit will automatically handle the new features without code changes. 