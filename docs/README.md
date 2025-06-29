# py-isa-xform Documentation

A comprehensive toolkit for creating, analyzing, and working with custom instruction set architectures (ISAs). This documentation provides complete guides for all aspects of the system.

## Overview

py-isa-xform is a professional-grade toolkit designed for educators, researchers, and developers working with custom instruction set architectures. It provides a complete ecosystem for ISA development, from specification to implementation.

### Key Features

- **ISA-Agnostic Design**: Works with any custom instruction set architecture
- **Complete Assembly Toolchain**: Parse, assemble, and disassemble with full symbol support
- **Comprehensive Error Handling**: Detailed error reporting with context and suggestions
- **Configurable Syntax**: Adaptable to different assembly language conventions
- **Professional Quality**: Production-ready code with extensive testing and documentation

### Core Components

1. **ISA Definition System**: JSON-based architecture specification with validation
2. **Assembly Parser**: Converts assembly language to structured AST representation
3. **Assembler**: Transforms assembly code into binary machine code
4. **Disassembler**: Converts machine code back to human-readable assembly
5. **Symbol Table Management**: Handles labels, constants, and memory references
6. **Bit Utilities**: Low-level operations for instruction encoding and decoding
7. **Error Handling**: Comprehensive error management with detailed reporting
8. **Command-Line Interface**: Unified access to all functionality

## Getting Started

### Quick Installation

```bash
git clone https://github.com/your-org/py-isa-xform.git
cd py-isa-xform
pip install -e .
```

### Basic Usage

```python
from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.parser import Parser
from isa_xform.core.assembler import Assembler

# Load ISA definition
loader = ISALoader()
isa_def = loader.load_isa("simple_risc")

# Parse assembly code
parser = Parser(isa_def)
nodes = parser.parse("""
start:
    ADD $r1, $r2, $r3
    JMP end
end:
    NOP
""")

# Assemble to machine code
assembler = Assembler(isa_def)
result = assembler.assemble(nodes)
print(f"Generated {len(result.machine_code)} bytes")
```

### Command Line Usage

```bash
# Validate ISA definition
python -m isa_xform validate my_isa.json

# Assemble program
python -m isa_xform assemble --isa simple_risc program.s

# Disassemble binary
python -m isa_xform disassemble --isa simple_risc program.bin
```

## Documentation Structure

### Core Guides

| Document | Description |
|----------|-------------|
| **[Getting Started](getting-started.md)** | Installation, basic usage, and first steps |
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

## Features Overview

### ISA Definition System

Define custom instruction set architectures using comprehensive JSON specifications:

```json
{
  "name": "CustomISA",
  "version": "1.0",
  "word_size": 32,
  "endianness": "little",
  "instruction_size": 32,
  "assembly_syntax": {
    "comment_char": ";",
    "register_prefix": "$",
    "immediate_prefix": "#"
  },
  "instructions": [
    {
      "mnemonic": "ADD",
      "opcode": "0001",
      "encoding": {
        "fields": [
          {"name": "opcode", "bits": "31:28", "value": "0001"},
          {"name": "rd", "bits": "27:24", "type": "register"}
        ]
      }
    }
  ]
}
```

### Assembly Processing

Complete assembly toolchain with two-pass assembly support:

- **Configurable Syntax**: Adapts to ISA-specific assembly language conventions
- **Symbol Resolution**: Handles forward references and complex symbol dependencies
- **Directive Support**: Standard and custom assembly directives
- **Error Reporting**: Detailed error messages with file, line, and column information

### Machine Code Generation

Professional-grade assembler with advanced features:

- **Two-Pass Assembly**: Resolves forward references automatically
- **Field-Based Encoding**: Supports modern ISA encoding schemes
- **Validation**: Comprehensive operand and instruction validation
- **Optimization**: Efficient assembly for large programs

### Disassembly Capabilities

Intelligent disassembler with advanced analysis:

- **Pattern Recognition**: Flexible instruction pattern matching
- **Data Detection**: Automatically identifies code vs. data sections
- **Symbol Generation**: Creates meaningful labels for jump targets
- **Multiple Formats**: Various output formatting options

### Error Management

Comprehensive error handling system:

- **Error Collection**: Batch multiple errors for complete validation
- **Context Information**: File, line, column, and source context
- **Suggestions**: Helpful hints for error resolution
- **Error Types**: Specific exception classes for different error categories

## Use Cases

### Educational Applications

