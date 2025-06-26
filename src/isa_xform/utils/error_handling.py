"""
Error handling classes for ISA transformation
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class ErrorLocation:
    """Represents the location of an error in source code"""
    line: int
    column: int
    file: Optional[str] = None


class ISAError(Exception):
    """Base exception for ISA-related errors"""
    
    def __init__(self, message: str, location: Optional[ErrorLocation] = None):
        self.message = message
        self.location = location
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        if self.location:
            file_info = f" in {self.location.file}" if self.location.file else ""
            return f"{self.message} at line {self.location.line}, column {self.location.column}{file_info}"
        return self.message


class ISALoadError(ISAError):
    """Raised when there's an error loading an ISA definition"""
    pass


class ISAValidationError(ISAError):
    """Raised when an ISA definition is invalid"""
    pass


class ParseError(ISAError):
    """Raised when there's an error parsing assembly code"""
    
    def __init__(self, message: str, location: Optional[ErrorLocation] = None, 
                 expected: Optional[str] = None, found: Optional[str] = None):
        self.expected = expected
        self.found = found
        super().__init__(message, location)
    
    def _format_message(self) -> str:
        msg = super()._format_message()
        if self.expected and self.found:
            msg += f" (expected '{self.expected}', found '{self.found}')"
        return msg


class SymbolError(ISAError):
    """Raised when there's an error with symbol resolution"""
    
    def __init__(self, message: str, symbol: Optional[str] = None, 
                 location: Optional[ErrorLocation] = None):
        self.symbol = symbol
        super().__init__(message, location)
    
    def _format_message(self) -> str:
        msg = super()._format_message()
        if self.symbol:
            msg += f" (symbol: '{self.symbol}')"
        return msg


class AssemblerError(ISAError):
    """Raised when there's an error during assembly"""
    pass


class DisassemblerError(ISAError):
    """Raised when there's an error during disassembly"""
    pass


class ErrorReporter:
    """Collects and reports multiple errors"""
    
    def __init__(self):
        self.errors: List[ISAError] = []
        self.warnings: List[str] = []
    
    def add_error(self, error: ISAError):
        """Add an error to the collection"""
        self.errors.append(error)
    
    def add_warning(self, warning: str, location: Optional[ErrorLocation] = None):
        """Add a warning to the collection"""
        if location:
            warning = f"{warning} at line {location.line}, column {location.column}"
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0
    
    def get_errors(self) -> List[ISAError]:
        """Get all collected errors"""
        return self.errors.copy()
    
    def get_warnings(self) -> List[str]:
        """Get all collected warnings"""
        return self.warnings.copy()
    
    def clear(self):
        """Clear all errors and warnings"""
        self.errors.clear()
        self.warnings.clear()
    
    def raise_if_errors(self):
        """Raise the first error if any exist"""
        if self.has_errors():
            raise self.errors[0]
    
    def format_errors(self) -> str:
        """Format all errors as a string"""
        if not self.errors:
            return "No errors"
        
        lines = ["Errors:"]
        for i, error in enumerate(self.errors, 1):
            lines.append(f"  {i}. {error}")
        
        return "\n".join(lines)
    
    def format_warnings(self) -> str:
        """Format all warnings as a string"""
        if not self.warnings:
            return "No warnings"
        
        lines = ["Warnings:"]
        for i, warning in enumerate(self.warnings, 1):
            lines.append(f"  {i}. {warning}")
        
        return "\n".join(lines) 