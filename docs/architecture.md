# Architecture Overview

This document provides a comprehensive overview of the py-isa-xform system architecture, including design principles, component interactions, and implementation details.

## System Design Philosophy

py-isa-xform is designed with modularity, extensibility, and maintainability as core principles. The system architecture follows a clean separation of concerns to provide a flexible framework that can handle any instruction set architecture:

1. **ISA Definition** - Declarative specification of instruction sets using JSON
2. **Parsing Layer** - Converts assembly text to structured representations
3. **Assembly and Disassembly** - Bidirectional conversion between assembly and machine code
4. **Symbol Management** - Handles labels, constants, and memory references
5. **Bit Manipulation** - Low-level operations for instruction encoding/decoding
6. **Error Handling** - Comprehensive error management and reporting
7. **Command-Line Interface** - Provides unified access to all functionality
8. **Simulation** - Instruction execution simulation for testing and debugging

## Core Components

### 1. ISA Definition System (`src/isa_xform/core/isa_loader.py`)

The foundation of the entire system that provides infrastructure for defining and validating instruction set architectures.

**Key Responsibilities:**
- Load ISA definitions from JSON files
- Validate ISA specifications for completeness and consistency
- Provide standardized internal representation of ISAs
- Support extensible instruction and addressing mode definitions
- Handle ISA-specific syntax configurations
- Support variable-length instruction architectures

**Key Classes:**
- `ISALoader` - Main loader for ISA definitions with validation
- `ISADefinition` - Complete ISA specification with metadata, instructions, and syntax rules
- `Instruction` - Individual instruction specification with operands and encoding
- `Register` - Register definitions with size, aliases, and descriptions
- `Directive` - Assembly directive specifications with handlers
- `AddressingMode` - Addressing mode specifications
- `AssemblySyntax` - ISA-specific syntax rules (comment chars, prefixes, etc.)
- `AddressSpace` - Memory layout and default addresses

**Data Flow:**
```
JSON File → JSON Parser → Validation → ISADefinition Object → Components
```

### 2. ISA Scaffold Generator (`src/isa_xform/core/isa_scaffold.py`)

Automatically generates ISA definitions with common instruction patterns and implementations.

**Key Responsibilities:**
- Generate complete ISA definitions from high-level specifications
- Provide templates for common instruction types (R-type, I-type, etc.)
- Include standard assembly directives and pseudo-instructions
- Support customizable register sets and instruction lists
- Generate working implementations for basic instructions

### 3. Assembly Parser (`src/isa_xform/core/parser.py`)

Converts human-readable assembly code into structured Abstract Syntax Tree (AST) representations with full ISA syntax support.

**Key Responsibilities:**
- Parse assembly source files with ISA-specific syntax rules
- Generate AST nodes for different assembly constructs
- Handle labels, instructions, directives, and comments
- Support configurable syntax (comment chars, prefixes, case sensitivity)
- Provide detailed error reporting with line and column information
- Support variable-length instruction parsing

**Key Classes:**
- `Parser` - Main parsing engine with ISA-aware syntax processing
- `ASTNode` - Base class for all AST nodes
- `LabelNode` - Represents label definitions
- `InstructionNode` - Represents assembly instructions with operands
- `DirectiveNode` - Represents assembler directives
- `CommentNode` - Represents comments
- `OperandNode` - Represents instruction operands with type information

**Parsing Process:**
```
Assembly Text → ISA Syntax Rules → Line Tokenization → AST Node Creation → AST List
```

### 4. Assembler (`src/isa_xform/core/assembler.py`)

Converts assembly language AST into binary machine code with full ISA support.

**Key Responsibilities:**
- Transform AST nodes into binary machine code
- Handle two-pass assembly for forward reference resolution
- Support field-based instruction encoding
- Process assembly directives (.org, .word, .byte, etc.)
- Validate operand values against bit field constraints
- Generate comprehensive error messages with context
- Support variable-length instruction encoding
- Generate headered binaries by default

**Key Classes:**
- `Assembler` - Main assembly engine with ISA-aware encoding
- `AssemblyContext` - Maintains state during assembly process
- `AssembledCode` - Result container with machine code and symbols

**Assembly Process:**
```
AST Nodes → Symbol Collection (Pass 1) → Code Generation (Pass 2) → Machine Code
```

### 5. Disassembler (`src/isa_xform/core/disassembler.py`)

