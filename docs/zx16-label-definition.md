# ZX16 Label Definition Guide

## Overview

ZX16 assembly supports comprehensive label definition with multiple types, scopes, and advanced features like label arithmetic and bitfield extraction.

## Label Types

### 1. Global Labels
Global labels are visible across all files and are typically used for main entry points and exported functions.

```assembly
main:                  # Global label
    LI x6, 10
    CALL function
    RET
```

### 2. Local Labels
Local labels are file-scope only and start with a dot (`.`). They're useful for internal loops and temporary references.

```assembly
.local_label:          # Local label (file scope)
    ADD x1, x2
    BNZ x1, .local_label
```

### 3. Loop Labels
Common pattern for loop control structures.

```assembly
loop:                  # Loop label
    ADD x1, x2
    BNZ x1, loop       # Branch to local label
    RET
```

### 4. Section Labels
Define boundaries for code or data sections.

```assembly
data_section:          # Section label
    .word 0x1234
    .word 0x5678
```

### 5. Data Labels
Labels with data allocation directives.

```assembly
buffer: .space 64      # Data label with allocation
message: .ascii "Hello, World!"
```

## Label Syntax Rules

### Naming Convention
- **Pattern**: `^[a-zA-Z_][a-zA-Z0-9_]*$`
- **Local prefix**: `.` (for local labels)
- **Case sensitivity**: No (case-insensitive)
- **Maximum length**: 64 characters

### Placement Rules
- Must be at the start of a line
- Must be followed by a colon (`:`)
- Cannot follow instructions (must be on separate line)
- Can follow directives (for data labels)

### Scope Rules
- **Global**: Visible across all files
- **Local**: Visible only within current file
- **Section**: Defines section boundaries

## Advanced Features

### 1. Forward References
Labels can be used before they are defined, enabling flexible code organization.

```assembly
    BZ x1, forward_label    # Used before defined
    J backward_label
backward_label:
    NOP
forward_label:
    NOP
```

### 2. Label Arithmetic
Support for arithmetic operations with labels.

```assembly
start_label:
    NOP
end_label:
    .word end_label - start_label  # Label arithmetic
```

### 3. Bitfield Extraction
Extract specific bits from label addresses using `label[high:low]` syntax.

```assembly
high_bits:
    .word label[15:9]   # Upper 7 bits
low_bits:
    .word label[8:0]    # Lower 9 bits
```

### 4. Complex Expressions
Support for complex expressions with labels and constants.

```assembly
complex_expr:
    .word (buffer + 4)  # Address calculation
    .word ~0x0F         # Bitwise NOT
    .word (value << 2) | 0x03  # Shift and OR
```

## Supported Operators

### Arithmetic Operators
- `+` : Addition
- `-` : Subtraction
- `*` : Multiplication
- `/` : Division

### Bitwise Operators
- `&` : Bitwise AND
- `|` : Bitwise OR
- `^` : Bitwise XOR
- `~` : Bitwise NOT

### Shift Operators
- `<<` : Shift left
- `>>` : Shift right

### Precedence
1. `()` : Parentheses
2. `~` : Bitwise NOT
3. `* / %` : Multiply, divide, modulo
4. `+ -` : Add, subtract
5. `<< >>` : Shift left, shift right
6. `&` : Bitwise AND
7. `^` : Bitwise XOR
8. `|` : Bitwise OR

## Section Awareness

Labels are section-aware, allowing proper organization of code and data.

```assembly
.text
code_section:
    LI x1, 42
    J data_section

.data
data_section:
    .word 0xDEAD
    .word 0xBEEF
```

## Best Practices

### 1. Naming Conventions
- Use descriptive names for global labels
- Use short, clear names for local labels
- Prefix local labels with `.`
- Use consistent naming patterns

### 2. Organization
- Group related labels together
- Use section labels to organize code and data
- Keep local labels close to their usage

### 3. Forward References
- Use forward references sparingly
- Document complex label relationships
- Consider code readability when using forward references

### 4. Expression Complexity
- Keep expressions simple and readable
- Use parentheses to clarify operator precedence
- Break complex expressions into multiple lines if needed

## Examples

### Complete Function Example
```assembly
my_function:
    PUSH x3              # Save register
    ADD x6, x7           # Main operation
    POP x3               # Restore register
    RET                  # Return
```

### Data Structure Example
```assembly
struct_start:
    .word struct_size    # Size field
    .word data_ptr       # Pointer field
data_ptr:
    .word 0x1234         # Data value
struct_size:
    .word data_ptr - struct_start  # Calculate size
```

### Loop with Local Labels
```assembly
process_array:
    LI x1, 0             # Initialize counter
.loop:
    LW x2, (x1)(x3)      # Load array element
    ADD x2, x2, 1        # Increment
    SW x2, (x1)(x3)      # Store back
    ADDI x1, 2           # Next element
    BLT x1, x4, .loop    # Continue if not done
    RET
```

This comprehensive label system provides ZX16 assembly with the flexibility and power needed for complex programming tasks while maintaining clarity and readability. 