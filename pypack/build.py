"""
This is kind of a hack, but distutils isn't super friendly
to programmatic access. It really likes to be called from
the shell.
"""
import os
import subprocess
import shutil


def render_setup_py(name, version, packages):
    this_dir = os.path.dirname(__file__)
    f = open(os.path.join(this_dir,"setup_py_template.txt"), "rb")
    template = f.read()
    f.close()

    setup_py = template % {"name": name,
                           "version": version,
                           "packages": packages}

    return setup_py


def render_wrapped_binary(zip_file_basename, entry_module):
    this_dir = os.path.dirname(__file__)
    f = open(os.path.join(this_dir, "wrapped_binary_template.txt"), "rb")
    template = f.read()
    f.close()

    return template % {"zip_file": zip_file_basename,
                       "entry_module": entry_module}


def write_setup_py(definition):
    setup_py = render_setup_py(definition.project_name,
                               "1.0", definition.all_dependent_modules())

    setup_py_path = os.path.join(definition.repository_root, "setup.py")
    f = open(setup_py_path, "wb")
    f.write(setup_py)
    f.close()

    return setup_py_path

def write_wrapped_binary(zip_basename, binary):
    wrapped_binary = render_wrapped_binary(zip_basename,
                                           binary.entry_module_path)
    f = open(binary.output_path, "wb")
    f.write(wrapped_binary)
    f.close()
    os.chmod(binary.output_path, 0755)



def zip_build_dir(definition):
    build_dir = os.path.join(definition.repository_root, "build")
    shutil.make_archive(base_name=definition.project_name,
                        format="zip",
                        root_dir=build_dir)

    return "%s.zip" % definition.project_name


def make_data_dir(definition):
    data_rel_paths = definition.all_dependent_data_paths()
    if not data_rel_paths:
        return
    data_dir = os.path.join(definition.repository_root,
                            "%s_data" % definition.project_name)
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    return data_dir

def copy_data_entries(definition, data_dir):
    for repo_rel_path in definition.all_dependent_data_paths():
        destination_abs_path = os.path.join(definition.repository_root,
                                            data_dir,
                                            repo_rel_path)
        source_abs_path = os.path.join(definition.repository_root,
                                       repo_rel_path)
        shutil.copytree(source_abs_path, destination_abs_path)


def build_project(definition):
    setup_py_path = write_setup_py(definition)

    build_dir = os.path.join(definition.repository_root, "build")
    subprocess.check_call(["python", setup_py_path,
                           "build", "--build-lib=%s" % build_dir],
                          cwd=definition.repository_root)

    zip_basename = zip_build_dir(definition)

    for binary in definition.binaries:
        write_wrapped_binary(zip_basename, binary)

    data_dir = make_data_dir(definition)
    copy_data_entries(definition, data_dir)


    # Cleanup
    shutil.rmtree(build_dir)
    os.remove(setup_py_path)

