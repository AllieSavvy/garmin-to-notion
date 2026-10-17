"""Garmin and Notion client initialization using native Garmin authentication."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from garminconnect import Garmin as GarminClient
from notion_client import Client as NotionClient

from garmin_to_notion.config import Settings

logger = logging.getLogger(__name__)
TOKENSTORE_DIR = Path(os.getenv("GARMIN_TOKENSTORE", "~/.garmin_tokens")).expanduser()


@dataclass
class Clients:
    garmin: GarminClient
    notion: NotionClient


def _request_mfa() -> str:
    raise RuntimeError("Garmin requires interactive MFA; unattended login cannot continue.")


def init_clients(settings: Settings) -> Clients:
    """Resume native tokens or authenticate once with the configured credentials.

    garminconnect 0.3 uses native DI OAuth, replacing the obsolete garth
    OAuth1 exchange. login(tokenstore) saves and refreshes its own tokens.
    Let the library manage authentication; do not repeat failed login chains.
    """
    logger.info("Authenticating with Garmin Connect using native DI OAuth...")
    TOKENSTORE_DIR.mkdir(parents=True, exist_ok=True)
    garmin = GarminClient(
        settings.garmin_email,
        settings.garmin_password,
        prompt_mfa=_request_mfa,
    )
    try:
        garmin.login(str(TOKENSTORE_DIR))
    except Exception as exc:
        logger.error("Garmin authentication failed (%s).", type(exc).__name__)
        raise SystemExit(1) from None
    logger.info("Garmin authentication successful.")
    return Clients(garmin=garmin, notion=NotionClient(auth=settings.notion_token))


def init_notion_only(settings: Settings) -> NotionClient:
    """Initialize only Notion for tools that do not need Garmin."""
    return NotionClient(auth=settings.notion_token)
