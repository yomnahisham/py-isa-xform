# xform

A comprehensive ISA (Instruction Set Architecture) transformation toolkit that provides robust assembler and disassembler capabilities for custom instruction sets. This project enables the creation of custom processors and their associated toolchains for educational purposes, research, and rapid prototyping of novel architectures.

## Overview

xform serves as a foundation for building custom instruction set architectures and their corresponding development tools. The toolkit provides a complete pipeline from ISA specification to code compilation and analysis, making it suitable for computer architecture education, research projects, and EDA tool integration.

### Key Capabilities

- **ISA Definition System**: Define custom instruction set architectures using a flexible JSON-based specification format
- **Assembly Engine**: Convert human-readable assembly code to machine code with comprehensive error reporting
- **Disassembly Engine**: Reverse machine code back to assembly language with symbol reconstruction
- **Extensible Parser**: Support for custom assembly syntaxes and addressing modes
- **Symbol Management**: Advanced symbol table handling for labels, constants, and memory references
- **EDA Integration**: Designed for seamless integration with electronic design automation workflows

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
│   │   │   └── symbol_table.py        # Manages labels/symbols
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── bit_utils.py           # Bit manipulation
│   │   │   └── error_handling.py      # Error classes
│   │   └── cli.py                     # Command-line interface
│   └── isa_definitions/               # Built-in ISA configs
│       ├── simple_risc.json
│       └── risc_v_rv32i.json
├── tests/
├── examples/
├── docs/
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
# Assemble code for a specific ISA
isa-xform assemble --isa simple_risc --input program.s --output program.bin

# Disassemble machine code
isa-xform disassemble --isa simple_risc --input program.bin --output program.s

# Validate an ISA definition
isa-xform validate --isa-file custom_isa.json
```

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

### Additional Documentation

- **[Contributing Guide](docs/contributing.md)** - Guidelines for contributors

## Example ISAs

The project includes several reference implementations of well-known instruction set architectures:

- **Simple RISC**: Basic RISC-style instruction set for educational purposes
- **RISC-V RV32I**: Base integer instruction set for RISC-V 32-bit processors

These examples serve as both functional references and templates for creating custom ISAs.

## Development Status

The project is actively developed with a focus on modularity, extensibility, and comprehensive testing. The current implementation provides a complete foundation for ISA definition and basic assembly/disassembly operations, with ongoing work on advanced optimization features and expanded ISA support.

## Contributing

Contributions are welcome and encouraged! Please refer to the [Contributing Guide](docs/contributing.md) for guidelines on code style, testing requirements, and the development workflow.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/yomnahisham/py-isa-xform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yomnahisham/py-isa-xform/discussions)
- **Documentation**: [Project Documentation](docs/)