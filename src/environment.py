from typing import Dict, Optional


class EnvironmentManager:
    """Управляет переменными окружения."""

    def __init__(self, initial_vars: Optional[Dict[str, str]] = None) -> None:
        self.variables: Dict[str, str] = initial_vars or {}

    def get_var(self, name: str, default: str = '') -> str:
        return self.variables.get(name, default)

    def set_var(self, name: str, value: str) -> None:
        self.variables[name] = value

    def get_all_vars(self) -> Dict[str, str]:
        return self.variables.copy()
