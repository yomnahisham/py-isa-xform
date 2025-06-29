# TC-ZX16-R1: R1-type Instruction Format Test

## Overview
This test validates the ZX16 R1-type instruction format, which uses a single register operand.

## Instruction Format
```
R1-type: [15:10][9:7][6:3][2:0]
         unused rd  funct opcode
```

## Instructions Tested
- **NOP**: No operation (opcode 000, funct 0000)
- **EBREAK**: Environment break/debugger breakpoint (opcode 000, funct 0001)

## Test Coverage
- Basic R1-type instruction encoding
- Multiple consecutive NOPs (tests assembler/disassembler handling)
- System debugging instruction (EBREAK)

## Expected Behavior
1. NOP instructions should encode correctly and be disassembled properly
2. EBREAK should encode as a distinct R1-type instruction
3. Multiple NOPs should be handled without issues

## Running the Test
```bash
# Assemble the test
python3 -m isa_xform.cli assemble -i tests/TC-ZX16-R1/test_r1_format.s -o test_r1.bin --isa zx16

# Disassemble back to verify
python3 -m isa_xform.cli disassemble -i test_r1.bin -o test_r1_disasm.s --isa zx16

# Compare original and disassembled
diff tests/TC-ZX16-R1/test_r1_format.s test_r1_disasm.s
```

## Expected Output
The disassembled output should match the original assembly, with proper instruction recognition and formatting. 