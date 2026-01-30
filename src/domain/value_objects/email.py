from dataclasses import dataclass
from ..exceptions import DomainValidationError
import re

@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.value):
            raise DomainValidationError(f"Invalid email format: {self.value}")

    def __str__(self):
        return self.value