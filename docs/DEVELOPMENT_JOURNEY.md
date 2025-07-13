# Development Journey: py-isa-xform

This document chronicles the development journey of py-isa-xform, a comprehensive ISA transformation toolkit. It details the challenges we faced, the solutions we implemented, and the lessons learned throughout the development process.

## Project Genesis and Initial Vision

The py-isa-xform project began with a vision to create a professional-grade toolkit for working with custom instruction set architectures. The initial goal was to build a system that could handle any ISA definition through a declarative JSON format, providing assembler and disassembler capabilities that were both powerful and educational. The project was designed to serve multiple audiences: computer architecture students learning about ISAs, researchers prototyping new architectures, and developers building custom processor toolchains. 

*It was also done in completion of the course project requirement for CSCE2303: Computer Organization and Assembly Language Programming @ The American University in Cairo (AUC), New Cairo, Egypt, under the supervision of Dr. Mohamed Shalan.*

The foundation was built around the ZX16 ISA, a 16-bit RISC-V inspired instruction set developed by Dr. Mohamed Shalan, Professor at AUC. This ISA served as our primary test case and reference implementation, providing a realistic and comprehensive instruction set that included arithmetic operations, memory access, control flow, and system calls. The choice of ZX16 was strategic - it was complex enough to test all aspects of our toolkit while remaining accessible for educational purposes.

## Early Architecture Decisions and Challenges

One of the first major architectural decisions was the choice of a modular, component-based design. We structured the system around core components: ISA loader, parser, assembler, disassembler, and symbol table. Each component was designed to be independent yet seamlessly integrated. This modular approach proved invaluable as the project evolved, allowing us to add new features without disrupting existing functionality.

The initial implementation faced several technical challenges. The first was designing a flexible ISA definition format that could handle various instruction encoding schemes. We experimented with different approaches before settling on a field-based encoding system that could represent both simple and complex instruction formats. This system uses explicit bit field definitions, allowing for precise control over instruction encoding while maintaining readability.

Another early challenge was implementing proper symbol resolution and forward reference handling. Traditional assemblers use a two-pass approach, but implementing this correctly required careful consideration of symbol scoping, label resolution, and address calculation. We developed a robust symbol table system that could handle both local and global symbols, with proper error reporting for undefined or duplicate symbols.

## The Expression Evaluation Challenge

One of the most significant challenges we encountered was implementing expression evaluation in assembly directives. Users wanted to be able to write complex expressions in data directives, such as `.word label + 4` or `.byte (value >> 2) & 0xFF`. This feature would greatly enhance the usability of the assembler, making it more compatible with existing assembly language conventions.

The initial implementation attempted to add expression evaluation directly into the directive handler. However, this approach quickly became complex and error-prone. The expression parser needed to handle operator precedence, parentheses, symbol resolution, and type checking. Additionally, we had to ensure that expressions were evaluated in the correct context, with access to the symbol table and proper error reporting.

After several iterations, we made the strategic decision to defer expression evaluation implementation. While this feature would be valuable, we prioritized getting the core assembler and disassembler functionality working correctly first. This decision allowed us to focus on the fundamental features and ensure they were robust and well-tested. The expression evaluation feature was documented as a future enhancement, with a clear roadmap for implementation.

## Binary Format Evolution and Header Design

The binary output format underwent several iterations as we refined the system. Initially, the assembler produced raw binary files without any metadata. While this worked for simple cases, it created problems for the disassembler, which needed to know the starting address and ISA information to properly disassemble the code.

We designed a header format that included essential metadata while remaining lightweight. The header includes a magic number for format identification, ISA name and version, code size, and entry point address. This design allows the disassembler to automatically detect the correct starting address and verify that the binary was assembled with the correct ISA.

The header format also supports both headered and raw binary modes. Raw binary mode is useful for bootloaders and legacy systems that expect pure machine code. This flexibility ensures compatibility with various use cases while providing the benefits of metadata when possible.

## Operand Ordering and Disassembly Accuracy

A critical issue we discovered during testing was incorrect operand ordering in the disassembler output. The disassembler was outputting operands in the order they appeared in the instruction encoding, rather than the order specified in the instruction syntax. For example, a ZX16 ADD instruction with syntax "ADD rd, rs2" was being disassembled as "ADD rs2, rd" because the encoding fields were in a different order.

This issue required a fundamental redesign of the disassembly process. We implemented a system that parses the instruction syntax to determine the correct operand order, then maps the decoded field values to the appropriate operand positions. This ensures that disassembled code matches the original assembly syntax, making it much more readable and usable.

