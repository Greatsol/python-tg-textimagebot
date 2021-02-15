import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Bot script")
parser.add_argument(
    "-c",
    type=lambda p: Path(p).absolute(),
    help="Path to .env config file",
    default=(Path("cfg") / ".env").absolute(),
)
args = parser.parse_args()

CONFIG_FILE = args.c
is_initialized = True
