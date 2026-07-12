class ValidationEngineError(Exception):
    """Base exception for the validation engine."""

    pass


class ValidationError(ValidationEngineError):
    """Base exception for rule validation failures."""

    pass


class SchemaError(ValidationEngineError):
    """Raised when the schema structure or columns do not match expected types."""

    pass


class DuplicateKeyError(ValidationError):
    """Raised when primary keys or unique constraint checks find duplicates."""

    pass


class ForeignKeyError(ValidationError):
    """Raised when foreign key constraints are violated."""

    pass


class CriticalRuleViolation(ValidationEngineError):
    """Raised when a critical validation rule is violated."""

    pass


class DataLoadError(ValidationEngineError):
    """Raised when data loading fails."""

    pass
