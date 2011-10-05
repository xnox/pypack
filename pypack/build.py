"""
This is kind of a hack, but distutils isn't super friendly
to programmatic access. It really likes to be called from
the shell.
"""
import os
import subprocess
import zipfile
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
                               "1.0", definition.all_dependent_modules)

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
    zip_basename = "%s.zip" % definition.project_name
    zip_path = os.path.join(definition.repository_root,
                            zip_basename)
    zip_build(build_dir, zip_path)
    return zip_basename



def build_project(definition):
    setup_py_path = write_setup_py(definition)

    build_dir = os.path.join(definition.repository_root, "build")
    subprocess.check_call(["python", setup_py_path,
                           "build", "--build-lib=%s" % build_dir],
                          cwd=definition.repository_root)

    zip_basename = zip_build_dir(definition)

    for binary in definition.binaries:
        write_wrapped_binary(zip_basename, binary)


    # Cleanup
    shutil.rmtree(build_dir)
    os.remove(setup_py_path)


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


