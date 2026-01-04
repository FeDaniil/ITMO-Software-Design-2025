# SD-CLI

ITMO Software Design Labs. CLI - это простой интерпретатор командной строки, написанный на Python. Он поддерживает выполнение встроенных команд, внешних команд, переменные окружения и пайплайны.

## Функциональность

- **Встроенные команды**: echo, cat, pwd, wc, grep, assignment (для переменных), exit
- **Внешние команды**: выполнение системных команд
- **Переменные окружения**: поддержка переменных, включая PS1 для промпта
- **Пайплайны**: поддержка | для перенаправления вывода между командами
- **Перенаправление вывода**: поддержка > для записи вывода команды в файл
- **Обработка ошибок**: базовая обработка исключений

## Установка

### Требования

- Python >= 3.11
- `uv` - быстрый менеджер пакетов для Python (установите с [официального сайта](https://github.com/astral-sh/uv))

### Шаги установки

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/FeDaniil/ITMO-Software-Design-2025.git
   cd ITMO-Software-Design-2025
   ```

2. **Создайте виртуальное окружение и установите зависимости**:
   ```bash
   uv sync
   ```

## Запуск

### Запуск CLI

```bash
uv run python main.py
```

### Запуск тестов

```bash
uv run pytest
```

Тесты находятся в папке `tests/` и проверяют функциональность команд и CLI.

## Документация

- **Архитектура**: Подробное описание архитектуры системы см. в [`architecture/CLI/README.md`](architecture/CLI/README.md).
- **Задачи**: Описания домашних заданий находятся в папке [`tasks/`](tasks/) (PDF файлы).

## Структура проекта

- `src/`: исходный код
  - `main.py`: точка входа
  - `cli.py`: основной класс CLI
  - `parser.py`: парсер команд
  - `executor.py`: исполнитель команд
  - `environment.py`: менеджер переменных окружения
  - `pipeline.py`: обработка пайплайнов
  - `registry.py`: реестр команд
  - `commands/`: реализации команд
- `tests/`: тесты
- `pyproject.toml`: конфигурация проекта
- `architecture/`: документация архитектуры (см. `architecture/CLI/README.md`)
- `tasks/`: описания задач (PDF файлы)

## Использование

После запуска `uv run python main.py` вы увидите промпт `$ `. Введите команды, например:

- `echo hello world`
- `pwd`
- `cat file.txt | wc`
- `x=5; echo $x`
- `grep hello file.txt` - поиск строк, содержащих "hello" в файле
- `echo "hello\nworld\nhello" | grep -i hello` - поиск с игнорированием регистра
- `grep -w word file.txt` - поиск целых слов
- `grep -A 2 pattern file.txt` - вывод 2 строк после совпадения
- `echo "test" > file.txt` - записать "test" в файл
- `cat file.txt | grep pattern > output.txt` - найти строки и записать в файл

### Команды

#### grep
Поиск строк, соответствующих регулярному выражению.

**Синтаксис**: `grep [OPTIONS] PATTERN [FILE...]`

**Опции**:
- `-w`: Поиск целых слов
- `-i`: Игнорирование регистра
- `-A NUM`: Вывод NUM строк после совпадения

**Примеры**:
- `grep hello file.txt`
- `echo "Hello World" | grep -i hello`
- `grep -w test *.txt`

## Авторы

- Andrey Perevoshikov
- Vadim Kozlov
- Daniil Fedorov