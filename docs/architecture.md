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

## Core Components

### 1. ISA Definition System (`src/isa_xform/core/isa_loader.py`)

The foundation of the entire system that provides infrastructure for defining and validating instruction set architectures.

**Key Responsibilities:**
- Load ISA definitions from JSON files
- Validate ISA specifications for completeness and consistency
- Provide standardized internal representation of ISAs
- Support extensible instruction and addressing mode definitions
- Handle ISA-specific syntax configurations

**Key Classes:**
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

### 2. Assembly Parser (`src/isa_xform/core/parser.py`)

Converts human-readable assembly code into structured Abstract Syntax Tree (AST) representations with full ISA syntax support.

**Key Responsibilities:**
- Parse assembly source files with ISA-specific syntax rules
- Generate AST nodes for different assembly constructs
- Handle labels, instructions, directives, and comments
- Support configurable syntax (comment chars, prefixes, case sensitivity)
- Provide detailed error reporting with line and column information

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

### 3. Assembler (`src/isa_xform/core/assembler.py`)

Converts assembly language AST into binary machine code with full ISA support.

**Key Responsibilities:**
- Transform AST nodes into binary machine code
- Handle two-pass assembly for forward reference resolution
- Support field-based and legacy instruction encoding
- Process assembly directives (.org, .word, .byte, etc.)
- Validate operand values against bit field constraints
- Generate comprehensive error messages with context

**Key Classes:**
- `Assembler` - Main assembly engine with ISA-aware encoding
- `AssemblyContext` - Maintains state during assembly process
- `AssembledCode` - Result container with machine code and symbols

**Assembly Process:**
```
AST Nodes → Symbol Collection (Pass 1) → Code Generation (Pass 2) → Machine Code
```

### 4. Disassembler (`src/isa_xform/core/disassembler.py`)

Converts binary machine code back into human-readable assembly language.

**Key Responsibilities:**
- Decode binary machine code using ISA instruction patterns
- Identify code vs. data sections automatically
- Generate symbolic labels for jump targets and data references
- Support multiple instruction encoding formats
- Handle endianness and instruction size configurations
- Provide formatted output with optional addresses and machine code

**Key Classes:**
- `Disassembler` - Main disassembly engine with pattern matching
- `DisassembledInstruction` - Individual disassembled instruction representation
- `DisassemblyResult` - Complete disassembly result with instructions and data

**Disassembly Process:**
```
Machine Code → Pattern Matching → Instruction Decode → Symbol Extraction → Assembly Text
```

### 5. Symbol Table Management (`src/isa_xform/core/symbol_table.py`)

Manages symbols, labels, and their values during assembly and disassembly processes.

**Key Responsibilities:**
- Track symbol definitions and their memory addresses
- Resolve forward references and symbol dependencies
- Handle different symbol types (labels, constants, data)
- Support multiple passes for complex symbol resolution
- Provide symbol lookup and validation services
- Generate symbol export/import capabilities

**Key Classes:**
- `SymbolTable` - Main symbol management container
- `Symbol` - Individual symbol representation with metadata
- `SymbolType` - Enumeration of symbol types (label, constant, etc.)
- `SymbolScope` - Symbol scope management (local, global, external)

**Symbol Resolution Process:**
```
AST Nodes → Symbol Extraction → Address Assignment → Forward Reference Resolution → Symbol Table
```

### 6. Bit Utilities (`src/isa_xform/utils/bit_utils.py`)

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

### 7. Error Handling (`src/isa_xform/utils/error_handling.py`)

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

### 8. Command-Line Interface (`src/isa_xform/cli.py`)

Provides unified command-line interface for all py-isa-xform operations.

**Key Responsibilities:**
- Parse command-line arguments and options
- Dispatch commands to appropriate handlers
- Provide user-friendly error messages and help
- Support multiple input/output formats
- Handle ISA loading and validation

**Supported Commands:**
- `validate` - Validate ISA definition files
- `parse` - Parse assembly code and display AST
- `assemble` - Convert assembly to machine code
- `disassemble` - Convert machine code to assembly
- `list-isas` - List available ISA definitions

## System Data Flow

### Complete Assembly Flow

```
Assembly File → Parser → AST Nodes → Assembler → Machine Code
     ↓              ↓         ↓          ↓           ↓
  Text Input   ISA Syntax   Structured  Instruction  Binary
              Processing    AST         Encoding     Output
                ↓              ↓          ↓           ↓
            Symbol Table → Forward Ref → Final       Error
            Management     Resolution    Addresses   Reporting
```

### Complete Disassembly Flow

