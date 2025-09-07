# handlers/__init__.py
"""
Инициализация обработчиков для TeammateBot
"""

from . import start
from . import profile
from . import search
from . import likes

__all__ = ['start', 'profile', 'search', 'likes']