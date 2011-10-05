import os
import argparse

from dependencies import read_dependency_tree
from dependencies import parse_pypack_definition
from dependencies import determine_repository_root
from build import build_project



def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a production python package")
    parser.add_argument("project",
                        help="Directory of the project to build")
    args = parser.parse_args()
    return args


def get_target_definition(project):
    project_abs_dir = os.path.abspath(project)
    definition = parse_pypack_definition(project_abs_dir)
    definition.repository_root = determine_repository_root(project_abs_dir)
    return definition


def main():
    args = parse_args()
    definition = get_target_definition(args.project)
    depends = read_dependency_tree(definition)

    build_project(definition, depends)

if __name__ == "__main__":
    main()

