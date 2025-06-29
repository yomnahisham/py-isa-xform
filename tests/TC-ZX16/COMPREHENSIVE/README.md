# TC-ZX16-COMPREHENSIVE: Complete ZX16 ISA Test

## Overview
This is the comprehensive test suite for the ZX16 16-bit RISC-V inspired ISA. It tests all instruction format types, ECALL system calls, pseudo-instructions, and advanced features in a single cohesive program.

## Test Coverage

### Instruction Format Types
- **R1-type**: Single register format (NOP, EBREAK)
- **R3-type**: Three register format (ADD, SUB, AND, OR, XOR, SLL, SRL, SRA)
- **I6-type**: 6-bit immediate format (ADDI, ANDI, ORI, XORI, SLLI, SRLI, SRAI, LB, LW, SB, SW, JALR)
- **I9-type**: 9-bit immediate format (LI, ECALL)
- **B-type**: Branch format (BEQ, BNE, BLT, BGE, BLTU, BGEU)
- **J-type**: Jump format (JAL)
- **U-type**: Upper immediate format (LUI, AUIPC)

### System Features
- **ECALL Instructions**: Tests all major syscall numbers (0x000-0x3FF)
- **Memory Operations**: Word and byte loads/stores with offsets
- **Stack Management**: Stack pointer initialization and usage
- **Function Calls**: Subroutines, nested calls, return handling

### Pseudo-Instructions
- **MOV**: Register move (expands to ADD rd, rs, x0)
- **CLR**: Clear register (expands to XOR rd, rd, rd)
- **NOT**: Bitwise NOT (expands to XORI rd, rs, -1)
- **NEG**: Negate (expands to SUB rd, x0, rs)
- **INC/DEC**: Increment/decrement (expands to ADDI rd, rd, ±1)
- **JMP**: Unconditional jump (expands to JAL x0, offset)
- **CALL/RET**: Function call/return
- **LI16**: Load 16-bit immediate
- **LA**: Load address

### Advanced Features
- **Symbol Resolution**: Forward and backward references
- **Data Sections**: Mixed code and data
- **Address Calculations**: PC-relative addressing with AUIPC
- **Branching Logic**: Complex control flow paths
- **Memory Layout**: Proper ZX16 memory organization

## ZX16 Architecture Features Tested

### Memory Map
- **Code Section**: Starts at 0x0020 (32)
- **Data Section**: Located at 0x4000 
- **Stack**: Initialized to 0xEFFE (61438)
- **MMIO Region**: 0xF000-0xFFFF (not directly tested)

### Register Usage
- **x0-x7**: All 8 general-purpose registers
- **ABI Names**: t0, ra, sp, s0/fp, s1, t1, a0, a1
- **Special Usage**: Stack pointer, return address, function arguments

### Instruction Encodings
All instruction formats are tested with proper bit field allocation:
- Opcodes in bits [2:0]
- Function codes in appropriate bit ranges
- Register fields in correct positions
- Immediate values with proper sign extension

## Running the Comprehensive Test

### Basic Assembly/Disassembly
```bash
# Assemble the comprehensive test
python3 -m isa_xform.cli assemble -i tests/TC-ZX16-COMPREHENSIVE/test_comprehensive.s -o comprehensive.bin --isa zx16 --verbose

# Disassemble back to verify
python3 -m isa_xform.cli disassemble -i comprehensive.bin -o comprehensive_disasm.s --isa zx16 --show-addresses --show-machine-code

# View the disassembled output
cat comprehensive_disasm.s
```

### Validation Commands
```bash
# Validate ISA definition
python3 -m isa_xform.cli validate --isa zx16

# Parse only (syntax check)
python3 -m isa_xform.cli parse -i tests/TC-ZX16-COMPREHENSIVE/test_comprehensive.s --isa zx16

# List available ISAs
python3 -m isa_xform.cli list-isas
```

### Advanced Testing
```bash
# Test with different start addresses
python3 -m isa_xform.cli disassemble -i comprehensive.bin -o test_addr.s --isa zx16 --start-address 0x0020

# Generate with symbol information
python3 -m isa_xform.cli assemble -i tests/TC-ZX16-COMPREHENSIVE/test_comprehensive.s -o comprehensive.bin --isa zx16 --symbols comprehensive.sym
```

## Expected Results

### Assembly Success Criteria
1. All instructions should assemble without errors
2. Symbol resolution should work for all labels
3. Forward and backward references should resolve correctly
4. Pseudo-instructions should expand properly
5. Memory layout should be organized correctly

### Disassembly Verification
1. All instructions should disassemble to valid mnemonics
2. Register names should use proper ABI aliases
3. Immediate values should be formatted correctly
4. Branch targets should resolve to label names
5. Data sections should be identified properly

### Instruction Coverage
- **33 base instructions**: All should be tested
- **15 pseudo-instructions**: All should expand correctly
- **8 instruction formats**: All should encode/decode properly
- **ECALL variants**: Multiple syscall numbers tested

## Debugging Failed Tests

### Common Issues
1. **Symbol resolution errors**: Check for typos in label names
2. **Immediate range errors**: Verify values fit in specified bit fields
3. **Instruction format errors**: Ensure operands match expected formats
4. **Memory alignment**: Check word accesses are aligned to even addresses

### Debug Commands
```bash
# Verbose assembly for detailed output
python3 -m isa_xform.cli assemble -i test_comprehensive.s --isa zx16 --verbose --debug

# Check specific instruction encoding
python3 -c "
from src.isa_xform.core.isa_loader import ISALoader
loader = ISALoader()
isa = loader.load_isa_from_file('src/isa_definitions/zx16.json')
print('Instructions:', len(isa.instructions))
for instr in isa.instructions[:5]:
    print(f'{instr.mnemonic}: {instr.format}')
"
```

## Test Success Metrics
- **Assembly**: Should complete without errors or warnings
- **Disassembly**: Should produce readable, correct assembly
- **Round-trip**: Original → Binary → Disassembled should be functionally equivalent
- **Coverage**: All instruction types and features should be exercised
- **Performance**: Should complete in reasonable time (< 5 seconds)

This comprehensive test serves as the primary validation that the ZX16 ISA definition is correct and the py-isa-xform tool can handle all features of the architecture. 