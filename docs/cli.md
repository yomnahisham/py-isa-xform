# Command-Line Interface (CLI)

## Overview

The Command-Line Interface (CLI) provides a comprehensive user interface to the py-isa-xform toolkit, enabling users to perform all major operations including ISA validation, assembly, disassembly, and program analysis through simple, intuitive commands.

## Basic Usage

The CLI is accessed through the `isa_xform.cli` module:

```bash
python -m isa_xform.cli <command> [options]
```

## Command Structure

All commands follow a consistent structure:

```bash
python -m isa_xform.cli <command> [options] [arguments]
```

### Global Options

All commands support these global options:

- `--help`, `-h`: Display help information for the command
- `--verbose`, `-v`: Enable verbose output with detailed information

## Available Commands

### `assemble` - Assembly

Converts assembly source files to machine code.

**Syntax:**
```bash
python -m isa_xform.cli assemble --isa <isa> --input <files> --output <file> [options]
```

**Required Options:**
- `--isa <isa>`: ISA definition file or name (e.g., "zx16", "simple_risc", or path to JSON file)
- `--input <files>`: Input assembly files (one or more)
- `--output <file>`: Output binary file

**Optional Options:**
- `--verbose`, `-v`: Verbose output
- `--list-symbols`: List resolved symbols
- `--raw`: Output raw binary with no header (for legacy/bootloader use)

**Examples:**
```bash
# Basic assembly
python -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin

# Assembly with symbol listing
python -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin --list-symbols

# Raw binary output
python -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin --raw

# Multiple input files
python -m isa_xform.cli assemble --isa zx16 --input file1.s file2.s --output program.bin
```

### `disassemble` - Disassembly

Converts machine code back to assembly with automatic data region detection.

**Syntax:**
```bash
python -m isa_xform.cli disassemble --isa <isa> --input <file> --output <file> [options]
```

**Required Options:**
- `--isa <isa>`: ISA definition file or name
- `--input <file>`: Input binary file
- `--output <file>`: Output assembly file

**Optional Options:**
- `--verbose`, `-v`: Verbose output
- `--debug`: Show detailed PC progression and mode switches
- `--show-addresses`: Show addresses in output
- `--show-machine-code`: Show machine code in output
- `--start-address <addr>`: Starting address for disassembly (default: 0)
- `--data-regions <regions>`: Data regions as start-end pairs (e.g., "0x0-0xA 0x100-0x200")
- `--smart`: Reconstruct pseudo-instructions using patterns from ISA definition
- `--reconstruct-labels`: Reconstruct labels in branch and jump instructions

**Disassembly Modes:**
- **Raw Mode (default)**: Shows only real hardware instructions as encoded in the binary
- **Smart Mode (--smart)**: Reconstructs pseudo-instructions using patterns from the ISA definition

**Data Region Detection:**
The disassembler automatically detects data regions based on your ISA's memory layout when `--data-regions` is not specified. This includes:
- Interrupt vectors (treated as data)
- Data sections (treated as data)
- MMIO regions (treated as data)
- Code sections (treated as instructions)

**Examples:**
```bash
# Basic disassembly
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s

# Smart disassembly with pseudo-instruction reconstruction
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s --smart

# Manual override with custom data regions
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s --data-regions 0x100-0x200

# Start disassembly at specific address
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s --start-address 0x20

# Debug mode with detailed information
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s --debug --show-addresses
```

### `validate` - ISA Definition Validation

Validates ISA definition files for correctness and completeness.

**Syntax:**
```bash
python -m isa_xform.cli validate --isa <isa> [options]
```

**Required Options:**
- `--isa <isa>`: ISA definition file or name

**Optional Options:**
- `--verbose`, `-v`: Display detailed validation information

**Examples:**
```bash
# Basic validation
python -m isa_xform.cli validate --isa zx16

# Verbose validation
python -m isa_xform.cli validate --isa zx16 --verbose

# Validate custom ISA file
python -m isa_xform.cli validate --isa my_isa.json --verbose
```

### `parse` - Assembly Code Parsing

Parses assembly code and displays the Abstract Syntax Tree (AST) representation.

**Syntax:**
```bash
python -m isa_xform.cli parse --isa <isa> --input <file> [options]
```

**Required Options:**
- `--isa <isa>`: ISA definition file or name
- `--input <file>`: Path to the assembly source file