The solution involved creating a mapping between encoding field order and syntax operand order. The disassembler now correctly outputs operands in the order specified by the instruction syntax, regardless of how they are encoded in the machine code. This fix was crucial for maintaining the usability of the disassembler output.

## Custom Instruction Implementation System

One of the most innovative features we developed was the custom instruction implementation system. This allows users to define the actual behavior of instructions using Python code embedded in the ISA definition. This feature enables the creation of complex instructions that go beyond simple arithmetic operations.

The implementation system provides a controlled execution environment with access to registers, memory, program counter, and status flags. Users can write Python code that defines how their custom instructions behave, including complex operations like cryptographic functions, DSP operations, or specialized memory operations.

The challenge was creating a secure execution environment that prevented malicious code execution while providing the flexibility needed for custom instructions. We implemented a sandboxed environment that restricts access to system resources while allowing the necessary operations for instruction simulation.

## Modular Refactoring and ISA-Aware Architecture

As the toolkit matured and we began supporting multiple ISAs beyond ZX16, we encountered a significant architectural challenge: the assembler and disassembler were hardcoded with ZX16-specific values and assumptions. This limitation prevented the toolkit from being truly modular and adaptable to different instruction set architectures.

### Hardcoded Constants and Architecture-Specific Assumptions

The initial implementation contained numerous hardcoded values that were specific to the ZX16 architecture. These included instruction size (16 bits), word size (16 bits), address space (16 bits), immediate widths, register counts, and various bit masks. While these values worked perfectly for ZX16, they created a fundamental barrier to supporting other ISAs.

For example, the disassembler used hardcoded bit masks like `0xFFFF` for 16-bit values and assumed 7-bit signed immediates. The assembler assumed 16-bit instruction alignment and used ZX16-specific register formatting. These assumptions made it impossible to support 32-bit RISC-V style ISAs or 8-bit microcontroller ISAs without extensive code modifications.

The challenge was identifying all these hardcoded values and replacing them with ISA-aware functions that could dynamically adapt to different architectures. This required a systematic audit of the entire codebase to locate every architecture-specific assumption.

### Sign Extension and Immediate Handling Complexity

One of the most complex challenges was implementing proper sign extension that worked correctly across different ISA configurations. The original implementation used hardcoded sign extension logic that assumed 7-bit signed immediates for ZX16. When we tried to support other ISAs, this logic failed spectacularly.

For example, a 32-bit RISC-V ISA might use 12-bit signed immediates for I-type instructions and 20-bit signed immediates for J-type instructions. The sign extension logic needed to be aware of the immediate width and the target word size to correctly handle sign extension.

We implemented an ISA-aware sign extension system that calculates the sign bit position based on the immediate width and applies the correct mask based on the word size. This system dynamically adapts to different ISA configurations, ensuring that sign extension works correctly regardless of the architecture.

The immediate handling challenge was further complicated by the need to distinguish between raw field values and sign-extended values. The disassembler needed access to both the raw immediate value (for display purposes) and the sign-extended value (for calculations). This required refactoring the field extraction system to provide both values simultaneously.

### Disassembly Output Formatting and Raw Value Access

A critical issue emerged during testing when we discovered that the disassembler was incorrectly displaying signed immediates. The problem was that the disassembly logic was manually extracting fields without using the modular field extraction system, causing raw values to be missing.

For example, a ZX16 SW instruction with a negative immediate was being disassembled as `SW x0, 14(x0)` instead of the expected `SW t0, -2(t0)`. This happened because the disassembler was using sign-extended values for display instead of raw values, and the sign extension was being applied incorrectly.

The solution required a fundamental refactoring of the disassembly process. We implemented a unified field extraction system that always uses the `_extract_field_values` method, ensuring that both raw and sign-extended values are available for all instructions. We also created ISA-aware immediate formatting functions that handle signed immediate display correctly.

The disassembly formatting challenge was particularly complex because different ISAs might format immediates differently. Some ISAs prefer decimal notation for small values and hexadecimal for large values, while others might use different prefixes or formatting conventions. We implemented a flexible formatting system that can be customized per ISA.

### ISA Definition Schema Evolution and Standardization

As we expanded support for multiple ISAs, we discovered that the existing ISA definitions were inconsistent and missing many fields that the toolkit needed for proper modular operation. The ZX16 ISA had evolved to include comprehensive configuration fields, but other ISA definitions lacked these essential components.

The standardization challenge involved identifying all the fields that the toolkit required for modular operation and updating all ISA definitions to include these fields. Missing fields included `pc_behavior`, `instruction_architecture`, `operand_formatting`, `instruction_categories`, `pseudo_instruction_fallbacks`, `data_detection`, `symbol_resolution`, `error_messages`, and `constants`.

