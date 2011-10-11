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


def render_wrapped_binary(zip_file_basename, binary):
    this_dir = os.path.dirname(__file__)
    f = open(os.path.join(this_dir, "wrapped_binary_template.txt"), "rb")
    template = f.read()
    f.close()

    entry_module = binary.entry_module_path
    pythonpath_additions = " ".join(binary.relative_pythonpath_additions)


    return template % {"pythonpath_additions": pythonpath_additions,
                       "zip_file_basename": zip_file_basename,
                       "entry_module": entry_module}



def write_wrapped_binary(zip_path, binary, build_dir):
    wrapped_binary = render_wrapped_binary(os.path.basename(zip_path),
                                           binary.entry_module_path)
    output_path = os.path.join(build_dir, binary.binary_name)
    f = open(output_path, "wb")
    f.write(wrapped_binary)
    f.close()
    os.chmod(output_path, 0755)
    LOG.info("Wrote binary '%s' to %s",
             binary.binary_name, output_path)



def zip_build_dir(definition, build_dir, output_dir):
    base_name = os.path.join(output_dir, definition.project_name)
    shutil.make_archive(base_name=base_name,
                        format="zip",
                        root_dir=build_dir)

    return "%s.zip" % base_name







def build_project(definition, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    build_dir = os.path.join(output_directory, "build")

    setup_py_path = write_setup_py(definition)
    run_setup_py(setup_py_path, build_dir, definition.repository_root)
    move_third_party_c_extensions(build_dir, output_directory)
    zip_path = zip_build_dir(definition, build_dir, output_directory)

    for binary in definition.binaries:
        write_wrapped_binary(zip_path, binary, output_directory)

    data_dir = make_external_data_dir(definition, output_directory)
    copy_data_entries(definition, data_dir)


    # Cleanup
    shutil.rmtree(build_dir)
    os.remove(setup_py_path)