```
Machine Code → Disassembler → Instructions → Formatter → Assembly Text
     ↓              ↓              ↓            ↓            ↓
  Binary Input   Pattern        Decoded       Symbol       Human
                Matching        Structs      Generation   Readable
                    ↓              ↓            ↓
                Data Section   Operand       Address
                Detection      Resolution    Formatting
```

### ISA Definition Flow

```
JSON File → ISA Loader → Validation → ISADefinition → All Components
    ↓           ↓           ↓            ↓              ↓
  Raw JSON   JSON Parse   Rules Check   Validated      Available
             & Load       & Validate    Object         for Use
                ↓            ↓
            Syntax Rules  Field Defs
            Extraction    Processing
```

## ISA Definition Format

ISAs are defined using a comprehensive JSON format that specifies all aspects of the instruction set architecture:

```json
{
  "name": "SimpleRISC",
  "version": "1.0",
  "description": "A simple RISC-style instruction set",
  "word_size": 32,
  "endianness": "little",
  "instruction_size": 32,
  "assembly_syntax": {
    "comment_char": ";",
    "label_suffix": ":",
    "register_prefix": "$",
    "immediate_prefix": "#",
    "hex_prefix": "0x",
    "binary_prefix": "0b",
    "case_sensitive": false
  },
  "address_space": {
    "default_code_start": 4096,
    "default_data_start": 8192,
    "default_stack_start": 12288
  },
  "registers": {
    "general_purpose": [
      {"name": "R0", "size": 32, "alias": ["ZERO"], "description": "Zero register"},
      {"name": "R1", "size": 32, "alias": ["AT"], "description": "Assembler temporary"}
    ]
  },
  "instructions": [
    {
      "mnemonic": "ADD",
      "opcode": "0001",
      "format": "R-type",
      "description": "Add two registers",
      "encoding": {
        "fields": [
          {"name": "opcode", "bits": "31:28", "value": "0001"},
          {"name": "rd", "bits": "27:24", "type": "register"},
          {"name": "rs1", "bits": "23:20", "type": "register"},
          {"name": "rs2", "bits": "19:16", "type": "register"}
        ]
      },
      "syntax": "ADD $rd, $rs1, $rs2",
      "semantics": "$rd = $rs1 + $rs2"
    }
  ]
}
```

## Design Principles

### 1. ISA-Agnostic Design

All components are designed to work with any custom ISA definition:
- No hardcoded instruction sets or syntax rules
- Configurable bit widths, endianness, and instruction sizes
- Flexible encoding formats supporting various architectures
- Adaptable to educational, research, or commercial ISAs

### 2. Comprehensive Error Handling

Every component provides detailed error information:
- Context-aware error messages with file/line/column
- Suggestions for problem resolution
- Batch error collection for complex validation
- Graceful degradation when possible

### 3. Modular Architecture

Clean separation allows independent testing and extension:
- Each component has well-defined interfaces
- Minimal dependencies between modules
- Easy to extend with new ISA features
- Supports plugin architectures for custom functionality

### 4. Performance Optimization

Efficient implementations for common operations:
- Optimized bit manipulation routines
- Cached ISA definition parsing
- Streaming processing for large files
- Memory-efficient data structures

## Future Architecture Enhancements

### Planned Features
- **Optimization Passes**: Code optimization during assembly
- **Debugging Support**: Debug symbol generation and handling
- **Simulation Integration**: Direct integration with simulation engines
- **Advanced Disassembly**: Control flow analysis and function detection

### Long-term Vision
- **Higher-level Language Support**: C-like syntax compilation
- **IDE Integration**: Language server protocol support
- **Cross-Architecture Analysis**: Compare ISAs and translate between them
- **Formal Verification**: Mathematical verification of ISA properties

## Performance Characteristics

### Memory Usage
- ISA definitions: ~10-100KB per architecture
- Symbol tables: Linear in number of symbols
- AST nodes: Proportional to source code size
- Machine code: 1:1 with instruction count

### Processing Speed
- Parsing: ~1000-10000 lines/second
- Assembly: ~500-5000 instructions/second
- Disassembly: ~1000-10000 instructions/second
- Validation: Sub-second for typical ISA definitions

### Scalability
- Handles programs up to millions of instructions
- Supports ISAs with thousands of instructions
- Memory usage scales linearly with program size
- Parallel processing opportunities in batch operations

## Conclusion

The py-isa-xform architecture provides a robust, extensible foundation for instruction set architecture development and analysis. The modular design ensures flexibility while maintaining performance and reliability. The comprehensive error handling and validation systems enable confident use across diverse applications, from education to research to commercial development.

The architecture successfully achieves its goal of being truly ISA-agnostic while providing professional-grade tooling capabilities. The clear component boundaries and well-defined interfaces support both current needs and future enhancements. 