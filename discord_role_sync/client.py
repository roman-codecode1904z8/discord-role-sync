from __future__ import annotations

import random
import time
from typing import Any
import httpx

from discord_role_sync.models import GuildMember, Role


API_BASE = "https://discord.com/api/v10"


class DiscordClient:
    """Barebones Discord REST client covering member and role operations."""

    def __init__(self, token: str, guild_id: int | str, timeout: float = 15.0):
        self.guild_id = str(guild_id)
        clean_token = token.removeprefix("Bot ").strip()
        self._client = httpx.Client(
            base_url=API_BASE,
            headers={
                "Authorization": f"Bot {clean_token}",
                "User-Agent": "discord-role-sync (github.com/sync-tools, 0.1.0)",
            },
            timeout=timeout,
        )

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        max_attempts = 5
        for attempt in range(max_attempts):
            resp = self._client.request(method, path, **kwargs)
            
            if resp.status_code == 429:
                # Check JSON payload first; Discord sometimes includes sub-second precision there
                try:
                    body = resp.json()
                    retry_after = float(body.get("retry_after", 1.0))
                except Exception:
                    retry_after = float(resp.headers.get("Retry-After", 1.0))
                
                # Jitter prevents thundering herd when multi-syncing
                jitter = random.uniform(0.05, 0.2)
                time.sleep(retry_after + jitter)
                continue
                
            if resp.status_code >= 500 and attempt < max_attempts - 1:
                time.sleep(1.0 * (attempt + 1))
                continue

            resp.raise_for_status()
            return resp

        raise RuntimeError(f"Exceeded max retry attempts for {method} {path}")

    def fetch_roles(self) -> dict[int, Role]:
        resp = self._request("GET", f"/guilds/{self.guild_id}/roles")
        roles_data = resp.json()
        out = {}
        for r in roles_data:
            role_id = int(r["id"])
            out[role_id] = Role(
                id=role_id,
                name=r["name"],
                position=r.get("position", 0),
                managed=r.get("managed", False),
            )
        return out

    def fetch_members(self) -> dict[int, GuildMember]:
        members: dict[int, GuildMember]
        members = {}
        after = 0
        limit = 1000

        while True:
            params = {"limit": limit}
            if after > 0:
                params["after"] = after

            resp = self._request("GET", f"/guilds/{self.guild_id}/members", params=params)
            batch = resp.json()
            if not batch:
                break

            for item in batch:
                user_data = item["user"]
                uid = int(user_data["id"])
                role_ids = {int(rid) for rid in item.get("roles", [])}
                username = user_data.get("username", "")
                nick = item.get("nick")
                members[uid] = GuildMember(
                    user_id=uid,
                    username=username,
                    nickname=nick,
                    roles=role_ids,
                )
                if uid > after:
                    after = uid

            if len(batch) < limit:
                break

        return members

    def add_role_to_member(self, user_id: int, role_id: int, reason: str = "") -> None:
        headers = {}
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        self._request(
            "PUT",
            f"/guilds/{self.guild_id}/members/{user_id}/roles/{role_id}",
            headers=headers,
        )

    def remove_role_from_member(self, user_id: int, role_id: int, reason: str = "") -> None:
        headers = {}
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        self._request(
            "DELETE",
            f"/guilds/{self.guild_id}/members/{user_id}/roles/{role_id}",
            headers=headers,
        )
