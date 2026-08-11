import argparse
import sys
from pathlib import Path
from typing import List, Optional

from discord_role_sync.config import load_config
from discord_role_sync.client import DiscordClient
from discord_role_sync.sources import load_state_file, dump_state_file
from discord_role_sync.diff import calculate_diff
from discord_role_sync.executor import SyncExecutor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="discord-role-sync",
        description="Batch sync and reconcile Discord server roles from state files.",
    )
    parser.add_argument("-g", "--guild", type=int, help="Discord guild ID (overrides DISCORD_GUILD_ID)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")

    sub = parser.add_subparsers(dest="command", required=True)

    # plan
    p_plan = sub.add_parser("plan", help="Show diff between state file and live guild without mutating anything")
    p_plan.add_argument("-f", "--file", type=Path, required=True, help="Path to desired state file")
    p_plan.add_argument("--ignore-managed", action="store_true", default=True, help="Skip bot/integration managed roles")

    # apply
    p_apply = sub.add_parser("apply", help="Reconcile server state with state file")
    p_apply.add_argument("-f", "--file", type=Path, required=True, help="Path to desired state file")
    p_apply.add_argument("-y", "--yes", action="store_true", help="Execute without confirmation prompt")
    p_apply.add_argument("--dry-run", action="store_true", help="Simulate API calls without applying changes")
    p_apply.add_argument("--batch-size", type=int, default=10, help="Concurrent requests batch size")

    # export / dump
    p_dump = sub.add_parser("export", aliases=["dump"], help="Dump current guild roles and members to file")
    p_dump.add_argument("-o", "--output", type=Path, default=Path("discord-state.yaml"), help="Output path")
    p_dump.add_argument("--include-members", action="store_true", default=True, help="Include user role assignments")

    return parser


def run_plan(args, client: DiscordClient) -> int:
    desired = load_state_file(args.file)
    remote_roles = client.fetch_roles()
    remote_members = client.fetch_members()

    plan = calculate_diff(remote_roles, remote_members, desired)
    if not plan:
        print("Everything in sync. No actions required.")
        return 0

    print(f"Planned actions ({len(plan)} total):")
    for action in plan:
        prefix = "+" if "add" in action.action_type.value or "create" in action.action_type.value else "-"
        print(f"  {prefix} [{action.action_type.value}] {action.target_name} -> role: {action.role_name or action.role_id}")
    return 0


def run_apply(args, client: DiscordClient, config) -> int:
    desired = load_state_file(args.file)
    remote_roles = client.fetch_roles()
    remote_members = client.fetch_members()

    plan = calculate_diff(remote_roles, remote_members, desired)
    if not plan:
        print("Guild is already in sync with state file.")
        return 0

    print(f"Found {len(plan)} changes to apply.")
    for action in plan:
        print(f"  * {action.action_type.value}: {action.target_name} ({action.role_name})")

    if not args.yes and not args.dry_run:
        # Simple prompt to prevent accidental server-wide wipeouts
        resp = input("\nProceed with changes? [y/N]: ").strip().lower()
        if resp not in ("y", "yes"):
            print("Aborted.")
            return 0

    executor = SyncExecutor(client, dry_run=args.dry_run or config.dry_run)
    executor.execute(plan)
    print("Sync finished successfully.")
    return 0


def run_export(args, client: DiscordClient) -> int:
    roles = client.fetch_roles()
    members = client.fetch_members() if args.include_members else []
    # print(f"DEBUG: fetched {len(roles)} roles, {len(members)} members")
    dump_state_file(args.output, roles, members)
    print(f"Exported live state to {args.output}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    dry_run = getattr(args, "dry_run", False)
    try:
        cfg = load_config(guild_override=args.guild, dry_run=dry_run)
    except ValueError as err:
        sys.stderr.write(f"Configuration error: {err}\n")
        return 1

    # TODO: allow passing state content from stdin via '-' as filename
    client = DiscordClient(cfg)

    try:
        if args.command == "plan":
            return run_plan(args, client)
        elif args.command == "apply":
            return run_apply(args, client, cfg)
        elif args.command in ("export", "dump"):
            return run_export(args, client)
        else:
            parser.print_help()
            return 1
    except Exception as exc:
        if args.verbose:
            raise
        sys.stderr.write(f"Error: {exc}\n")
        return 1
