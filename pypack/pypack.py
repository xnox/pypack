import os
import argparse
import subprocess
import logging

from definition import PypackDefinition
from build import build_project



def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a production python package")
    parser.add_argument("project",
                        help="Directory of the project to build")
    parser.add_argument("-r", "--repo-root",
                        help="The path to the root of the "
                        "source repository. Default is to guess.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Say a lot about what's going on",
                        default=False)
    parser.add_argument("-o", "--output",
                        default="$REPO_ROOT/projectname_PYPACK",
                        help="The directory to output build files")
    args = parser.parse_args()
    return args


def get_repo_root(args):
    if not args.repo_root:
        git_dir = subprocess.check_output(["git", "rev-parse",
                                           "--show-toplevel"])
        return git_dir.strip()
    return os.path.abspath(args.repo_root)


def get_output_directory(args, repo_root, definition):
    if args.output == "$REPO_ROOT/projectname_PYPACK":
        basename = "%s_PYPACK" % (definition.project_name)
        return os.path.join(repo_root, basename)
    return os.path.abspath(args.output)


def configure_logging(args):
    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    logging.basicConfig(level=log_level)


def main():
    args = parse_args()
    configure_logging(args)
    repo_root = get_repo_root(args)

    definition = PypackDefinition.from_project_directory(
        args.project, repo_root)

    output_directory = get_output_directory(args, repo_root, definition)
    build_project(definition, output_directory)

if __name__ == "__main__":
    main()