Each missing field required understanding how the toolkit used that information and ensuring that the field values were appropriate for each ISA. For example, the `pc_behavior` field defines how the program counter behaves during jumps and branches, which varies significantly between different architectures.

The standardization process revealed inconsistencies in field naming and structure across different ISA definitions. We had to establish consistent conventions for field names, data types, and organizational structure. This included standardizing register definitions, instruction formats, and directive implementations.

### Utility Function Modularization and ISA Awareness

The toolkit contained numerous utility functions that were hardcoded for specific architectures. These included bit manipulation functions, immediate formatting functions, and register formatting functions. Making these functions ISA-aware required significant refactoring.

For example, the `sign_extend` function was originally hardcoded to handle 7-bit immediates. We refactored it to accept immediate width and word size parameters, making it work correctly for any ISA configuration. Similarly, the immediate formatting functions needed to be aware of the ISA's formatting preferences.

The utility function modularization challenge was complicated by the need to maintain backward compatibility. We had to ensure that existing code continued to work while adding the new ISA-aware functionality. This required careful interface design and extensive testing.

### Testing and Validation Across Multiple ISAs

The modular refactoring introduced a new testing challenge: ensuring that the toolkit worked correctly across multiple different ISA configurations. We needed to test that the assembler and disassembler could handle ISAs with different instruction sizes, word sizes, register counts, and encoding schemes.

The testing challenge was particularly complex because different ISAs have different edge cases and requirements. For example, a 32-bit RISC-V ISA might have different immediate value ranges than a 16-bit ZX16 ISA, requiring different test cases and validation logic.

We developed a comprehensive testing strategy that included multiple ISA definitions with different characteristics. This included testing with ZX16 (16-bit), custom ISAs with various configurations, and quantum core ISAs with unique instruction formats. Each ISA required its own set of test programs to verify that assembly and disassembly worked correctly.

The validation process revealed several subtle issues that only appeared when testing with different ISA configurations. These included issues with immediate value handling, register name resolution, and instruction encoding. Each issue required careful analysis and systematic fixes.

### Performance Impact and Optimization

The modular refactoring introduced some performance overhead due to the additional function calls and dynamic calculations required for ISA-aware operations. The original hardcoded approach was faster because it avoided function calls and used pre-calculated constants.

We implemented several optimizations to minimize the performance impact. These included caching ISA configuration values, optimizing the field extraction process, and reducing redundant calculations. The optimizations ensured that the modular system performed acceptably while maintaining the flexibility needed for multiple ISA support.

The performance optimization challenge was particularly important because the toolkit needed to handle large assembly programs efficiently. We conducted performance testing with various ISA configurations to ensure that the modular approach didn't significantly impact usability.

## Documentation Challenges and Solutions

As the project grew in complexity, maintaining accurate and comprehensive documentation became a significant challenge. The initial documentation was scattered across multiple files and often became outdated as features evolved. We needed a systematic approach to documentation that would keep pace with development.

We implemented a comprehensive documentation review process that involved systematically checking each documentation file against the actual codebase implementation. This process revealed several areas where documentation was inaccurate or incomplete. We updated all documentation to reflect the current state of the system, removed outdated information, and added missing details.

The documentation cleanup included removing references to non-existent features, updating examples to work with the current codebase, and ensuring that all API documentation was accurate. We also reorganized the documentation structure to make it more navigable and user-friendly.

## Testing and Quality Assurance

Quality assurance was a continuous challenge throughout development. The system needed to handle a wide variety of edge cases, from malformed ISA definitions to invalid assembly code. We implemented comprehensive testing strategies that included unit tests, integration tests, and end-to-end testing.

The testing process revealed several bugs and edge cases that required fixes. These included issues with immediate value validation, register name resolution, and error handling. Each bug fix was documented and tested to ensure it didn't introduce new issues.

We also developed a set of test ISAs that cover various instruction formats and edge cases. These test ISAs help ensure that the system can handle different instruction encoding schemes and provide a baseline for regression testing.

## Performance Optimization and Scalability

As the system grew in complexity, performance became a concern. The initial implementation was functional but not optimized for large programs or complex ISA definitions. We implemented several optimizations to improve performance.

The ISA loader now caches loaded ISA definitions to avoid repeated file I/O and parsing. The assembler uses efficient bit manipulation operations and optimized data structures for symbol resolution. The disassembler implements fast pattern matching for instruction recognition.

These optimizations ensure that the system can handle large assembly programs and complex ISA definitions efficiently. The performance improvements were achieved while maintaining the accuracy and reliability of the system.

## User Experience and Error Handling

