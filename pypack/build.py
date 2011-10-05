"""
This is kind of a hack, but distutils isn't super friendly
to programmatic access. It really likes to be called from
the shell.
"""
import os
import subprocess
import zipfile
from ConfigParser import NoSectionError
from ConfigParser import NoOptionError

def render_setup_py(name, version, packages):
    this_dir = os.path.dirname(__file__)
    f = open(os.path.join(this_dir,"setup_py_template.txt"), "rb")
    template = f.read()
    f.close()

    setup_py = template % {"name": name,
                           "version": version,
                           "packages": packages}

    return setup_py


def build_project(definition, dependencies):
    project_name = definition.get("project", "name")
    setup_py = render_setup_py(project_name, "1.0", dependencies)

    setup_py_path = os.path.join(definition.repository_root, "setup.py")
    f = open(setup_py_path, "wb")
    f.write(setup_py)
    f.close()

    subprocess.check_call(["python", "setup.py",
                           "build", "--build-lib=build"],
                          cwd=definition.repository_root)


    zip_path = os.path.join(definition.repository_root,
                            "%s.zip" % project_name)
    zip_build(os.path.join(definition.repository_root, "build"), zip_path)


def zip_build(build_path, zip_file_path):
    zip_file = zipfile.ZipFile(zip_file_path, "w",
                               compression=zipfile.ZIP_DEFLATED)
    zip_dir(zip_file, build_path, build_path)
    print build_path
    zip_file.close()


def zip_dir(zip_file, directory, build_root):
    for f in os.listdir(directory):
        f = os.path.join(directory, f)
        if os.path.isfile(f):
            zip_path = os.path.relpath(f, build_root)
            print "Adding %s to zip" % zip_path
            zip_file.write(f, zip_path, zipfile.ZIP_DEFLATED)
        elif os.path.isdir(f):
            print "Descending to %s" % f
            zip_dir(zip_file, f, build_root)
