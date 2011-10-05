import os
import argparse

from definition import PypackDefinition
from build import build_project



def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a production python package")
    parser.add_argument("project",
                        help="Directory of the project to build")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    definition = PypackDefinition.from_project_directory(args.project)
    build_project(definition)

if __name__ == "__main__":
    main()

