import sys
from discord_role_sync.cli import main

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # Don't vomit a stacktrace when aborted in terminal
        sys.stderr.write("\nAborted.\n")
        sys.exit(130)
