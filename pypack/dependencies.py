import os
import ConfigParser
import subprocess

class MissingBuildDefinition(Exception):
    pass


def read_dependency_tree(pypack_def):
    # Dependencies are returned as their relative paths from
    # the repository root.
    depend_package_dirs = []
    depend_rel_paths = [k for k, v in pypack_def.items("depends")]
    for depend_rel_path in depend_rel_paths:
        depend_abs_path = os.path.join(pypack_def.repository_root,
                                       depend_rel_path)
        depend_package_dirs.append(depend_rel_path)
        try:
            depend_def = parse_pypack_definition(depend_abs_path)
        except MissingBuildDefinition:
            # No build def, so assume it's a module with no depends
            continue

        depend_def.repository_root = pypack_def.repository_root
        depend_package_dirs.extend(read_dependency_tree(depend_def))

    return depend_package_dirs

def parse_pypack_definition(project_dir):
    pypack_definition = os.path.join(project_dir, "PYPACK")
    if not os.path.exists(pypack_definition):
        raise MissingBuildDefinition(pypack_definition)

    parser = ConfigParser.SafeConfigParser(allow_no_value=True)

    parser.read(pypack_definition)
    return parser

def determine_repository_root(project_dir):
    # Git or GTFO.
    git_dir = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                      cwd=project_dir)
    return git_dir.strip()
