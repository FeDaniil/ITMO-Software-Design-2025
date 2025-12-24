import sys
from importlib import import_module

_messages_module = import_module(".chat_pb2", package=__name__)

sys.modules.setdefault("chat_pb2", _messages_module)