Converts binary machine code back into human-readable assembly language with advanced features.

**Key Responsibilities:**
- Decode binary machine code using ISA instruction patterns
- Identify code vs. data sections automatically based on ISA memory layout
- Generate symbolic labels for jump targets and data references
- Support multiple instruction encoding formats
- Handle endianness and instruction size configurations
- Provide formatted output with optional addresses and machine code
- Support variable-length instruction disassembly
- Reconstruct pseudo-instructions using smart pattern matching
- Automatic data region detection

**Key Classes:**
- `Disassembler` - Main disassembly engine with pattern matching
- `DisassembledInstruction` - Individual disassembled instruction representation
- `DisassemblyResult` - Complete disassembly result with instructions and data

**Disassembly Process:**
```
Machine Code → Pattern Matching → Instruction Decode → Symbol Extraction → Assembly Text
```

### 6. Symbol Table Management (`src/isa_xform/core/symbol_table.py`)

Manages symbols, labels, and their values during assembly and disassembly processes.

**Key Responsibilities:**
- Track symbol definitions and their memory addresses
- Resolve forward references and symbol dependencies
- Handle different symbol types (labels, constants, data)
- Support multiple passes for complex symbol resolution
- Provide symbol lookup and validation services
- Generate symbol export/import capabilities
- Support label bitfield extraction (label[high:low])

**Key Classes:**
- `SymbolTable` - Main symbol management container
- `Symbol` - Individual symbol representation with metadata
- `SymbolType` - Enumeration of symbol types (label, constant, etc.)
- `SymbolScope` - Symbol scope management (local, global, external)

**Symbol Resolution Process:**
```
AST Nodes → Symbol Extraction → Address Assignment → Forward Reference Resolution → Symbol Table
```

### 7. Directive System (`src/isa_xform/core/directive_handler.py`, `src/isa_xform/core/directive_executor.py`)

Handles assembly directives and custom directive implementations.

**Key Responsibilities:**
- Process standard assembly directives (.org, .word, .byte, etc.)
- Execute custom directive implementations written in Python
- Handle directive arguments and validation
- Support data definition and memory layout directives
- Provide extensible directive system for custom ISAs

### 8. Instruction Execution (`src/isa_xform/core/instruction_executor.py`)

Executes custom instruction implementations written in Python.

**Key Responsibilities:**
- Execute Python code embedded in ISA definitions
- Provide safe execution environment with controlled access
- Handle register access, memory operations, and flag management
- Support custom instruction semantics and behavior
- Integrate with assembler, disassembler, and simulator

### 9. Simulator (`src/isa_xform/core/simulator.py`, `src/isa_xform/core/zx16sim.py`)

Provides instruction execution simulation for testing and debugging.

**Key Responsibilities:**
- Execute instructions using ISA definitions
- Simulate register and memory state
- Support debugging and step-by-step execution
- Provide execution traces and state inspection
- Handle system calls and interrupts

### 10. Bit Utilities (`src/isa_xform/utils/bit_utils.py`)

Provides low-level bit manipulation operations essential for instruction encoding and decoding.

**Key Responsibilities:**
- Bit field extraction and manipulation with configurable widths
- Sign extension for different bit widths
- Number format parsing (binary, decimal, hexadecimal)
- Alignment operations with power-of-2 boundaries
- Endianness conversion between bytes and integers
- Comprehensive input validation and error handling

**Key Functions:**
- `extract_bits()`, `set_bits()` - Bit field operations
- `sign_extend()` - Configurable sign extension
- `parse_bit_range()` - Parse ISA bit field specifications
- `create_mask()` - Generate bit masks
- `align_up()`, `align_down()` - Memory alignment
- `bytes_to_int()`, `int_to_bytes()` - Endianness conversion

### 11. Error Handling (`src/isa_xform/utils/error_handling.py`)

Comprehensive error management system with detailed context and reporting.

**Key Responsibilities:**
- Custom exception hierarchies for different error types
- Error context tracking with file/line/column information
- Batch error collection and reporting
- Suggestion and resolution hint system
- Integration with all toolkit components
- Configurable error limits and formatting

**Key Classes:**
- `ISAError` - Base exception with context and suggestions
- `ErrorLocation` - Detailed error location information
- `ErrorReporter` - Batch error collection and formatting
- Specific error types: `ISALoadError`, `ParseError`, `AssemblerError`, etc.

