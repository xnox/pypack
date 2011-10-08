"""
This is kind of a hack, but distutils isn't super friendly
to programmatic access. It really likes to be called from
the shell.
"""
import os
import subprocess
import shutil
import logging
from StringIO import StringIO

LOG = logging.getLogger(__name__)


def render_setup_py(name, version, packages, package_data):
    this_dir = os.path.dirname(__file__)
    f = open(os.path.join(this_dir,"setup_py_template.txt"), "rb")
    template = f.read()
    f.close()

    setup_py = template % {"name": name,
                           "version": version,
                           "packages": packages,
                           "package_data": package_data}

    return setup_py


def render_wrapped_binary(zip_file_basename, entry_module):
    this_dir = os.path.dirname(__file__)
    f = open(os.path.join(this_dir, "wrapped_binary_template.txt"), "rb")
    template = f.read()
    f.close()

    return template % {"zip_file": zip_file_basename,
                       "entry_module": entry_module}


def write_setup_py(definition):
    dependent_modules = definition.all_dependencies["modules"]
    package_data = definition.all_dependencies["internal_data_paths"]
    setup_py = render_setup_py(definition.project_name,
                               "1.0", dependent_modules,
                               package_data)

    setup_py_path = os.path.join(definition.repository_root, "setup.py")
    f = open(setup_py_path, "wb")
    f.write(setup_py)
    f.close()
    LOG.info("Wrote setup.py to %s", setup_py_path)

    return setup_py_path


def write_wrapped_binary(zip_basename, binary):
    wrapped_binary = render_wrapped_binary(zip_basename,
                                           binary.entry_module_path)
    f = open(binary.output_path, "wb")
    f.write(wrapped_binary)
    f.close()
    os.chmod(binary.output_path, 0755)
    LOG.info("Wrote binary '%s' to %s",
             binary.binary_name, binary.output_path)



def zip_build_dir(definition):
    build_dir = os.path.join(definition.repository_root, "build")
    shutil.make_archive(base_name=definition.project_name,
                        format="zip",
                        root_dir=build_dir)

    return "%s.zip" % definition.project_name


def make_external_data_dir(definition):
    data_rel_paths = definition.all_dependencies["external_data_paths"]
    if not data_rel_paths:
        return
    data_dir = os.path.join(definition.repository_root,
                            "%s_data" % definition.project_name)
    if os.path.exists(data_dir):
        LOG.info("External data dir %s exists, removing", data_dir)
        shutil.rmtree(data_dir)

    os.mkdir(data_dir)
    LOG.info("Made external data dir %s", data_dir)

    return data_dir

def copy_data_entries(definition, data_dir):
    """
    Copy both the external data definitions.
    "external data" gets written to a projectname_data directory,
    outside of the zipped package of dependencies.
    """
    for repo_rel_path in definition.all_dependencies["external_data_paths"]:
        destination_abs_path = os.path.join(definition.repository_root,
                                            data_dir,
                                            repo_rel_path)
        source_abs_path = os.path.join(definition.repository_root,
                                       repo_rel_path)
        destination_dir = os.path.dirname(destination_abs_path)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        # Copies file + metadata
        shutil.copy2(source_abs_path, destination_abs_path)
        LOG.info("Copied %s --> %s", source_abs_path, destination_abs_path)


def run_setup_py(setup_py_path, build_dir, repo_root):
    stderr = stdout = open("/dev/null", "wb")

    if LOG.isEnabledFor(logging.INFO):
        stderr = None
        stdout = None

    subprocess.check_call(["python", setup_py_path,
                           "build", "--build-lib=%s" % build_dir],
                          cwd=repo_root,
                          stderr=stderr,
                          stdout=stdout)



def build_project(definition):
    build_dir = os.path.join(definition.repository_root, "build")

    setup_py_path = write_setup_py(definition)
    run_setup_py(setup_py_path, build_dir, definition.repository_root)
    zip_basename = zip_build_dir(definition)

    for binary in definition.binaries:
        write_wrapped_binary(zip_basename, binary)

    data_dir = make_external_data_dir(definition)
    copy_data_entries(definition, data_dir)


    # Cleanup
    shutil.rmtree(build_dir)
    os.remove(setup_py_path)

