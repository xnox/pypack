"""
This is kind of a hack, but distutils isn't super friendly
to programmatic access. It really likes to be called from
the shell.
"""
import os
import subprocess
import zipfile


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


def get_entry_module(binary_name, pypack_definition):
    project_relative_path = os.path.relpath(pypack_definition.project_abs_dir,
                                            pypack_definition.repository_root)
    module_path = project_relative_path.replace(os.path.sep, ".")
    binary_file = pypack_definition.get("binaries", binary_name)
    if binary_file.endswith(".py"):
        binary_file = binary_file[:-3]

    entry_module = "%s.%s" % (module_path, binary_file)
    return entry_module


def write_init_py(build_dir):
    f = open(os.path.join(build_dir, "__init__.py"), "wb")
    f.close()


def build_project(definition):
    setup_py = render_setup_py(definition.project_name,
                               "1.0", definition.all_dependent_modules)

    setup_py_path = os.path.join(definition.repository_root, "setup.py")
    f = open(setup_py_path, "wb")
    f.write(setup_py)
    f.close()

    subprocess.check_call(["python", "setup.py",
                           "build", "--build-lib=build/lib"],
                          cwd=definition.repository_root)
    write_init_py(os.path.join(definition.repository_root, "build", "lib"))

    zip_basename = "%s.zip" % definition.project_name
    zip_path = os.path.join(definition.repository_root,
                            zip_basename)
    zip_build(os.path.join(definition.repository_root, "build"), zip_path)

    for binary in definition.binaries:
        wrapped_binary = render_wrapped_binary(zip_basename,
                                               binary.entry_module_path)
        f = open(binary.output_path, "wb")
        f.write(wrapped_binary)
        f.close()
        os.chmod(binary.output_path, 0755)


def zip_build(build_path, zip_file_path):
    zip_file = zipfile.ZipFile(zip_file_path, "w",
                               compression=zipfile.ZIP_DEFLATED)
    zip_dir(zip_file, build_path, build_path)
    zip_file.close()



def zip_dir(zip_file, directory, build_root):
    for f in os.listdir(directory):
        f = os.path.join(directory, f)
        if os.path.isfile(f):
            zip_path = os.path.relpath(f, build_root)
            zip_file.write(f, zip_path, zipfile.ZIP_DEFLATED)
        elif os.path.isdir(f):
            zip_dir(zip_file, f, build_root)


