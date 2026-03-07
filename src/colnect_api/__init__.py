"""Colnect browser automation module for stamp collection management.

This module provides Chrome DevTools Protocol (CDP) browser automation to interact
with Colnect.com. It connects to an existing Chrome session via CDP, verifies
user login state, and performs collection operations like adding stamps.

Prerequisites
-------------
1. Start Chrome with remote debugging enabled:
   & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222

2. Log into Colnect manually in that Chrome session

3. Set CHROME_CDP_URL in .env.app (default: http://localhost:9222)

Modules
-------
session.py
    CDPSession: Manages Chrome DevTools Protocol connection. Connects to existing
    Chrome instance, verifies Colnect login state, and provides page automation.

actions.py
    ColnectActions: Performs collection operations on Colnect.com. Supports adding
    stamps to collection with condition, quantity, and comments. Checks ownership
    status and handles duplicate detection.

Key Exports
-----------
- CDPSession: CDP connection and session management
- ColnectActions: Collection operations (add stamp, check owned)
- create_colnect_session: Factory function for CDPSession
- create_colnect_actions: Factory function for ColnectActions with session
"""

from src.colnect_api.session import CDPSession, create_colnect_session
from src.colnect_api.actions import ColnectActions, create_colnect_actions

__all__ = [
    "CDPSession",
    "ColnectActions",
    "create_colnect_session",
    "create_colnect_actions",
]