**Optional Options:**
- `--output <file>`: Output file for AST (JSON format)
- `--verbose`, `-v`: Display detailed parsing information

**Examples:**
```bash
# Basic parsing
python -m isa_xform.cli parse --isa zx16 --input program.s

# Save AST to file
python -m isa_xform.cli parse --isa zx16 --input program.s --output ast.json

# Verbose parsing
python -m isa_xform.cli parse --isa zx16 --input program.s --verbose
```

### `list-isas` - List Available ISAs

Lists all available ISA definitions.

**Syntax:**
```bash
python -m isa_xform.cli list-isas [options]
```

**Optional Options:**
- `--verbose`, `-v`: Display detailed information about each ISA

**Examples:**
```bash
# List all ISAs
python -m isa_xform.cli list-isas

# Verbose listing
python -m isa_xform.cli list-isas --verbose
```

### `simulate` - Run Modular Simulator

Runs the modular simulator with graphics support to execute and visualize binary programs.

**Syntax:**
```bash
python -m isa_xform.cli simulate --isa <isa> --input <file> [options]
```

**Required Options:**
- `--isa <isa>`: ISA definition file or name
- `--input <file>`: Input binary file to simulate

**Optional Options:**
- `--step`: Step through instructions one by one (press Enter to continue)
- `--verbose`, `-v`: Verbose output with detailed information

**Features:**
- **Graphics Support**: Visual display of program execution with pygame
- **Step Mode**: Execute instructions one at a time for debugging
- **Register Display**: Real-time register state visualization
- **Memory Dump**: Display memory contents at the end of execution
- **Keyboard Input**: Support for keyboard input simulation
- **ECALL Services**: Built-in system call support (exit, print, input, etc.)

**Examples:**
```bash
# Basic simulation
python -m isa_xform.cli simulate --isa zx16 --input program.bin

# Step-by-step execution
python -m isa_xform.cli simulate --isa zx16 --input program.bin --step

# Verbose simulation with detailed output
python -m isa_xform.cli simulate --isa zx16 --input program.bin --verbose
```

### `scaffold` - Generate ISA Scaffold

Generates a new ISA scaffold definition with basic structure and common instructions.

**Syntax:**
```bash
python -m isa_xform.cli scaffold --name <name> --instructions <list> [options]
```

**Required Options:**
- `--name <name>`: Name of the ISA
- `--instructions <list>`: Comma-separated list of instructions to include

**Optional Options:**
- `--directives <list>`: Comma-separated list of directives to include
- `--word-size <size>`: Word size in bits (default: 16)
- `--instruction-size <size>`: Instruction size in bits (default: 16)
- `--register-count <count>`: Number of general-purpose registers (default: 8)
- `--registers <list>`: Comma-separated list of register names (overrides --register-count)
- `--output <file>`: Output file path (default: {name}_isa.json)

**Examples:**
```bash
# Generate basic ISA
python -m isa_xform.cli scaffold --name "MY_ISA" --instructions "ADD,SUB,LI,J,ECALL" --directives ".org,.word,.byte"

# Generate comprehensive ISA
python -m isa_xform.cli scaffold --name "ADVANCED_ISA" \
  --instructions "ADD,SUB,AND,OR,XOR,ADDI,ANDI,ORI,XORI,LI,J,JAL,BEQ,BNE,LW,SW,ECALL" \
  --directives ".org,.word,.byte,.ascii,.align" \
  --word-size 16 \
  --instruction-size 16

# Generate with custom registers
python -m isa_xform.cli scaffold --name "CUSTOM_ISA" \
  --instructions "ADD,SUB,LI" \
  --registers "r0,r1,r2,r3,r4,r5,r6,r7" \
  --output my_custom_isa.json
```

## Built-in ISA Definitions

The toolkit includes several built-in ISA definitions that can be referenced by name:

- **zx16**: 16-bit RISC-V inspired ISA (reference implementation)
- **riscv_rv32i**: Standard RISC-V 32-bit integer instruction set
- **simple_risc**: Basic RISC-style instruction set for educational purposes
- **modular_example**: Demonstrates modular ISA design patterns
- **custom_isa_example**: Example custom ISA definition
- **custom_modular_isa**: Modular custom ISA example
- **test_user_custom_isa**: Test custom ISA for validation
- **complete_user_isa_example**: Complete example of a user-defined ISA
- **variable_length_example**: Demonstrates variable-length instruction support
- **quantum_core_isa**: Quantum computing instruction set example