User experience was a key focus throughout development. We wanted the system to provide clear, helpful error messages that guide users toward solutions. This required implementing comprehensive error handling with detailed context information.

The error handling system includes location information (file, line, column), context about the problematic code, and suggestions for resolution. Error messages are designed to be educational, helping users understand what went wrong and how to fix it.

We also implemented a robust validation system that catches errors early in the process. The ISA loader validates ISA definitions for completeness and correctness, while the assembler validates instructions and operands against the ISA definition.

## Integration and Interoperability

Ensuring that all components work together seamlessly was a significant challenge. The parser, assembler, disassembler, and symbol table needed to integrate properly while maintaining their independence. We designed clear interfaces between components and implemented proper error propagation.

The integration testing revealed several issues with component communication and data flow. We fixed these issues by implementing proper abstraction layers and ensuring that each component had a well-defined interface. This modular design makes the system easier to maintain and extend.

## Scaffold Generator Development and Integration Challenges

One of the most significant additions to the toolkit was the ISA scaffold generator, designed to help users rapidly create new ISA definitions. This feature was intended to lower the barrier to entry for creating custom ISAs by providing a template-based generation system. However, the development and integration of this feature presented several unexpected challenges that required careful consideration and systematic problem-solving.

### Initial Scaffold Generator Architecture

The scaffold generator was designed to take high-level specifications (instruction names, register count, word size, etc.) and generate complete ISA JSON definitions. The initial architecture used a template-based approach with predefined instruction formats for common instruction types like R-type, I-type, and J-type instructions. This approach seemed straightforward but quickly revealed complexity in handling different instruction sizes and encoding schemes.

The first challenge was making the scaffold generator truly modular and ISA-driven. The initial implementation was hardcoded for 16-bit instructions, which limited its usefulness for creating 32-bit or 64-bit ISAs. We needed to redesign the system to dynamically generate instruction templates based on the specified instruction size and word size parameters.

### Dynamic Template Generation and Field Layout Issues

The most significant technical challenge was implementing dynamic template generation that could adapt to different instruction sizes. The original scaffold generator used static templates that assumed 16-bit instructions with specific bit field layouts. When we attempted to generate 32-bit RISC-V style ISAs, the field layouts were completely wrong.

We implemented a `get_instruction_templates()` method that generates appropriate templates based on instruction size. For 32-bit instructions, we created RISC-V style templates with proper field layouts (31:25 for funct7, 24:20 for rs2, etc.). For 16-bit instructions, we maintained the original compact layouts. This dynamic approach required careful consideration of bit field positioning and immediate value handling.

The field layout challenge was particularly complex because different instruction sizes require different approaches to immediate value encoding. 16-bit instructions typically use 7-bit signed immediates, while 32-bit RISC-V instructions use 12-bit signed immediates for I-type instructions and 20-bit signed immediates for J-type instructions. The scaffold generator needed to handle these differences automatically.

### Missing Required Fields and ISA Loader Compatibility

A critical issue emerged when we discovered that the generated ISA definitions were missing several required fields that the ISA loader expected. The first missing field was the `size` field for registers, which the loader uses to validate register definitions. Without this field, the loader would fail with a `KeyError: 'size'`.

We systematically identified and added all missing required fields:
- `size` field for both general-purpose and special registers
- `format` field for all instructions (R-type, I-type, J-type, etc.)
- `mnemonic` field for pseudo-instructions (instead of `name`)
- `syntax` field for pseudo-instructions

Each missing field required understanding how the ISA loader processes different components and ensuring that the generated definitions match the expected format. This process revealed the importance of comprehensive testing with the actual toolkit components rather than just generating syntactically correct JSON.

### Pseudo-Instruction Field Naming Inconsistencies

The pseudo-instruction implementation revealed an inconsistency in field naming conventions within the toolkit. The ISA loader expected pseudo-instructions to have a `mnemonic` field, but the scaffold generator was using `name`. This inconsistency required updating the scaffold generator to match the loader's expectations.

Additionally, pseudo-instructions required a `syntax` field that wasn't initially included. This field is used by the disassembler to reconstruct pseudo-instructions from their expanded forms. The syntax field needed to match the expected operand pattern, such as "MV rd, rs" for the move pseudo-instruction.

### CLI Integration and Subprocess Communication

Integrating the scaffold generator into the main CLI presented its own set of challenges. The scaffold generator was originally implemented as a standalone script, but we wanted to make it available as a subcommand in the main CLI for better user experience.

The integration required careful handling of argument passing between the main CLI and the scaffold generator. We implemented a subprocess-based approach that allows the scaffold generator to receive all its arguments while maintaining the existing CLI structure. This approach provides flexibility but required proper error handling and output capture.

