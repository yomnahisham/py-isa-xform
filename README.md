# py-isa-xform (AKA ~xform)

A comprehensive ISA (Instruction Set Architecture) transformation toolkit that provides robust assembler and disassembler capabilities for custom instruction sets. This project enables the creation of custom processors and their associated toolchains for educational purposes, research, and rapid prototyping of novel architectures.

## Overview

xform serves as a foundation for building custom instruction set architectures and their corresponding development tools. The toolkit provides a complete pipeline from ISA specification to code compilation and analysis, making it suitable for computer architecture education, research projects, and EDA tool integration.

### Key Capabilities

- **ISA Definition System**: Define custom instruction set architectures using a flexible JSON-based specification format
- **Assembly Engine**: Convert human-readable assembly code to machine code with comprehensive error reporting
- **Disassembly Engine**: Reverse machine code back to assembly language with symbol reconstruction and correct operand ordering
- **Extensible Parser**: Support for custom assembly syntaxes and addressing modes
- **Symbol Management**: Advanced symbol table handling for labels, constants, and memory references
- **Pseudo-Instruction Support**: Automatic expansion of high-level assembly constructs
- **Multiple ISA Support**: Built-in support for various instruction set architectures
- **Professional Toolchain**: Command-line interface suitable for integration into development workflows

## Project Structure

```
py-isa-xform/
├── src/
│   ├── isa_xform/
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── isa_loader.py          # Loads ISA definitions
│   │   │   ├── parser.py              # Parses assembly text
│   │   │   ├── assembler.py           # Assembly engine
│   │   │   ├── disassembler.py        # Disassembly engine
│   │   │   ├── symbol_table.py        # Manages labels/symbols
│   │   │   ├── directive_handler.py   # Handles assembly directives
│   │   │   └── operand_parser.py      # Operand parsing and validation
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── bit_utils.py           # Bit manipulation utilities
│   │   │   └── error_handling.py      # Error classes and handling
│   │   └── cli.py                     # Command-line interface
│   └── isa_definitions/               # Built-in ISA configurations
│       ├── zx16.json                  # ZX16 16-bit RISC-V inspired ISA
│       ├── simple_risc.json           # Simple RISC instruction set
│       ├── riscv_rv32i.json           # RISC-V RV32I base integer ISA
│       ├── modular_example.json       # Modular ISA example
│       └── crazy_isa.json             # Experimental ISA definition
├── tests/
│   ├── TC-ZX16/                       # ZX16 test cases
│   │   ├── test_arithmetic.s          # Comprehensive arithmetic operations
│   │   ├── test_ecall.s               # System call services
│   │   ├── test_branching.s           # Control flow operations
│   │   └── README.md                  # Test documentation
│   └── [other test directories]
├── examples/                          # Example programs and demonstrations
├── docs/                              # Comprehensive documentation
├── setup.py
├── requirements.txt
└── README.md
```

## Installation and Setup

### Requirements
- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

### Installation
```bash
git clone https://github.com/yomnahisham/py-isa-xform.git
cd py-isa-xform
pip install -r requirements.txt
pip install -e .
```

### Basic Usage
```bash
# Assemble code for ZX16 ISA
python3 -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin

# Disassemble machine code
python3 -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s

# Assemble with verbose output
python3 -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin --verbose

# List available ISAs
python3 -m isa_xform.cli list-isas
```

## Supported Instruction Set Architectures

### ZX16 (Primary Implementation)
A 16-bit RISC-V inspired instruction set architecture featuring:
- **8 General-Purpose Registers**: x0-x7 with aliases (t0, ra, sp, s0, s1, t1, a0, a1)
- **16-bit Instructions**: Compact encoding for embedded applications
- **Comprehensive Instruction Set**: Arithmetic, logical, control flow, and system operations
- **System Services**: Multiple ECALL services for I/O and program control
- **Immediate Constraints**: 7-bit signed immediate values (-64 to 63)
- **Professional Toolchain**: Complete assembly and disassembly support

