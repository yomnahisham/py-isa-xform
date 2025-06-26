# Architecture Overview

This document provides a comprehensive overview of the py-isa-xform system architecture, including design principles, component interactions, and implementation details.

## System Design Philosophy

py-isa-xform is designed with modularity, extensibility, and maintainability as core principles. The system architecture follows a clean separation of concerns to provide a flexible framework that can handle any instruction set architecture:

1. **ISA Definition** - Declarative specification of instruction sets using JSON
2. **Parsing Layer** - Converts assembly text to structured representations
3. **Symbol Management** - Handles labels, constants, and memory references
4. **Validation System** - Ensures correctness and consistency at every step
5. **Command-Line Interface** - Provides unified access to all functionality

## Core Components

### 1. ISA Definition System (`src/isa_xform/core/isa_loader.py`)

The foundation of the entire system that provides the infrastructure for defining and validating instruction set architectures.

**Key Responsibilities:**
- Load ISA definitions from JSON files
- Validate ISA specifications for completeness and consistency
- Provide standardized internal representation of ISAs
- Support extensible instruction and addressing mode definitions

**Key Classes:**
- `ISADefinition` - Main ISA specification container with metadata
- `Instruction` - Individual instruction specification with operands and encoding
- `Operand` - Operand specification with type, size, and position information
- `Register` - Register definitions with size and description
- `AddressingMode` - Addressing mode specifications

**Data Flow:**
```
JSON File → JSON Parser → Validation → ISADefinition Object
```

### 2. Assembly Parser (`src/isa_xform/core/parser.py`)

Converts human-readable assembly code into structured Abstract Syntax Tree (AST) representations.

**Key Responsibilities:**
- Parse assembly source files line by line
- Generate AST nodes for different assembly constructs
- Handle labels, instructions, directives, and comments
- Provide detailed error reporting with line and column information

**Key Classes:**
- `Parser` - Main parsing engine with ISA-aware parsing
- `ASTNode` - Base class for all AST nodes
- `LabelNode` - Represents label definitions
- `InstructionNode` - Represents assembly instructions
- `DirectiveNode` - Represents assembler directives
- `CommentNode` - Represents comments

**Parsing Process:**
```
Assembly Text → Line Tokenization → AST Node Creation → AST List
```

### 3. Symbol Table Management (`src/isa_xform/core/symbol_table.py`)

Manages symbols, labels, and their values during the assembly process.

**Key Responsibilities:**
- Track symbol definitions and their memory addresses
- Resolve forward references and symbol dependencies
- Handle different symbol types (labels, constants, data)
- Provide symbol lookup and validation services

**Key Classes:**
- `SymbolTable` - Main symbol management container
- `Symbol` - Individual symbol representation with metadata

**Symbol Resolution Process:**
```
AST Nodes → Symbol Extraction → Address Assignment → Symbol Table
```

### 4. Command-Line Interface (`src/isa_xform/cli.py`)

Provides a unified command-line interface for all py-isa-xform operations.

**Key Responsibilities:**
- Parse command-line arguments and options
- Dispatch commands to appropriate handlers
- Provide user-friendly error messages and help
- Support multiple input/output formats

**Supported Commands:**
- `validate` - Validate ISA definition files
- `parse` - Parse assembly code and display AST
- `assemble` - Convert assembly to machine code (future)
- `disassemble` - Convert machine code to assembly (future)

### 5. Utilities (`src/isa_xform/utils/`)

Common utilities and helper functions used throughout the system.

**Key Components:**
- `error_handling.py` - Custom exception classes and error handling
- Error reporting with detailed context information
- Consistent error message formatting

## System Data Flow

### Assembly Parsing Flow

```
Assembly File → Parser → AST Nodes → Symbol Table → Validated Output
     ↓              ↓         ↓           ↓              ↓
  Text Input   Line-by-Line  Structured  Symbol        Final
              Tokenization   AST         Resolution    Result
```

### ISA Definition Flow

```
JSON File → ISA Loader → Validation → ISADefinition → Parser/CLI
    ↓           ↓           ↓            ↓              ↓
  Raw JSON   JSON Parse   Rules Check   Validated      Available
             & Load       & Validate    Object         for Use
```

## ISA Definition Format

ISAs are defined using a structured JSON format that specifies all aspects of the instruction set architecture:

```json
{
  "name": "SimpleRISC",
  "description": "A simple RISC-style instruction set for educational purposes",
  "word_size": 32,
  "endianness": "little",
  "registers": {
    "r0": {"name": "r0", "bits": 32, "description": "Zero register"},
    "r1": {"name": "r1", "bits": 32, "description": "General purpose register 1"}
  },
  "instructions": {
    "add": {
      "name": "add",
      "opcode": 0,
      "format": "R",
      "operands": [
        {"name": "rd", "type": "register", "bits": 4, "position": 0, "addressing_mode": "register"},
        {"name": "rs1", "type": "register", "bits": 4, "position": 4, "addressing_mode": "register"},
        {"name": "rs2", "type": "register", "bits": 4, "position": 8, "addressing_mode": "register"}
      ],
      "encoding": {"opcode": 0, "funct": 0},
      "description": "Add two registers and store result in destination register"
    }
  },
  "addressing_modes": {
    "register": {
      "name": "register",
      "description": "Register addressing mode",
      "format": "R"
    }
  }
}
```

## Future Architecture Enhancements

### Planned Features
- **Assembler Engine**: Complete assembly to machine code conversion
- **Disassembler Engine**: Machine code to assembly conversion
- **Optimization Passes**: Code optimization during assembly
- **Debugging Support**: Debug symbol generation and handling

### Long-term Vision
- **Higher-level Language Support**: C-like syntax compilation
- **Simulation Integration**: Direct integration with simulation engines

## Conclusion

The py-isa-xform architecture provides a solid foundation for building custom instruction set architectures and their associated development tools. The modular design ensures extensibility while maintaining simplicity and reliability. The comprehensive error handling and validation systems ensure robust operation across a wide range of use cases.

The architecture is designed to grow with the project, supporting both current educational and research needs while providing clear paths for future enhancements and integrations. 