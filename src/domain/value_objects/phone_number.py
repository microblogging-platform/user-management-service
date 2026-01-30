from dataclasses import dataclass
from ..exceptions import DomainValidationError

@dataclass(frozen=True)
class PhoneNumber:
    value: str

    def __post_init__(self):
        if not self.value.isdigit() or len(self.value) < 10:
            raise DomainValidationError("Phone must contain digits")

    def format_international(self) -> str:
        return f"+{self.value}"