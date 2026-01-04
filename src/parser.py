import re
from typing import List, TYPE_CHECKING
from pipeline import CommandPipeline
from environment import EnvironmentManager

if TYPE_CHECKING:
    pass

class CommandParser:
    """Парсит команды из строки."""
    
    def __init__(self, env_manager: EnvironmentManager) -> None:
        self.env_manager = env_manager
        self.tokenizer = Tokenizer()
        self.quote_handler = QuoteHandler()
        self.var_substitutor = VariableSubstitutor(env_manager)

    def parse(self, input_str: str) -> CommandPipeline:
        tokens = self.tokenizer.tokenize(input_str)
        tokens = self.quote_handler.process_quotes(tokens)
        tokens = self.var_substitutor.substitute_variables(tokens)
        return self.build_pipeline(tokens)

    def build_pipeline(self, tokens: List[str]) -> CommandPipeline:
        commands: List[List[str]] = []
        current_cmd: List[str] = []
        stdout_file = None
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == '|':
                if current_cmd:
                    commands.append(current_cmd)
                    current_cmd = []
            elif token == '>':
                if i + 1 < len(tokens):
                    stdout_file = tokens[i + 1]
                    i += 1  # skip the filename
                # ignore further tokens after >
            else:
                current_cmd.append(token)
            i += 1
        
        if current_cmd:
            commands.append(current_cmd)
        
        return CommandPipeline(commands, stdout_file)

class Tokenizer:
    """Токенизатор для разбиения строки на токены."""
    
    def tokenize(self, input_str: str) -> List[str]:
        # Простая токенизация: разделение по пробелам, но с учетом кавычек
        tokens: List[str] = []
        current_token = ""
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(input_str):
            char = input_str[i]
            
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_token += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                current_token += char
                quote_char = None
            elif char == ' ' and not in_quotes:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            elif char == '|':
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append('|')
            elif char == '>':
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append('>')
            else:
                current_token += char
            
            i += 1
        
        if current_token:
            tokens.append(current_token)
        
        return tokens

class QuoteHandler:
    """Обработчик кавычек."""
    
    def process_quotes(self, tokens: List[str]) -> List[str]:
        # Удаление кавычек и обработка содержимого
        processed: List[str] = []
        for token in tokens:
            if token.startswith('"') and token.endswith('"'):
                processed.append(token[1:-1])
            elif token.startswith("'") and token.endswith("'"):
                processed.append(token[1:-1])
            else:
                processed.append(token)
        return processed

class VariableSubstitutor:
    """Подстановщик переменных окружения."""
    
    def __init__(self, env_manager: EnvironmentManager) -> None:
        self.env_manager = env_manager

    def substitute_variables(self, tokens: List[str]) -> List[str]:
        substituted: List[str] = []
        for token in tokens:
            # Подстановка переменных вида $VAR
            substituted_token = re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)', 
                                     lambda m: self.env_manager.get_var(m.group(1), ''), 
                                     token)
            substituted.append(substituted_token)
        return substituted
