# py-isa-xform Documentation

Comprehensive documentation for the py-isa-xform toolkit, a professional-grade system for creating, analyzing, and working with custom instruction set architectures (ISAs). This documentation provides complete guides for all aspects of the system.

## Overview

py-isa-xform is a professional-grade toolkit designed for educators, researchers, and developers working with custom instruction set architectures. It provides a complete ecosystem for ISA development, from specification to implementation, with particular emphasis on the ZX16 16-bit RISC-V inspired instruction set architecture.

### Key Features

- **ISA-Agnostic Design**: Works with any custom instruction set architecture
- **Complete Assembly Toolchain**: Parse, assemble, and disassemble with full symbol support
- **Comprehensive Error Handling**: Detailed error reporting with context and suggestions
- **Configurable Syntax**: Adaptable to different assembly language conventions
- **Professional Quality**: Production-ready code with extensive testing and documentation
- **ZX16 Implementation**: Complete 16-bit RISC-V inspired ISA with comprehensive test suite
- **Correct Disassembly**: Operand ordering matches assembly syntax, not encoding order

### Core Components

1. **ISA Definition System**: JSON-based architecture specification with validation
2. **Assembly Parser**: Converts assembly language to structured AST representation
3. **Assembler**: Transforms assembly code into binary machine code with pseudo-instruction support
4. **Disassembler**: Converts machine code back to human-readable assembly with correct operand ordering
5. **Symbol Table Management**: Handles labels, constants, and memory references
6. **Bit Utilities**: Low-level operations for instruction encoding and decoding
7. **Error Handling**: Comprehensive error management with detailed reporting
8. **Command-Line Interface**: Unified access to all functionality

## Getting Started

### Quick Installation

```bash
git clone https://github.com/yomnahisham/py-isa-xform.git
cd py-isa-xform
pip install -e .
```

### Basic Usage with ZX16

```bash
# Assemble ZX16 program
python3 -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin

# Disassemble to verify
python3 -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program_dis.s
```

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

## Documentation Structure

### Core Guides

| Document | Description |
|----------|-------------|
| **[Getting Started](getting-started.md)** | Installation, basic usage, and first steps with ZX16 |
| **[Architecture Overview](architecture.md)** | System design and component interactions |
| **[API Reference](api-reference.md)** | Complete API documentation |

### Component Documentation

| Component | Documentation | Description |
|-----------|---------------|-------------|
| **ISA Loader** | [isa_loader.md](isa_loader.md) | Loading and validating ISA definitions |
| **Parser** | [parser.md](parser.md) | Assembly language parsing and AST generation |
| **Assembler** | [assembler.md](assembler.md) | Converting assembly to machine code |
| **Disassembler** | [disassembler.md](disassembler.md) | Converting machine code to assembly |
| **Symbol Table** | [symbol_table.md](symbol_table.md) | Symbol management and resolution |
| **Bit Utils** | [bit-utils.md](bit-utils.md) | Low-level bit manipulation utilities |
| **Error Handling** | [error-handling.md](error-handling.md) | Comprehensive error management |

### Reference Materials

| Document | Description |
|----------|-------------|
| **[ISA Definition Format](isa-definition.md)** | Complete specification for ISA JSON format |
| **[CLI Guide](cli.md)** | Command-line interface reference |
| **[Testing Guide](testing.md)** | Testing strategies and frameworks |
| **[Contributing](contributing.md)** | Development setup and contribution guidelines |

## ZX16 Instruction Set Architecture

### Overview
ZX16 is a 16-bit RISC-V inspired instruction set architecture designed for educational and embedded applications. It features a compact instruction encoding with comprehensive support for arithmetic, logical, control flow, and system operations.

### Key Characteristics
- **16-bit Instructions**: Compact encoding suitable for embedded applications
- **8 General-Purpose Registers**: x0-x7 with standard aliases (t0, ra, sp, s0, s1, t1, a0, a1)
- **7-bit Signed Immediates**: Immediate values in range -64 to 63
- **Multiple ECALL Services**: System call support for I/O and program control
- **Professional Toolchain**: Complete assembly and disassembly support

### Instruction Categories

#### Arithmetic and Logical Operations
- **ADD, SUB**: Register arithmetic operations
- **ADDI**: Immediate arithmetic operations
- **AND, OR, XOR**: Bitwise logical operations
- **SLT, SLTU**: Comparison operations (signed/unsigned)
- **SLL, SRL, SRA**: Shift operations (logical/arithmetic)
- **MV**: Register move operations

#### Control Flow Operations
- **BEQ, BNE**: Conditional branching (equal/not equal)
- **BZ, BNZ**: Conditional branching (zero/not zero)
- **J**: Unconditional jump

#### System Operations
- **ECALL**: System call with multiple service numbers
  - `0x000`: Print character
  - `0x001`: Read character
  - `0x002`: Print string
  - `0x3FF`: Exit program

