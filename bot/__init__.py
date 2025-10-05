"""
Discord Voice Bot Package

A Discord bot for automatically creating temporary voice channels.
"""

from .bot import VoiceBot
from .config import setup_logging

__version__ = "2.0.0"
__author__ = "Discord Voice Bot Team"

__all__ = ['VoiceBot', 'setup_logging']