The subprocess communication also revealed issues with working directory management and file path resolution. The scaffold generator needed to work correctly regardless of the current working directory when invoked through the CLI.

### Instruction Size and Word Size Parameter Handling

The scaffold generator needed to handle different combinations of instruction size and word size parameters correctly. The relationship between these parameters affects how instructions are encoded and how immediate values are handled.

For example, a 32-bit instruction with 32-bit word size requires different immediate value handling than a 16-bit instruction with 16-bit word size. The scaffold generator needed to generate appropriate implementation code that uses the correct bit masks and sign extension logic.

The word mask calculation (`word_mask = (1 << word_size) - 1`) needed to be used consistently throughout the generated implementation code. This ensures that all arithmetic operations respect the word size constraints of the target architecture.

### Testing and Validation of Generated ISAs

Testing the generated ISAs presented unique challenges because we needed to verify that the generated definitions were not only syntactically correct but also functionally complete. This required creating test programs that used the generated instructions and verifying that they could be assembled and disassembled correctly.

The testing process revealed several edge cases where the generated ISAs had subtle issues:
- Incorrect immediate value handling in different instruction types
- Missing or incorrect field mappings for complex instruction formats
- Improper handling of signed vs. unsigned immediates

We developed a comprehensive testing strategy that includes:
- Unit tests for individual instruction generation
- Integration tests for complete ISA generation
- End-to-end tests that assemble and disassemble programs using generated ISAs

### Error Handling and User Feedback

The scaffold generator needed robust error handling to provide meaningful feedback when generation fails. This included validation of input parameters, checking for conflicting specifications, and providing clear error messages that guide users toward solutions.

Error handling was particularly important for the CLI integration, where errors needed to be captured and displayed properly through the main CLI interface. We implemented proper error propagation and formatting to ensure that users receive helpful feedback when something goes wrong.

### Documentation and Usage Examples

Creating comprehensive documentation for the scaffold generator was challenging because the feature touches multiple aspects of the toolkit. Users needed to understand:
- How to specify instruction lists and directives
- How to choose appropriate instruction and word sizes
- How to customize the generated ISAs for their specific needs
- How to integrate the generated ISAs with the rest of the toolkit

We created detailed usage examples and documented the various parameters and options available. The documentation needed to be clear enough for users who might not be familiar with instruction set architecture design while providing enough detail for advanced users who want to create complex ISAs.

## Future Enhancements and Roadmap

Throughout development, we identified several areas for future enhancement. These include expression evaluation in directives, support for more complex instruction formats, and integration with external tools and simulators. We documented these enhancements to provide a clear roadmap for future development.

The expression evaluation feature remains a priority for future development. This would allow users to write complex expressions in data directives, greatly enhancing the usability of the assembler. The implementation would involve creating a safe expression parser and evaluator that integrates with the existing directive system.

Other planned enhancements include support for more sophisticated instruction formats, improved optimization capabilities, and integration with external debugging and simulation tools. These enhancements will build on the solid foundation we've established.

## Lessons Learned and Best Practices

The development of py-isa-xform taught us several valuable lessons about building complex software systems. One key lesson was the importance of modular design and clear interfaces between components. This approach made the system easier to develop, test, and maintain.

Another important lesson was the value of comprehensive testing and documentation. The testing process revealed many issues that would have been difficult to discover otherwise. Good documentation helped us maintain consistency and made the system more accessible to users.

We also learned the importance of user feedback and iterative development. The system evolved significantly based on testing and usage patterns. This iterative approach allowed us to refine features and fix issues before they became major problems.

The modular refactoring process taught us the importance of planning for extensibility from the beginning. While the initial hardcoded approach was simpler and faster to implement, it created significant technical debt that required extensive refactoring later. This experience reinforced the value of designing systems with future requirements in mind.

## Conclusion

The development of ~xform has been a rewarding journey that resulted in a robust, flexible, and user-friendly ISA transformation toolkit. The challenges we faced and the solutions we implemented have created a system that serves its intended purpose well.

The project demonstrates the value of careful planning, modular design, and iterative development. The resulting toolkit provides a solid foundation for working with custom instruction set architectures, whether for educational purposes, research, or development.

As we look to the future, we're excited about the potential for further enhancements and the continued evolution of the system. The foundation we've built provides a strong base for adding new features and capabilities while maintaining the reliability and usability that users expect.

The journey of developing ~xform has been both challenging and rewarding. We've created a tool that fills a real need in the computer architecture community, and we're proud of the quality and functionality of the final product. The lessons learned during this development process will continue to inform our future work and help us create even better tools for the community. 