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
from isa_xform.core.isa_loader import load_isa_definition

# Load ISA definition
isa_def = load_isa_definition("simple_risc.json")

# Create parser
parser = Parser(isa_def)

# Parse assembly text
assembly_text = """
    .data
    value: .word 42
    
    .text
    main:
        add r1, r2, r3
        sub r4, r1, r5
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
add r1, r2, r3      # Creates InstructionNode with mnemonic="add", operands=["r1", "r2", "r3"]
sub r4, r1, #5      # Creates InstructionNode with mnemonic="sub", operands=["r4", "r1", "#5"]
```

### `DirectiveNode`

Represents an assembler directive.

**Attributes:**
- `name`: Directive name (string)
- `arguments`: List of directive arguments (strings)

**Example:**
```assembly
.data                   # Creates DirectiveNode with name=".data", arguments=[]
.word 42               # Creates DirectiveNode with name=".word", arguments=["42"]
.ascii "Hello, World!" # Creates DirectiveNode with name=".ascii", arguments=["Hello, World!"]
```

### `CommentNode`

Represents a comment in assembly code.

**Attributes:**
- `text`: Comment text (string)

**Example:**
```assembly
# This is a comment     # Creates CommentNode with text="This is a comment"
add r1, r2, r3         # Creates CommentNode with text="Add r1 and r2, store in r3"
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
2. **Directive Lines**: Lines starting with `.` (e.g., `.data`, `.word`)
3. **Instruction Lines**: Lines containing instruction mnemonics
4. **Comment Lines**: Lines starting with `#` or containing `#`
5. **Empty Lines**: Lines with only whitespace (ignored)

### Operand Parsing

Operands are parsed according to ISA-specific rules:

- **Registers**: Identified by register names from ISA definition
- **Immediates**: Values prefixed with `#` or numeric literals
- **Labels**: Symbolic references to memory addresses
- **Addresses**: Memory references in various formats

## Error Handling

### Error Types

The parser handles several types of errors:

1. **Syntax Errors**: Invalid assembly syntax
2. **Semantic Errors**: Invalid instruction usage
3. **ISA Errors**: Instructions not defined in the ISA
4. **Operand Errors**: Invalid operand types or values

### Error Reporting

Errors include detailed information:

```python
# Example error output
ParseError: Invalid instruction 'invalid_instruction' at line 5, column 1
ParseError: Expected register operand, got 'invalid_operand' at line 6, column 10
ParseError: Unknown directive '.invalid' at line 7, column 1
```

### Error Recovery

The parser implements graceful error recovery:

- **Line Skipping**: Skip lines with errors and continue parsing
- **Partial Results**: Return successfully parsed nodes even if errors occur
- **Error Collection**: Collect multiple errors for comprehensive reporting

## ISA Integration

### Instruction Validation

The parser uses ISA definitions to validate instructions:

```python
# Check if instruction exists in ISA
if mnemonic not in isa_definition.instructions:
    raise ParseError(f"Unknown instruction '{mnemonic}'")

# Validate operand count
instruction_def = isa_definition.instructions[mnemonic]
if len(operands) != len(instruction_def.operands):
    raise ParseError(f"Instruction '{mnemonic}' expects {len(instruction_def.operands)} operands, got {len(operands)}")
```

### Register Validation

Register names are validated against the ISA definition:

```python
# Check if register exists
if operand not in isa_definition.registers:
    raise ParseError(f"Unknown register '{operand}'")
```

## Performance Considerations

### Memory Efficiency

- **Line-by-line processing**: Avoids loading entire file into memory
- **Minimal object creation**: Reuses objects where possible
- **Efficient string handling**: Uses string slicing and splitting

### Processing Speed

- **Early termination**: Stops processing on critical errors
- **Optimized tokenization**: Fast string operations for token extraction
- **Caching**: ISA definitions are cached for repeated access

## Usage Examples

### Basic Parsing

```python
from isa_xform.core.parser import Parser
from isa_xform.core.isa_loader import load_isa_definition

# Load ISA and create parser
isa_def = load_isa_definition("simple_risc.json")
parser = Parser(isa_def)

# Parse assembly code
assembly_code = """
    .data
    counter: .word 0
    
    .text
    main:
        addi r1, r0, 10    # Initialize counter
        add r2, r1, r1     # Double the value
"""

nodes = parser.parse(assembly_code)

# Process AST nodes
for node in nodes:
    print(f"{type(node).__name__}: {node}")
```

### File Parsing

```python
# Parse from file
nodes = parser.parse_file("program.s")

# Filter by node type
labels = [node for node in nodes if isinstance(node, LabelNode)]
instructions = [node for node in nodes if isinstance(node, InstructionNode)]
```

### Error Handling

```python
try:
    nodes = parser.parse(assembly_code)
except ParseError as e:
    print(f"Parse error: {e}")
    # Handle error appropriately
```

## Integration with Other Components

### Symbol Table Integration

The parser works closely with the symbol table:

```python
# Extract symbols from AST nodes
symbol_table = SymbolTable()

for node in nodes:
    if isinstance(node, LabelNode):
        symbol_table.add_symbol(node.name, current_address)
    elif isinstance(node, DirectiveNode):
        # Handle data directives
        pass
```

### Assembler Integration

The parser provides the foundation for assembly:

```python
# Parse and then assemble
nodes = parser.parse(assembly_code)
assembler = Assembler(isa_def)
machine_code = assembler.assemble(nodes)
```

## Conclusion

The parser module provides a robust, efficient, and extensible foundation for assembly language processing in py-isa-xform. Its clean architecture, comprehensive error handling, and ISA integration make it suitable for both educational use and professional development workflows.

The parser's design allows for easy extension and customization while maintaining high performance and reliability. Its integration with other components provides a complete pipeline for assembly language processing and analysis. 