## Example Workflows

### Complete Assembly/Disassembly Workflow

```bash
# 1. Create a simple assembly program
cat > program.s << 'EOF'
.org 32
_start:
    LI x0, 10
    LI x1, 5
    ADD x0, x1
    ECALL 0x3FF
EOF

# 2. Assemble the program
python -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin

# 3. Disassemble to verify
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program_dis.s

# 4. Compare the output
diff program.s program_dis.s
```

### ISA Development Workflow

```bash
# 1. Generate a new ISA scaffold
python -m isa_xform.cli scaffold --name "MY_ISA" \
  --instructions "ADD,SUB,LI,J,ECALL" \
  --directives ".org,.word,.byte" \
  --output my_isa.json

# 2. Validate the generated ISA
python -m isa_xform.cli validate --isa my_isa.json --verbose

# 3. Create a test program
cat > test.s << 'EOF'
.org 0
_start:
    LI r0, 42
    ADD r1, r0
    ECALL 0
EOF

# 4. Test assembly and disassembly
python -m isa_xform.cli assemble --isa my_isa.json --input test.s --output test.bin
python -m isa_xform.cli disassemble --isa my_isa.json --input test.bin --output test_dis.s
```

### Debugging Workflow

```bash
# 1. Parse assembly to check syntax
python -m isa_xform.cli parse --isa zx16 --input program.s --verbose

# 2. Assemble with symbol listing
python -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin --list-symbols

# 3. Disassemble with debug information
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program_dis.s --debug --show-addresses
```

## Error Handling

The CLI provides comprehensive error handling with detailed context information:

```
Error: Immediate value 256 doesn't fit in 8-bit unsigned field at line 15, column 20 in main.s
  Context: LDI $r1, #256
  Suggestion: Use a value between 0 and 255, or use a different instruction
```

Common error types and solutions:

1. **ISA Loading Errors**: Check that the ISA file exists and is valid JSON
2. **Assembly Errors**: Verify instruction syntax and operand constraints
3. **Disassembly Errors**: Check binary file format and ISA compatibility
4. **Validation Errors**: Fix missing or invalid fields in ISA definition

## Professional Binary Format

The toolchain generates **headered binaries by default** following industry best practices:

- **Automatic Entry Point Detection**: Disassemblers automatically determine the correct starting address
- **Tool Interoperability**: Works seamlessly with debuggers, loaders, and other tools
- **Robust Disassembly**: No manual address specification required
- **Industry Standard**: Follows patterns from ELF, PE, and other executable formats

Use the `--raw` option for legacy systems or bootloaders that require raw binary output.

## Integration with Development Tools

The CLI is designed to integrate seamlessly with development workflows:

### Makefile Integration
```makefile
%.bin: %.s
	python -m isa_xform.cli assemble --isa zx16 --input $< --output $@

%.s: %.bin
	python -m isa_xform.cli disassemble --isa zx16 --input $< --output $@
```

### Script Integration
```bash
#!/bin/bash
# Build script example
for file in *.s; do
    base=${file%.s}
    python -m isa_xform.cli assemble --isa zx16 --input "$file" --output "${base}.bin"
done
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Validate ISA
  run: python -m isa_xform.cli validate --isa zx16

- name: Assemble Programs
  run: |
    python -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin
    python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program_dis.s
```

## Troubleshooting

### Common Issues

1. **"Unknown ISA"**: Use `python -m isa_xform.cli list-isas` to see available ISAs
2. **"File not found"**: Check file paths and ensure files exist
3. **"Invalid ISA definition"**: Use `python -m isa_xform.cli validate --isa <isa>` to check for errors
4. **"Assembly/disassembly mismatch"**: Check ISA definition and operand formatting

### Getting Help

```bash
# General help
python -m isa_xform.cli --help

# Command-specific help
python -m isa_xform.cli assemble --help
python -m isa_xform.cli disassemble --help
python -m isa_xform.cli validate --help
```

## Conclusion

The CLI provides a complete interface to the py-isa-xform toolkit, enabling both interactive use and automation. The consistent command structure, comprehensive error handling, and integration capabilities make it suitable for both educational and production environments.
