from typing import List, Optional, Dict, Any
from datetime import datetime


class AICodeError(Exception):
    """Enhanced command error that collects multiple errors with timestamps and contexts"""

    _errors: List[Dict[str, Any]] = []
    _auto_print = True  # Control whether to auto-print
    def __init__(self, message: str = "", context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.timestamp = datetime.now()
        self.context = context or {}

        if message:  # Only add non-empty messages
            error_entry = {
                'title': self.__class__.__name__,
                'message': message,
                'timestamp': self.timestamp,
                'context': self.context
            }
            AICodeError._errors.append(error_entry)
            if AICodeError._auto_print:
                print(f"{message}")
        super().__init__(message)


    def __str__(self):
        return self.message

    @classmethod
    def get_errors(cls) -> List[Dict[str, Any]]:
        """Get all collected errors with details"""
        return cls._errors.copy()

    @classmethod
    def get_error_messages(cls) -> List[str]:
        """Get only the error messages"""
        return ["<i>"+error['title']+"</i> - " + error['message'] for error in cls._errors]

    @classmethod
    def clear_errors(cls):
        """Clear all collected errors"""
        cls._errors.clear()

    @classmethod
    def has_errors(cls) -> bool:
        """Check if any errors were collected"""
        return len(cls._errors) > 0

    @classmethod
    def get_error_count(cls) -> int:
        """Get the number of collected errors"""
        return len(cls._errors)

    @classmethod
    def format_errors_for_display(cls) -> str:
        """Format errors as plain text bullet list for QMessageBox detailed text"""
        if not cls._errors:
            return "No errors"

        bullet_items = "\n".join([f"• {error}<br/>" for error in AICodeError.get_error_messages()])
        return f"Found {cls.get_error_count()} error(s):<br/>{bullet_items}"

    @classmethod
    def set_auto_print(cls, enabled: bool):
        """Enable/disable automatic printing"""
        cls._auto_print = enabled

# To be deleted as it shouldn't be used
class OpCodeNotFound(AICodeError):
    def __init__(self, op_code: int):
        message = f"No op_code defined for op_id: {op_code}"
        super().__init__(message)

class FuncNameNotFound(AICodeError):
    def __init__(self, func_name: str):
        message = f"Didn't find func name: <b>{func_name}</b>"
        super().__init__(message)

class FuncNameUnexpected(AICodeError):
    def __init__(self, func_name_unexpected: str, func_name_expected: str):
        message = f"Unexpected func name: <b>{func_name_unexpected}</b>, expected {func_name_expected}"
        super().__init__(message)

class LineUnexpectedCharaError(AICodeError):
    def __init__(self, chara_unexpected: str, func_name_expected: str):
        message = f"Unexpected <b>{chara_unexpected}</b> in line {func_name_expected}"
        super().__init__(message)
class EmptyLineError(AICodeError):
    def __init__(self):
        message = f"Unexpected empty line"
        super().__init__(message)

class LineError(AICodeError):
    def __init__(self, message: str):
        super().__init__(message)

class BracketError(AICodeError):
    def __init__(self, message: str):
        super().__init__(message)

class SectionError(AICodeError):
    def __init__(self, message: str):
        super().__init__(message)
class ParamCountError(AICodeError):
    def __init__(self, message: str):
        super().__init__(message)

