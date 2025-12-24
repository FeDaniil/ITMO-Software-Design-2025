from abc import ABC, abstractmethod
from typing import IO, TYPE_CHECKING

if TYPE_CHECKING:
    from environment import EnvironmentManager

class Command(ABC):
    """Базовый класс для всех команд."""
    
    @abstractmethod
    def execute(self, env_manager: 'EnvironmentManager', stdin: IO[str], stdout: IO[str], stderr: IO[str]) -> int:
        """Выполняет команду и возвращает код выхода."""
        pass
