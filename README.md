# discord-role-sync

I built this because running a 24/7 Discord bot daemon just to keep member roles in sync with an external database or YAML dump felt like overkill. This is a one-shot CLI tool that reads a state file, checks current guild state over the REST API, diffs them, and applies only the needed changes.

## Install

```bash
pip install -e .
```

Requires Python 3.10+.

## Configuration

Set your bot token:

```bash
export DISCORD_BOT_TOKEN="your-bot-token"
```

The bot needs `MANAGE_ROLES` permission and must sit higher in the role hierarchy than the roles it manages.

## State file format

Both YAML and JSON are supported. You can match roles by name or snowflake ID.

```yaml
version: 1
roles:
  - name: "Backer"
    members:
      - "123456789012345678"
      - "987654321098765432"
  - id: "223344556677889900"
    name: "VIP"
    members:
      - "123456789012345678"
```

## Usage

See what would change without modifying anything:

```bash
drs diff --guild 111222333444 --file roles.yaml
```

Apply changes:

```bash
drs apply --guild 111222333444 --file roles.yaml
```

By default it won't remove roles from members who aren't listed in the file. If you want strict reconciliation (remove roles from unlisted users), pass `--prune`:

```bash
drs apply --guild 111222333444 --file roles.yaml --prune
```

Rate limits are handled automatically with backoff, but for large guilds (>10k members) fetching the full member list can take a minute.
