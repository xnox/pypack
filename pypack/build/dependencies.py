import os
import logging
import shutil
import fnmatch

LOG = logging.getLogger(__name__)

# TODO: bring this out to a file a-la .gitignore
IGNORE_PATTERNS = ["*.pyc", ".*"]
SO_PATTERNS = ["*.so", "*.pyd"]


def copy_dependencies(build_plan):
    """
    Walk the dependency tree and copy files into the build
    directory.

    This will also copy third_party modules with C extensions
    into the third_party_cext directory, which will not be zipped,
    as .so module cannot be zipimport'ed.
    """

    dynamic_libs = []
    for dependency_def in build_plan.target_definition.dependency_list:
        has_dynamic = _copy_dependency(dependency_def, build_plan)
        if has_dynamic:
            dynamic_libs.append(dependency_def)

    for dynamic_def in dynamic_libs:
        _move_dynamic_library(dynamic_def, build_plan)


def _move_dynamic_library(dependency_def, build_plan):
    LOG.info("Moving dynamic library %s", dependency_def.module_py_path)
    destination = build_plan.get_thirdparty_cext_dest(dependency_def)
    if os.path.exists(destination):
        LOG.debug("Removing dynamic lib directory %s", destination)
        shutil.rmtree(destination)

    shutil.move(build_plan.get_module_build_dest(dependency_def),
                destination)


def _copy_dependency(dependency_def, build_plan):
    """
    Hacky, but returns True if this dependency has a .so/.pyd
    file in it (as that can't be zipped and needs separate handling).
    """
    module_abs_path = dependency_def.project_absolute_path
    has_dynamic = False

    LOG.info("Copying dependency %s", dependency_def.module_py_path)
    # Technically, this should go in definition.py, as the paths
    # to the dependencies properties of the definition.
    for dir_path, directories, files in os.walk(module_abs_path):
        for file_name in files:
            if _should_ignore(file_name):
                LOG.debug("File %s fits IGNORE_PATTERNS, ignoring", file_name)
                continue

            if not has_dynamic and is_dynamic_module(file_name):
                LOG.debug("Found dynamic libraries in %s", file_name)
                has_dynamic = True

            src_abs_path = os.path.join(dir_path, file_name)
            dest_abs_path = build_plan.get_file_build_dest(src_abs_path)

            dest_dir = os.path.dirname(dest_abs_path)
            if not os.path.exists(dest_dir):
                LOG.debug("Making directory %s", dest_dir)
                os.makedirs(dest_dir)

            shutil.copy2(src_abs_path, dest_abs_path)
            LOG.debug("Copied %s --> %s", src_abs_path, dest_abs_path)

    copy_ancestor_init_py(dependency_def, build_plan)

    return has_dynamic


def copy_ancestor_init_py(dependency_def, build_plan):
    # TODO: bitch in documentation about __init__.py and why I need this.
    module_chunks = dependency_def.project_repo_rel_path.split(os.path.sep)
    for i in xrange(1, len(module_chunks)):
        ancestor_module_path = os.path.join(dependency_def.repository_root,
                                                *module_chunks[0:i])
        ancestor_init_path = os.path.join(dependency_def.repository_root,
                                          ancestor_module_path,
                                          "__init__.py")
        if os.path.exists(ancestor_init_path):
            destination = build_plan.get_file_build_dest(ancestor_init_path)
            shutil.copy2(ancestor_init_path, destination)

def _should_ignore(file_name):
    for ignore_pattern in IGNORE_PATTERNS:
        if fnmatch.fnmatch(file_name, ignore_pattern):
            return True
    return False


def is_dynamic_module(file_name):
    for so_pattern in SO_PATTERNS:
        if fnmatch.fnmatch(file_name, so_pattern):
            return True
    return False