### Test Cases
Comprehensive test cases are available in `tests/TC-ZX16/`:
- **test_arithmetic.s**: Demonstrates all arithmetic and logical operations
- **test_ecall.s**: Validates system call services
- **test_branching.s**: Tests control flow operations

## Features Overview

### ISA Definition System

Define custom instruction set architectures using comprehensive JSON specifications:

```json
{
  "name": "ZX16",
  "version": "1.0",
  "description": "ZX16 16-bit RISC-V inspired ISA",
  "instruction_size": 16,
  "word_size": 16,
  "endianness": "little",
  "registers": {
    "general_purpose": [
      {"name": "x0", "size": 16, "alias": ["t0"], "description": "Temporary"},
      {"name": "x6", "size": 16, "alias": ["a0"], "description": "Argument 0/Return value"}
    ]
  },
  "instructions": [
    {
      "mnemonic": "ADD",
      "format": "R-type",
      "syntax": "ADD rd, rs2",
      "semantics": "rd = rd + rs2",
      "encoding": {
        "fields": [
          {"name": "funct4", "bits": "15:12", "value": "0000"},
          {"name": "rs2", "bits": "11:9", "type": "register"},
          {"name": "rd", "bits": "8:6", "type": "register"}
        ]
      }
    }
  ]
}
```

### Assembly Processing

Complete assembly toolchain with advanced features:

- **Configurable Syntax**: Adapts to ISA-specific assembly language conventions
- **Symbol Resolution**: Handles forward references and complex symbol dependencies
- **Directive Support**: Standard and custom assembly directives
- **Error Reporting**: Detailed error messages with file, line, and column information
- **Pseudo-Instruction Expansion**: Automatic handling of high-level constructs
- **Immediate Validation**: Proper handling of immediate value constraints

### Machine Code Generation

Professional-grade assembler with advanced features:

- **Two-Pass Assembly**: Resolves forward references automatically
- **Field-Based Encoding**: Supports modern ISA encoding schemes
- **Validation**: Comprehensive operand and instruction validation
- **Optimization**: Efficient assembly for large programs
- **Register Validation**: Ensures only valid registers are used

### Disassembly Capabilities

Intelligent disassembler with advanced analysis:

- **Pattern Recognition**: Flexible instruction pattern matching
- **Data Detection**: Automatically identifies code vs. data sections
- **Symbol Generation**: Creates meaningful labels for jump targets
- **Multiple Formats**: Various output formatting options
- **Correct Operand Ordering**: Outputs operands in syntax order, not encoding order

### Error Management

Comprehensive error handling system:

- **Error Collection**: Batch multiple errors for complete validation
- **Context Information**: File, line, column, and source context
- **Suggestions**: Helpful hints for error resolution
- **Error Types**: Specific exception classes for different error categories
- **Immediate Validation**: Proper handling of immediate value constraints

## Use Cases

### Educational Applications

- **Computer Architecture Courses**: Teach ISA design and assembly programming with ZX16
- **Processor Design**: Support FPGA and ASIC processor implementations
- **Assembly Language Learning**: Practice with custom instruction sets
- **Compiler Design**: Understand instruction set architecture design principles

### Research Applications

- **ISA Experimentation**: Rapid prototyping of new instruction set features
- **Compiler Backends**: Generate assembly for research compilers
- **Architecture Analysis**: Study instruction set characteristics and performance
- **Custom Processor Design**: Develop specialized instruction sets

### Professional Development

- **Custom Processors**: Support embedded and specialized processors
- **Tool Development**: Build development tools for custom architectures
- **System Integration**: Interface with simulation and testing frameworks
- **Educational Tools**: Create interactive learning environments

## Examples and Test Cases

The project includes comprehensive examples and test cases:

### ZX16 Test Suite
Located in `tests/TC-ZX16/`:
- **Arithmetic Operations**: Complete coverage of arithmetic and logical instructions
- **System Services**: ECALL service validation and testing
- **Control Flow**: Branching and jump instruction testing
- **Documentation**: Detailed README explaining test coverage and validation

### Example Programs
Located in `examples/`:
- **Basic Programs**: Simple assembly language examples
- **Complex Programs**: Advanced usage demonstrations
- **Integration Examples**: Toolchain integration scenarios

## Recent Improvements

- **Operand Order Fix**: Disassembler now outputs operands in correct syntax order
- **ZX16 Implementation**: Complete 16-bit RISC-V inspired ISA
- **Enhanced Error Handling**: Improved error messages and validation
- **Professional Documentation**: Comprehensive and detailed documentation
- **Test Coverage**: Extensive test cases demonstrating all ISA features
- **Pseudo-Instruction Support**: Automatic expansion of high-level constructs

## Support and Contributing

- **Documentation**: Comprehensive guides for all system components
- **Testing**: Extensive test coverage for validation and regression testing
- **Contributing**: Detailed guidelines for contributors and developers
- **Issues**: Professional issue tracking and resolution process

This documentation provides a complete reference for using py-isa-xform in educational, research, and professional development contexts.