### Other Supported ISAs
- **Simple RISC**: Basic RISC-style instruction set for educational purposes
- **RISC-V RV32I**: Base integer instruction set for RISC-V 32-bit processors
- **Modular Example**: Demonstrates modular ISA design patterns
- **ZX16**: Open-Source ISA by Dr. Mohamed Shalan (Professor @ AUC), which initially inspired this project.

## Key Features

### Assembly Engine
- **Syntax Validation**: Comprehensive error checking and reporting
- **Pseudo-Instruction Expansion**: Automatic handling of high-level constructs
- **Symbol Resolution**: Advanced label and constant management
- **Immediate Validation**: Proper handling of immediate value constraints
- **Register Validation**: Ensures only valid registers are used

### Disassembly Engine
- **Correct Operand Ordering**: Outputs operands in syntax order, not encoding order
- **Symbol Reconstruction**: Rebuilds labels and symbols from machine code
- **Instruction Recognition**: Robust pattern matching for instruction identification
- **Professional Output**: Clean, readable assembly code generation

### ISA Definition System
- **JSON-Based Configuration**: Human-readable ISA specifications
- **Flexible Field Definitions**: Support for various instruction formats
- **Register Configuration**: Comprehensive register set definitions
- **Syntax Specification**: Customizable assembly language syntax
- **Validation Rules**: Built-in validation for ISA definitions

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Architecture Overview](docs/architecture.md)** - System design and component interaction
- **[ISA Definition Guide](docs/isa-definition.md)** - Creating custom instruction set architectures
- **[Parser Documentation](docs/parser.md)** - Assembly language parsing and AST generation
- **[Symbol Table Guide](docs/symbol_table.md)** - Label and symbol management
- **[CLI Reference](docs/cli.md)** - Command-line interface usage
- **[Testing Guide](docs/testing.md)** - Testing framework and examples
- **[API Reference](docs/api-reference.md)** - Complete programming interface documentation
- **[Getting Started Tutorial](docs/getting-started.md)** - Step-by-step introduction
- **[Contributing Guide](docs/contributing.md)** - Guidelines for contributors
- **[Error Handling](docs/error-handling.md)** - Error reporting and debugging
- **[Bit Utilities](docs/bit-utils.md)** - Bit manipulation and encoding utilities

## Example Usage

### ZX16 Assembly Example
```assembly
# ZX16 Arithmetic Operations
    .text
    .globl main

main:
    LI a0, 10          # Load immediate value
    LI a1, 5           # Load immediate value
    ADD a0, a1         # Add registers: a0 = a0 + a1
    SUB a0, a1         # Subtract registers: a0 = a0 - a1
    ADDI a0, 20        # Add immediate: a0 = a0 + 20
    ECALL 0x3FF        # Exit program
```

### Assembly and Disassembly
```bash
# Assemble the program
python3 -m isa_xform.cli assemble --isa zx16 --input example.s --output example.bin

# Disassemble to verify
python3 -m isa_xform.cli disassemble --isa zx16 --input example.bin --output example_dis.s
```

## Development Status

The project is actively developed with a focus on modularity, extensibility, and comprehensive testing. The current implementation provides a complete foundation for ISA definition and basic assembly/disassembly operations, with ongoing work on advanced optimization features and expanded ISA support.

## Contributing

Contributions are welcome and encouraged! Please refer to the [Contributing Guide](docs/contributing.md) for guidelines on:
- Code style and formatting requirements
- Testing requirements and procedures
- Documentation standards
- Development workflow and pull request process

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/yomnahisham/py-isa-xform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yomnahisham/py-isa-xform/discussions)
- **Documentation**: [Project Documentation](docs/)

## Acknowledgments

This project is designed for educational and research purposes in computer architecture and compiler design. It provides a foundation for understanding instruction set architecture design and implementation.
