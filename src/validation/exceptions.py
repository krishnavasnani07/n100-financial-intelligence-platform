class ValidationEngineError(Exception):
    """Base exception for the validation engine."""



class ValidationError(ValidationEngineError):
    """Base exception for rule validation failures."""



class SchemaError(ValidationEngineError):
    """Raised when the schema structure or columns do not match expected types."""



class DuplicateKeyError(ValidationError):
    """Raised when primary keys or unique constraint checks find duplicates."""



class ForeignKeyError(ValidationError):
    """Raised when foreign key constraints are violated."""



class CriticalRuleViolation(ValidationEngineError):
    """Raised when a critical validation rule is violated."""



class DataLoadError(ValidationEngineError):
    """Raised when data loading fails."""

