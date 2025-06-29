# Test Case TC002: Single-File Assembly and Modular Disassembly

## Description
This test case demonstrates single-file assembly and the improved modular disassembler capabilities.

## Files
- `test_program.s` - Single-file test program with various assembly features
- `disassembled.s` - Original disassembly output (4140 lines, mostly NOPs)
- `disassembled_modular.s` - Improved disassembly output
- `disassembled_from_tc001.s` - Demonstration using TC001 binary

## Key Improvements Demonstrated

### Modular Disassembler Features
1. **ISA Address Specifications**: Respects ISA's `address_space.default_code_start` setting
2. **Smart Padding Detection**: Large blocks of zeros are identified as data sections
3. **Reduced Output Size**: From 4140 lines to manageable output
4. **Proper Address Handling**: Starts from correct entry point

### Test Results (using TC001 binary)
- **Instructions Disassembled**: 65
- **Symbols Found**: 8  
- **Data Sections**: 3
- **Start Address**: 0x1000 (ISA-specified)

## Before vs After Comparison
- **Before**: 4140 lines starting from 0x0000 with thousands of NOPs
- **After**: 74 lines starting from 0x1000 with actual instructions and proper data sections

## Usage
```bash
# Disassemble with modular improvements
python3 -m isa_xform.cli disassemble --isa simple_risc --input program.bin --output disassembled_modular.s --verbose --show-addresses
```

## Notes
- The original `test_program.s` has some directive issues that need to be resolved for full testing
- The modular disassembler improvements are demonstrated using the TC001 binary file 