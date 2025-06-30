# Parser Documentation

## Overview

The `parser` module is a core component of the py-isa-xform toolkit responsible for converting human-readable assembly language source code into a structured Abstract Syntax Tree (AST) representation. This module provides the foundation for all subsequent processing including assembly, disassembly, symbol resolution, and program analysis.

## Design Philosophy

The parser is designed with the following principles:

- **Robustness**: Graceful handling of various assembly syntaxes and error conditions
- **Extensibility**: Support for ISA-specific syntax and custom directives
- **Performance**: Efficient line-by-line parsing with minimal memory overhead
- **Clarity**: Clear separation between lexical analysis and syntax processing
- **Error Reporting**: Detailed error messages with precise line and column information
- **ISA Integration**: Full integration with ISA definitions for instruction validation

## Architecture

### Parsing Pipeline

The parser follows a simple but effective pipeline:

```
Assembly Text → Line Tokenization → AST Node Creation → AST List
     ↓              ↓                    ↓              ↓
  Raw Input    Token Extraction    Node Generation   Final Output
```

### Component Structure

1. **Line Tokenizer**: Breaks assembly text into logical tokens
2. **Node Generator**: Creates appropriate AST nodes from tokens
3. **Error Handler**: Provides detailed error reporting and recovery
4. **ISA Integration**: Uses ISA definitions for instruction validation
5. **Operand Parser**: Handles ISA-specific operand parsing and validation

## Core Classes

### `Parser`

The main parser class that orchestrates the parsing process.

**Constructor:**
```python
def __init__(self, isa_definition: ISADefinition)
```

**Key Methods:**

#### `parse(text: str) -> List[ASTNode]`

Parses assembly text and returns a list of AST nodes.

**Parameters:**
- `text`: Assembly code as a string

**Returns:**
- `List[ASTNode]`: List of parsed AST nodes

**Raises:**
- `ParseError`: If parsing fails with detailed error information

**Example:**
```python
from isa_xform.core.parser import Parser
from isa_xform.core.isa_loader import ISALoader

# Load ISA definition
loader = ISALoader()
isa_def = loader.load_isa("zx16")

# Create parser
parser = Parser(isa_def)

# Parse assembly text
assembly_text = """
    .text
    .globl main
    
    main:
        LI a0, 10          # Load immediate value
        LI a1, 5           # Load immediate value
        ADD a0, a1         # Add registers
        ECALL 0x3FF        # Exit program
"""

nodes = parser.parse(assembly_text)
```

#### `parse_file(file_path: str) -> List[ASTNode]`

Parses an assembly file and returns a list of AST nodes.

**Parameters:**
- `file_path`: Path to the assembly file

**Returns:**
- `List[ASTNode]`: List of parsed AST nodes

**Raises:**
- `FileNotFoundError`: If the file does not exist
- `ParseError`: If parsing fails

## AST Node Types

### Base Class: `ASTNode`

All AST nodes inherit from this base class.

**Attributes:**
- `line_number`: Source line number (1-indexed)
- `column`: Source column number (1-indexed)

### `LabelNode`

Represents a label definition in assembly code.

**Attributes:**
- `name`: Label name (string)

**Example:**
```assembly
main:           # Creates LabelNode with name="main"
start_loop:     # Creates LabelNode with name="start_loop"
```

### `InstructionNode`

Represents an assembly instruction with its operands.

**Attributes:**
- `mnemonic`: Instruction mnemonic (string)
- `operands`: List of operand strings

**Example:**
```assembly
ADD a0, a1          # Creates InstructionNode with mnemonic="ADD", operands=["a0", "a1"]
LI a0, 10           # Creates InstructionNode with mnemonic="LI", operands=["a0", "10"]
ECALL 0x3FF         # Creates InstructionNode with mnemonic="ECALL", operands=["0x3FF"]
```

### `DirectiveNode`

Represents an assembler directive.

**Attributes:**
- `name`: Directive name (string)
- `arguments`: List of directive arguments (strings)

**Example:**
```assembly
.text                   # Creates DirectiveNode with name=".text", arguments=[]
.globl main             # Creates DirectiveNode with name=".globl", arguments=["main"]
.word 42                # Creates DirectiveNode with name=".word", arguments=["42"]
.ascii "Hello, World!"  # Creates DirectiveNode with name=".ascii", arguments=["Hello, World!"]
```

### `CommentNode`

Represents a comment in assembly code.

**Attributes:**
- `text`: Comment text (string)

**Example:**
```assembly
# This is a comment     # Creates CommentNode with text="This is a comment"
ADD a0, a1             # Creates CommentNode with text="Add a0 and a1"
```

## Parsing Process

### Line-by-Line Processing

The parser processes assembly code line by line for efficiency and clarity:

1. **Line Extraction**: Split input text into individual lines
2. **Whitespace Handling**: Remove leading/trailing whitespace and handle indentation
3. **Comment Detection**: Identify and extract comments
4. **Token Classification**: Determine the type of each line (label, instruction, directive)
5. **Node Creation**: Generate appropriate AST nodes based on line content

### Token Classification Rules

The parser uses these rules to classify assembly lines:

1. **Label Lines**: Lines ending with `:` (e.g., `main:`)
2. **Directive Lines**: Lines starting with `.` (e.g., `.text`, `.word`)
3. **Instruction Lines**: Lines containing instruction mnemonics
4. **Comment Lines**: Lines starting with `#` or containing `#`
5. **Empty Lines**: Lines with only whitespace (ignored)

### Operand Parsing

Operands are parsed according to ISA-specific rules:

- **Registers**: Identified by register names from ISA definition (e.g., `a0`, `a1`, `t1`, `s0`)
- **Immediates**: Values prefixed with `#` or numeric literals (e.g., `10`, `0x3FF`, `-5`)
- **Labels**: Symbolic references to memory addresses (e.g., `main`, `loop_start`)
- **Addresses**: Memory references in various formats

## ZX16 Parsing Examples

### Basic Instructions

```assembly
# ZX16 instruction parsing
LI a0, 10          # Load immediate: register a0, immediate 10
ADD a0, a1         # Add registers: destination a0, source a1
SUB a0, a1         # Subtract registers: destination a0, source a1
ADDI a0, 20        # Add immediate: register a0, immediate 20
```

### Control Flow

```assembly
# ZX16 control flow parsing
main:              # Label definition
    LI a0, 10
    BEQ a0, a1, equal_test  # Branch if equal with label target
    J final_test            # Unconditional jump with label target
equal_test:
    LI a0, 42
```

### System Calls

```assembly
# ZX16 system call parsing
ECALL 0x000        # Print character service
ECALL 0x001        # Read character service
ECALL 0x002        # Print string service
ECALL 0x3FF        # Exit program service
```

### Directives

```assembly
# ZX16 directive parsing
.text              # Text section directive
.globl main        # Global symbol directive
.data              # Data section directive
.word 42           # Word data directive
.ascii "Hello"     # ASCII string directive
.asciiz "World"    # Null-terminated string directive
```

## Error Handling

### Error Types

The parser provides comprehensive error handling:

- **ParseError**: General parsing errors with line and column information
- **SyntaxError**: Malformed assembly syntax
- **UnknownInstructionError**: Instructions not defined in the ISA
- **InvalidOperandError**: Operands that don't match expected format
- **RegisterError**: Invalid register names
- **ImmediateError**: Invalid immediate values

### Error Context

All errors include:
- Source file name and line/column numbers
- Context of the problematic code
- Suggestions for resolution where applicable
- ISA-specific validation information

### ZX16 Error Examples

```assembly
# Error: Unknown instruction
INVALID a0, a1     # Error: Unknown instruction: INVALID

# Error: Unknown register
ADD a2, a1         # Error: Unknown register: a2

# Error: Invalid immediate
LI a0, 100         # Error: Immediate value 100 doesn't fit in 7-bit signed field

# Error: Malformed syntax
ADD a0,            # Error: Missing operand for ADD instruction
```

## ISA Integration

### Instruction Validation

The parser validates instructions against the ISA definition:

```python
# Parser checks instruction mnemonics against ISA
isa_instructions = ["ADD", "SUB", "LI", "ECALL", "BEQ", "J"]
parser.validate_instruction("ADD")  # Valid
parser.validate_instruction("INVALID")  # Raises UnknownInstructionError
```

### Register Validation

Register names are validated against the ISA register set:

```python
# ZX16 register validation
valid_registers = ["a0", "a1", "t0", "t1", "s0", "s1", "sp", "ra"]
parser.validate_register("a0")  # Valid
parser.validate_register("a2")  # Raises RegisterError
```

### Operand Type Validation

Operand types are validated based on instruction requirements:

```python
# ZX16 operand validation
parser.validate_operands("ADD", ["a0", "a1"])  # Valid: two registers
parser.validate_operands("LI", ["a0", "10"])   # Valid: register and immediate
parser.validate_operands("ADD", ["a0"])        # Error: missing operand
```

## Performance Considerations

### Memory Efficiency

The parser processes instructions incrementally to minimize memory usage:

```python
# Line-by-line processing
for line in assembly_text.split('\n'):
    node = parser.parse_line(line)
    if node:
        nodes.append(node)
```

### Error Recovery

The parser continues processing after encountering errors:

```python
# Collect all errors for comprehensive reporting
errors = []
for line in assembly_text.split('\n'):
    try:
        node = parser.parse_line(line)
        nodes.append(node)
    except ParseError as e:
        errors.append(e)
        # Continue processing other lines
```

## Integration with Other Components

### Assembler Integration

The parser works seamlessly with the assembler:

```python
# Parse and assemble in one workflow
parser = Parser(isa_def)
assembler = Assembler(isa_def)

nodes = parser.parse(assembly_source)
result = assembler.assemble(nodes)
```

### Symbol Table Integration

The parser identifies symbols for the symbol table:

```python
# Extract labels and symbols during parsing
symbols = {}
for node in nodes:
    if isinstance(node, LabelNode):
        symbols[node.name] = current_address
```

### CLI Integration

The parser is accessible through the command-line interface:

```bash
# Parse assembly file
python3 -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin
```

## Best Practices

### Assembly Code Structure

Organize assembly code with clear sections:

```assembly
# Good structure
    .text
    .globl main

main:
    # Function prologue
    LI a0, 10
    
    # Main logic
    ADD a0, a1
    
    # Function epilogue
    ECALL 0x3FF

    .data
constants:
    .word 42
```

### Error Prevention

Use valid ZX16 syntax to avoid parsing errors:

```assembly
# Good: Valid ZX16 syntax
LI a0, 10          # Valid immediate value
ADD a0, a1         # Valid register names
BEQ a0, a1, label  # Valid branch instruction

# Bad: Invalid syntax
LI a0, 100         # Immediate too large
ADD a2, a1         # Unknown register
INVALID a0         # Unknown instruction
```

### Comments and Documentation

Use comments to improve code readability:

```assembly
# ZX16 program with clear comments
    .text
    .globl main

main:
    LI a0, 10          # Load first operand
    LI a1, 5           # Load second operand
    ADD a0, a1         # Add operands: a0 = a0 + a1
    ECALL 0x3FF        # Exit with result in a0
```

This parser provides professional-grade assembly language parsing with comprehensive error handling, ISA integration, and detailed validation, making it suitable for educational, research, and development applications. 