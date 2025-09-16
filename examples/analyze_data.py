#!/usr/bin/env python3
"""CLI helper mirroring `coldwatch analyze`."""

import argparse

from coldwatch.analyze import summarize_db


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("db", nargs="?", default="accessibility_log.db")
    args = parser.parse_args()
    summarize_db(args.db)


if __name__ == "__main__":
    main()
