#!/usr/bin/env python3

from yaml import safe_load
from pathlib import Path
import argparse

def main(args):
    with open(args.datapath, "r") as f:
        conf = safe_load(f)

    for section in conf:
        print(section)

    print(conf)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('datapath', type=Path)
    args = parser.parse_args()
    main(args)
