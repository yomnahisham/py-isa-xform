# ~xform (py-isa-xform)

A comprehensive ISA (Instruction Set Architecture) transformation toolkit that provides robust assembler and disassembler capabilities for custom instruction sets. This project enables the creation of custom processors and their associated toolchains for educational purposes, research, and rapid prototyping of novel architectures.

## Overview

xform serves as a foundation for building custom instruction set architectures and their corresponding development tools. The toolkit provides a complete pipeline from ISA specification to code compilation and analysis, making it suitable for computer architecture education, research projects, and EDA tool integration.

### Key Capabilities

- **ISA Definition System**: Define custom instruction set architectures using a flexible JSON-based specification format
- **Custom Instruction Implementations**: Write actual Python code to define instruction behavior and semantics
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
│   │   │   ├── isa_scaffold.py        # ISA scaffold generator
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

**See the [Custom ISA Definition Guide](ISA_DEFINITION_GUIDE.md) for how to write your own ISA!**

### Supported ISAs
- **Simple RISC**: Basic RISC-style instruction set for educational purposes
- **RISC-V RV32I**: Base integer instruction set for RISC-V 32-bit processors
- **Modular Example**: Demonstrates modular ISA design patterns
- **ZX16**: Open-Source ISA by Dr. Mohamed Shalan (Professor @ AUC), which initially inspired this project.

### Creating Your Own ISA

We provide a powerful tool to help you create custom ISAs:

#### ISA Scaffold Generator
Automatically generates boilerplate ISA definitions with implementations for common instruction types:

```bash
# Generate a basic ISA
python3 -m isa_xform.core.isa_scaffold --name "MY_ISA" --instructions "ADD,SUB,LI,J,ECALL" --directives ".org,.word,.byte"

# Generate a comprehensive ISA
python3 -m isa_xform.core.isa_scaffold --name "ADVANCED_ISA" \
  --instructions "ADD,SUB,AND,OR,XOR,ADDI,ANDI,ORI,XORI,LI,J,JAL,BEQ,BNE,LW,SW,ECALL" \
  --directives ".org,.word,.byte,.ascii,.align" \
  --word-size 16 \
  --instruction-size 16
```

**See the [ISA Creation Guide](docs/isa-creation-guide.md) for detailed instructions and examples!**

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

### Custom Instruction Implementations
- **Python Code Semantics**: Write actual Python code to define instruction behavior
- **Sandboxed Execution**: Safe execution environment with controlled access to system resources
- **Helper Functions**: Built-in functions for register access, memory operations, and flag management
- **Automatic Compilation**: Custom implementations are compiled and validated when loading ISA definitions
- **Seamless Integration**: Custom instructions work with assembler, disassembler, and simulator

## Documentation

Comprehensive documentation is available in the `docs/` directory. The following are the main docs for understanding project structure:

- **[Architecture Overview](docs/architecture.md)** - System design and component interaction
- **[Custom ISA Definition Guide](ISA_DEFINITION_GUIDE.md)** - Step-by-step instructions for writing your own ISA JSON
- **[ISA Creation Guide](docs/isa-creation-guide.md)** - Using the scaffold generator and standard template
- **[CLI Reference](docs/cli.md)** - Command-line interface usage
- **[Testing Guide](docs/testing.md)** - Testing framework and examples
- **[API Reference](docs/api-reference.md)** - Complete programming interface documentation
- **[Getting Started Tutorial](docs/getting-started.md)** - Step-by-step introduction
- **[Contributing Guide](docs/contributing.md)** - Guidelines for contributors

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

### Custom Instruction Example
```json
{
  "mnemonic": "MULT",
  "description": "Multiply registers (custom instruction)",
  "syntax": "MULT rd, rs2",
  "implementation": "# Custom multiplication\nrd_val = read_register(operands['rd'])\nrs2_val = read_register(operands['rs2'])\nresult = (rd_val * rs2_val) & 0xFFFF\nwrite_register(operands['rd'], result)\nset_flag('Z', result == 0)",
  "encoding": {
    "fields": [
      {"name": "funct4", "bits": "15:12", "value": "1111"},
      {"name": "rs2", "bits": "11:9", "type": "register"},
      {"name": "rd", "bits": "8:6", "type": "register"},
      {"name": "func3", "bits": "5:3", "value": "000"},
      {"name": "opcode", "bits": "2:0", "value": "000"}
    ]
  }
}
```

```assembly
# Using custom MULT instruction
    MULT a0, a1        # a0 = a0 * a1 (custom instruction)
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

## Development and Local CLI Usage

If you are developing or testing changes to the CLI or core modules, make sure to run the CLI with the local source by setting the `PYTHONPATH` environment variable:

```sh
PYTHONPATH=src python3 -m isa_xform.cli <command> [options]
```

This ensures that your changes in the `src/` directory are used, rather than any installed version of the package.

For example:

```sh
PYTHONPATH=src python3 -m isa_xform.cli validate --isa src/isa_definitions/simple_risc.json
```

The `--isa` argument now accepts both ISA names (for built-in ISAs) and file paths (for custom or temporary ISAs).
