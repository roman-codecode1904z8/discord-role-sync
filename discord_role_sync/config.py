import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    token: str
    guild_id: int
    api_base: str = "https://discord.com/api/v10"
    timeout: float = 20.0
    max_retries: int = 5
    rate_limit_buffer: float = 0.15
    audit_reason: str = "discord-role-sync state reconcile"
    dry_run: bool = False


def load_config(guild_override: Optional[int] = None, dry_run: bool = False) -> Config:
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        token = os.getenv("DISCORD_TOKEN", "").strip()
    
    if not token:
        raise ValueError("Missing DISCORD_BOT_TOKEN or DISCORD_TOKEN in environment.")

    guild_raw = guild_override or os.getenv("DISCORD_GUILD_ID")
    if not guild_raw:
        raise ValueError("Missing target guild ID. Provide --guild or DISCORD_GUILD_ID.")

    try:
        gid = int(guild_raw)
    except ValueError:
        raise ValueError(f"Invalid guild ID '{guild_raw}', must be an integer snowflake.")

    custom_reason = os.getenv("DISCORD_SYNC_REASON", "discord-role-sync automated update").strip()
    timeout_raw = float(os.getenv("DISCORD_HTTP_TIMEOUT", "20.0"))

    return Config(
        token=token,
        guild_id=gid,
        timeout=timeout_raw,
        audit_reason=custom_reason,
        dry_run=dry_run,
    )
