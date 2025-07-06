# Debug Disassembly Guide

The debug disassembly functionality allows you to track the program counter (PC) progression and understand how the disassembler separates code from data sections.

## Overview

When you enable debug mode, the disassembler provides detailed output showing:
- PC counter progression through the binary
- Mode switches between CODE and DATA
- Instruction decoding attempts
- Data section detection
- Final statistics

## Usage

### Command Line Interface

```bash
# Basic debug disassembly
python3 -m isa_xform.cli disassemble --isa zx16 --input program.bin --output disassembled.s --debug

# With additional options
python3 -m isa_xform.cli disassemble \
    --isa zx16 \
    --input program.bin \
    --output disassembled.s \
    --debug \
    --show-addresses \
    --start-address 0x1000
```

### Programmatic Usage

```python
from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.symbol_table import SymbolTable

# Load ISA and create disassembler
loader = ISALoader()
isa_definition = loader.load_isa("zx16")
symbol_table = SymbolTable()
disassembler = Disassembler(isa_definition, symbol_table)

# Run disassembly with debug output
result = disassembler.disassemble(
    machine_code, 
    start_address=0x1000, 
    debug=True
)
```

## Debug Output Explanation

### Initial Information
```
[DEBUG] Starting disassembly at PC=0x1000
[DEBUG] Machine code size: 68 bytes
[DEBUG] Instruction size: 2 bytes
[DEBUG] ISA: ZX16
[DEBUG] Endianness: little
```

### PC Progression
```
[DEBUG] PC=0x1000 | Byte offset=0000 | Mode=CODE
[DEBUG] PC=0x1002 | Byte offset=0002 | Mode=CODE
[DEBUG] PC=0x1004 | Byte offset=0004 | Mode=CODE
```

### Instruction Decoding
```
[DEBUG] PC=0x1000 | Decoded: LI x6, 10
[DEBUG] PC=0x1002 | Decoded: ADD x6, x7
[DEBUG] PC=0x1004 | Decoded: JR x1
```

### Unknown Instructions
```
[DEBUG] PC=0x1006 | Unknown instruction: 0x1234 (consecutive invalid: 1)
[DEBUG] PC=0x1006 | SWITCHING TO DATA MODE (unknown instruction)
```

### Data Mode
```
[DEBUG] PC=0x1008 | Byte offset=0008 | Mode=DATA
[DEBUG] PC=0x1008 | Adding to data section: 0x5678
```

### NOP Detection
```
[DEBUG] PC=0x100A | NOP detected (consecutive: 1)
[DEBUG] PC=0x100C | NOP detected (consecutive: 2)
```

### Return Instructions
```
[DEBUG] PC=0x1004 | Return instruction detected
```

### Final Statistics
```
[DEBUG] Disassembly complete!
[DEBUG] Total instructions: 30
[DEBUG] Data sections: 4
[DEBUG] Final PC: 0x1064
[DEBUG] Code range: 0x1000 - 0x1063
[DEBUG] Data sections at: ['0x105C', '0x105E', '0x1060', '0x1062']
```

## Understanding the Output

### PC Counter
- Shows the current program counter address
- Increments by instruction size (typically 2 or 4 bytes)
- Helps track where the disassembler thinks it is in the binary

### Mode Tracking
- **CODE**: Disassembler is trying to decode instructions
- **DATA**: Disassembler has switched to data mode and treats bytes as data

### Mode Switching Triggers
1. **Unknown Instructions**: When an instruction cannot be decoded
2. **Return Instructions**: After detecting a return instruction (JR, RET, etc.)
3. **Large NOP Blocks**: After many consecutive zero bytes
4. **Decode Errors**: When instruction decoding fails

### Data Section Detection
- Unknown instructions are added to data sections
- ASCII strings are automatically detected
- Data sections are reported with their addresses

## Example Scenarios

### Scenario 1: Pure Code
```
[DEBUG] PC=0x1000 | Mode=CODE
[DEBUG] PC=0x1000 | Decoded: LI x6, 10
[DEBUG] PC=0x1002 | Mode=CODE
[DEBUG] PC=0x1002 | Decoded: ADD x6, x7
```

### Scenario 2: Code + Data
```
[DEBUG] PC=0x1000 | Mode=CODE
[DEBUG] PC=0x1000 | Decoded: JR x1
[DEBUG] PC=0x1002 | Mode=CODE
[DEBUG] PC=0x1002 | Unknown instruction: 0x1234
[DEBUG] PC=0x1002 | SWITCHING TO DATA MODE
[DEBUG] PC=0x1004 | Mode=DATA
[DEBUG] PC=0x1004 | Adding to data section: 0x5678
```

### Scenario 3: NOP Padding
```
[DEBUG] PC=0x1000 | Mode=CODE
[DEBUG] PC=0x1000 | NOP detected (consecutive: 1)
[DEBUG] PC=0x1002 | Mode=CODE
[DEBUG] PC=0x1002 | NOP detected (consecutive: 2)
[DEBUG] PC=0x1004 | Mode=CODE
[DEBUG] PC=0x1004 | NOP detected (consecutive: 3)
[DEBUG] PC=0x1006 | SWITCHING TO DATA MODE (large NOP block)
```

## Troubleshooting

### PC Not Incrementing Correctly
- Check the ISA definition's instruction size
- Verify the endianness setting
- Ensure the start address is correct

### Unexpected Mode Switches
- Review the instruction definitions in the ISA
- Check for valid instructions that might be misidentified
- Verify the binary file integrity

### Missing Data Sections
- The disassembler might be too aggressive in trying to decode instructions
- Check if the binary contains actual data that should be preserved

## Best Practices

1. **Start with Debug**: Always use debug mode when analyzing unknown binaries
2. **Check PC Progression**: Ensure the PC increments correctly through the binary
3. **Review Mode Switches**: Understand why the disassembler switches between CODE and DATA modes
4. **Validate Results**: Compare debug output with expected binary structure
5. **Use Multiple ISAs**: Try different ISA definitions if one doesn't work well

## Examples

See the following example files:
- `test_debug_disassembly.py`: Basic debug functionality test
- `debug_disassembly_example.py`: Comprehensive examples with multiple ISAs
- `tests/TC-ZX16/comprehensive/`: Real binary analysis examples 