import argparse
import sys
from .reporting import REPORTERS


def main():
    parser = argparse.ArgumentParser(
        description="Transifex utility scripts for Python docs (Persian team)."
    )

    valid_commands = list(REPORTERS.keys())
    parser.add_argument(
        "command",
        choices=valid_commands,
        help=f"The command to execute. Available commands: {', '.join(valid_commands)}",
    )

    args = parser.parse_args()

    selected_reporter_class = REPORTERS.get(args.command)

    if selected_reporter_class:
        reporter_instance = selected_reporter_class()
        reporter_instance.generate()
    else:
        print(f"Error: Unknown command '{args.command}'.", file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