### 12. ISA Utilities (`src/isa_xform/utils/isa_utils.py`)

Provides utility functions for working with ISA definitions.

**Key Responsibilities:**
- ISA validation and consistency checking
- Instruction format analysis and validation
- Register set validation and analysis
- ISA comparison and compatibility checking

### 13. Command-Line Interface (`src/isa_xform/cli.py`)

Provides unified command-line interface for all py-isa-xform operations.

**Key Responsibilities:**
- Parse command-line arguments and options
- Dispatch commands to appropriate handlers
- Provide user-friendly error messages and help
- Support multiple input/output formats
- Handle ISA loading and validation
- Support scaffold generation for new ISAs

**Supported Commands:**
- `validate` - Validate ISA definition files
- `parse` - Parse assembly code and display AST
- `assemble` - Convert assembly to machine code
- `disassemble` - Convert machine code to assembly
- `list-isas` - List available ISA definitions
- `scaffold` - Generate new ISA scaffold definitions

## System Data Flow

### Complete Assembly Flow

```
Assembly File → Parser → AST Nodes → Assembler → Machine Code
     ↓              ↓         ↓          ↓           ↓
  Text Input   ISA Syntax   Structured  Instruction  Binary
              Processing    AST         Encoding     Output
```

### Complete Disassembly Flow

```
Machine Code → Disassembler → Instruction Decode → Symbol Reconstruction → Assembly Text
     ↓              ↓              ↓                    ↓                    ↓
  Binary Input   Pattern Match   Instruction        Label/Data          Formatted
                                   Recognition       Detection           Output
```

### ISA Definition Flow

```
JSON Definition → ISALoader → Validation → ISADefinition Object
      ↓              ↓            ↓              ↓
  User Input    File Loading   Consistency   Component Access
                                   Check
```

## Built-in ISA Support

The system includes several built-in ISA definitions:

- **ZX16**: 16-bit RISC-V inspired ISA (reference implementation)
- **RISC-V RV32I**: Standard RISC-V 32-bit integer instruction set
- **Simple RISC**: Basic RISC-style instruction set for educational purposes
- **Modular Example**: Demonstrates modular ISA design patterns
- **Variable Length Example**: Demonstrates variable-length instruction support
- **Quantum Core ISA**: Quantum computing instruction set example
- **Custom Examples**: Various custom ISA examples for learning and testing

## Advanced Features

### Variable Length Instructions

Support for ISAs with variable-length instructions through:
- Opcode-based length determination
- Configurable length tables
- Dynamic instruction parsing and encoding

### Automatic Data Region Detection

The disassembler automatically detects data vs code regions based on:
- ISA memory layout configuration
- Interrupt vector regions
- Data section definitions
- MMIO region specifications

### Smart Disassembly

Advanced disassembly features including:
- Pseudo-instruction reconstruction
- Symbol reconstruction from machine code
- Automatic label generation for jump targets
- Data pattern recognition

### Professional Binary Format

Default headered binary format with:
- Automatic entry point detection
- Tool interoperability
- Robust disassembly without manual address specification
- Industry-standard patterns

## Integration Points

### External Tool Integration

The system is designed for integration with:
- Debuggers and development tools
- EDA (Electronic Design Automation) tools
- Educational platforms
- Research and analysis tools

### API Design

The system provides clean APIs for:
- ISA definition loading and validation
- Assembly and disassembly operations
- Symbol table management
- Error handling and reporting
- Custom instruction and directive implementation

## Performance Considerations

### Memory Management

- Efficient bit manipulation for large instruction sets
- Streaming disassembly for large binary files
- Symbol table optimization for complex programs

### Scalability

- Modular design supports large ISA definitions
- Efficient parsing for large assembly files
- Optimized encoding/decoding for complex instructions

## Security and Safety

### Sandboxed Execution

- Safe execution environment for custom instruction implementations
- Controlled access to system resources
- Input validation and sanitization

### Error Handling

- Comprehensive error detection and reporting
- Graceful degradation for malformed input
- Detailed context information for debugging

## Conclusion

The py-isa-xform architecture provides a complete, modular framework for working with custom instruction set architectures. The clean separation of concerns, comprehensive error handling, and extensible design make it suitable for both educational and production environments. The system's support for variable-length instructions, automatic data detection, and professional tool integration demonstrates its maturity and readiness for real-world applications. 