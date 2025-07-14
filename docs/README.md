# py-isa-xform Documentation

Comprehensive documentation for the py-isa-xform toolkit, a professional-grade system for creating, analyzing, and working with custom instruction set architectures (ISAs). This documentation provides complete guides for all aspects of the system.

## Overview

py-isa-xform is a professional-grade toolkit designed for educators, researchers, and developers working with custom instruction set architectures. It provides a complete ecosystem for ISA development, from specification to implementation, with particular emphasis on the ZX16 16-bit RISC-V inspired instruction set architecture.

### Key Features

- **ISA-Agnostic Design**: Works with any custom instruction set architecture
- **Complete Assembly Toolchain**: Parse, assemble, and disassemble with full symbol resolution
- **Custom Instruction Support**: Define instruction behavior using Python code
- **Professional Error Handling**: Comprehensive error reporting with context and suggestions
- **Modular Architecture**: Clean separation of concerns with well-defined interfaces
- **Extensive Testing**: Comprehensive test suite with multiple ISA examples
- **Rich Documentation**: Complete guides and examples for all features
- **Variable Length Instruction Support**: Support for ISAs with variable-length instructions
- **Automatic Data Region Detection**: Smart disassembly that automatically detects code vs data regions

## Documentation Structure

- **[Getting Started](getting-started.md)** - Quick start guide and installation
- **[ISA Creation Guide](isa-creation-guide.md)** - Step-by-step custom ISA creation based on ZX16 and variable length examples
- **[ISA Definition](isa-definition.md)** - Complete ISA definition reference
- **[Custom Instructions](custom-instructions.md)** - Custom instruction implementation guide
- **[Architecture](architecture.md)** - System design and component overview
- **[API Reference](api-reference.md)** - Complete API documentation
- **[CLI Reference](cli.md)** - Command-line interface documentation
- **[Assembler](assembler.md)** - Assembly process and features
- **[Disassembler](disassembler.md)** - Disassembly process and features
- **[Parser](parser.md)** - Assembly language parsing
- **[Symbol Table](symbol_table.md)** - Symbol management and resolution
- **[ISA Loader](isa_loader.md)** - ISA definition loading and validation
- **[Bit Utils](bit-utils.md)** - Bit manipulation utilities
- **[Error Handling](error-handling.md)** - Error management and reporting
- **[Testing](testing.md)** - Testing guide and best practices
- **[Contributing](contributing.md)** - Development and contribution guidelines
- **[Development Journey](DEVELOPMENT_JOURNEY.md)** - Project history, challenges, and solutions

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yomnahisham/py-isa-xform.git
cd py-isa-xform

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### Basic Usage

```bash
# Assemble a program
python -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin

# Disassemble a program with automatic data region detection
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program_dis.s

# Smart disassembly with pseudo-instruction reconstruction
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program_dis.s --smart

# List available ISAs
python -m isa_xform.cli list-isas

# Validate ISA definition
python -m isa_xform.cli validate --isa zx16
```

### Example Assembly Program

```assembly
# ZX16 example program
    .text
    .globl main

main:
    LI a0, 10          # Load immediate value
    LI a1, 5           # Load immediate value
    ADD a0, a1         # Add registers
    ECALL 0x3FF        # Exit program
```

## Built-in ISAs

The toolkit includes several built-in ISA definitions:

- **ZX16**: 16-bit RISC-V inspired ISA by Dr. Mohamed Shalan (Professor @ AUC) - the reference implementation
- **RISC-V RV32I**: Standard RISC-V 32-bit integer instruction set
- **Simple RISC**: Basic RISC-style instruction set for educational purposes
- **Modular Example**: Demonstrates modular ISA design patterns
- **Custom ISA Example**: Example custom ISA definition
- **Custom Modular ISA**: Modular custom ISA example
- **Test User Custom ISA**: Test custom ISA for validation
- **Complete User ISA Example**: Complete example of a user-defined ISA
- **Variable Length Example**: Demonstrates variable-length instruction support
- **Quantum Core ISA**: Quantum computing instruction set example

## Core Components

### ISA Loader
Loads and validates ISA definitions from JSON files, providing a unified interface for working with both built-in and user-supplied ISAs.

### Parser
Converts assembly language source code into an Abstract Syntax Tree (AST), handling various syntax formats and providing detailed error reporting.

### Assembler
Performs two-pass assembly with symbol resolution, pseudo-instruction expansion, and comprehensive validation based on ISA definitions.

### Disassembler
Converts machine code back into human-readable assembly, with correct operand ordering and automatic data section detection.

### Symbol Table
Manages symbols, labels, and forward references during the assembly process, providing robust address resolution and validation.

### Bit Utils
Provides low-level bit manipulation functions for instruction encoding, decoding, and data processing.

### Simulator
Provides instruction execution simulation for testing and debugging ISA implementations.

## Custom Instruction System

The toolkit supports custom instruction implementations using Python code embedded in ISA definitions:

```json
{
  "mnemonic": "MULT",
  "implementation": "# Custom multiplication\nrd_val = read_register(operands['rd'])\nrs2_val = read_register(operands['rs2'])\nresult = (rd_val * rs2_val) & 0xFFFF\nwrite_register(operands['rd'], result)"
}
```

## Variable Length Instruction Support

The toolkit supports ISAs with variable-length instructions through the `variable_length_instructions` configuration:

```json
{
  "variable_length_instructions": true,
  "instruction_length_config": {
    "enabled": true,
    "length_determination": {
      "method": "opcode_based",
      "opcode_field": "opcode",
      "opcode_position": "31:24"
    },
    "length_table": {
      "0x00": 8,
      "0x01": 16,
      "0x02": 32
    }
  }
}
```

## Automatic Data Region Detection

The disassembler automatically detects data vs code regions based on ISA memory layout:

- **Interrupt vectors**: Treated as data
- **Data sections**: Treated as data  
- **MMIO regions**: Treated as data
- **Code sections**: Treated as instructions

This can be overridden with manual data region specification:

```bash
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s --data-regions 0x100-0x200
```

## Error Handling

The system provides comprehensive error handling with detailed context information:

```
Error: Immediate value 256 doesn't fit in 8-bit unsigned field at line 15, column 20 in main.s
  Context: LDI $r1, #256
  Suggestion: Use a value between 0 and 255, or use a different instruction
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/important/ -v
python -m pytest tests/custom/ -v

# Run with coverage
python -m pytest tests/ --cov=src/isa_xform --cov-report=html
```

## ISA Creation Guide

The [ISA Creation Guide](isa-creation-guide.md) provides comprehensive instructions for creating custom ISAs, with examples based on:

- **ZX16 ISA**: The reference implementation showing best practices
- **Variable Length Example**: Demonstrating variable-length instruction support
- **Scaffold Generator**: Automated ISA creation tool

Key topics covered:
- Basic ISA structure and configuration
- Instruction definition and encoding
- Register and operand formatting
- Custom directive implementation
- Pseudo-instruction support
- Variable length instruction configuration
- Testing and validation

## Contributing

We welcome contributions! Please see the [Contributing Guide](contributing.md) for development setup, coding standards, and submission guidelines.

## Development Journey

For a detailed account of the project's development history, challenges faced, and solutions implemented, see the [Development Journey](DEVELOPMENT_JOURNEY.md) document. This chronicles the evolution of py-isa-xform from initial concept to the robust toolkit it is today.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **ZX16 ISA**: Designed by Dr. Mohamed Shalan, Professor at AUC
- **Open Source**: Built on the shoulders of many excellent open source projects 