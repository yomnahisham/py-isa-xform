# Test Case TC001: Multi-File Assembly and Modular Disassembly

## Description
This test case demonstrates the multi-file assembly capabilities and the improved modular disassembler that respects ISA address specifications.

## Files
- `main.s` - Main program file with entry point and core logic
- `system.s` - System initialization module
- `data.s` - Data processing module
- `program.bin` - Assembled binary output
- `disassembled_modular.s` - Improved disassembly output

## Key Improvements

### Modular Disassembler
1. **ISA Address Specifications**: The disassembler now respects the ISA's `address_space.default_code_start` setting (0x1000)
2. **Reduced NOPs**: Large blocks of padding zeros are now properly identified as data sections instead of NOP instructions
3. **Smart Data Detection**: Consecutive NOPs beyond a threshold (8) are treated as data sections
4. **Proper Entry Point**: Uses the binary file's entry point (0x1000) when available

### Before vs After
- **Before**: 4140 lines of mostly NOPs starting from address 0x0000
- **After**: 74 lines with actual instructions starting from 0x1000, with data sections properly identified

## Test Results
- **Instructions Disassembled**: 65
- **Symbols Found**: 8
- **Data Sections**: 3
- **Start Address**: 0x1000 (ISA-specified)

## Usage
```bash
# Assemble multi-file program
python3 -m isa_xform.cli assemble --isa simple_risc --input main.s system.s data.s --output program.bin

# Disassemble with modular improvements
python3 -m isa_xform.cli disassemble --isa simple_risc --input program.bin --output disassembled_modular.s --verbose
``` 