- **Computer Architecture Courses**: Teach ISA design and assembly programming
- **Processor Design**: Support FPGA and ASIC processor implementations
- **Assembly Language Learning**: Practice with custom instruction sets

### Research Applications

- **ISA Experimentation**: Rapid prototyping of new instruction set features
- **Compiler Backends**: Generate assembly for research compilers
- **Architecture Analysis**: Study instruction set characteristics

### Professional Development

- **Custom Processors**: Support embedded and specialized processors
- **Tool Development**: Build development tools for custom architectures
- **System Integration**: Interface with simulation and testing frameworks

## Examples

The `examples/` directory contains complete test cases demonstrating various features:

- **TC001**: Basic assembly and disassembly workflow
- **TC002**: Advanced symbol resolution and debugging
- **TC003**: Minimal ISA implementation
- **TC004**: Complex instruction encoding examples

Each test case includes:
- Source assembly files
- Expected binary output
- Disassembly verification
- Documentation explaining the concepts demonstrated

## Architecture

py-isa-xform follows a modular architecture with clean component separation:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ISA Loader    │    │     Parser      │    │   Assembler     │
│                 │    │                 │    │                 │
│ • Load ISAs     │───▶│ • Parse ASM     │───▶│ • Generate Code │
│ • Validate      │    │ • Create AST    │    │ • Resolve Syms  │
│ • Configure     │    │ • Handle Syntax │    │ • Encode Instrs │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Error Handling  │    │ Symbol Table    │    │  Disassembler   │
│                 │    │                 │    │                 │
│ • Error Types   │    │ • Track Symbols │    │ • Decode Binary │
│ • Context Info  │    │ • Resolve Refs  │    │ • Extract Syms  │
│ • Suggestions   │    │ • Handle Scopes │    │ • Format Output │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────┐
                    │   Bit Utils     │
                    │                 │
                    │ • Bit Fields    │
                    │ • Sign Extend   │
                    │ • Alignment     │
                    │ • Endianness    │
                    └─────────────────┘
```

## Quality Assurance

### Testing

- **Unit Tests**: Comprehensive coverage of all components
- **Integration Tests**: End-to-end workflow validation
- **Property-Based Testing**: Random input validation
- **Performance Testing**: Scalability and efficiency verification

### Documentation

- **API Reference**: Complete documentation of all public interfaces
- **User Guides**: Step-by-step tutorials and examples
- **Architecture Docs**: System design and implementation details
- **Code Examples**: Practical usage demonstrations

### Error Handling

- **Comprehensive Validation**: Input validation at all levels
- **Graceful Degradation**: Robust handling of malformed input
- **Clear Error Messages**: Detailed context and suggestions
- **Error Recovery**: Continue processing when possible

## Performance

### Scalability

- **Large Programs**: Handles programs with millions of instructions
- **Complex ISAs**: Supports architectures with thousands of instructions
- **Memory Efficiency**: Linear memory usage with program size
- **Batch Processing**: Efficient handling of multiple files

### Optimization

- **Caching**: ISA definitions and lookup tables are cached
- **Streaming**: Large files processed in chunks
- **Parallel Processing**: Independent operations can run concurrently
- **Efficient Algorithms**: Optimized for common operations

## Community and Support

### Getting Help

1. **Documentation**: Start with the guides in this directory
2. **Examples**: Study the test cases in `examples/`
3. **API Reference**: Check the complete API documentation
4. **Issues**: Report bugs and request features on GitHub

### Contributing

We welcome contributions! See the [Contributing Guide](contributing.md) for:

- Development setup instructions
- Code style guidelines
- Testing requirements
- Pull request process

### License

This project is licensed under the MIT License. See the LICENSE file for details.

## Roadmap

### Current Version (1.0)

- Complete ISA definition system
- Full assembly and disassembly pipeline
- Comprehensive error handling
- Professional documentation

### Planned Features

- **Optimization Passes**: Code optimization during assembly
- **Debugging Support**: Debug symbol generation and handling
- **IDE Integration**: Language server protocol support
- **Advanced Analysis**: Control flow and data flow analysis

### Long-term Vision

- **Higher-level Languages**: C-like syntax compilation
- **Formal Verification**: Mathematical verification of ISA properties
- **Simulation Integration**: Direct interface with processor simulators
- **Cross-Architecture Tools**: Translation between different ISAs

---

For detailed information on any topic, please refer to the specific documentation files linked above. The [Getting Started Guide](getting-started.md) is the recommended starting point for new users.
