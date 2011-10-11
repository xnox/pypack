import os
import logging
import pkg_resources
import shutil

LOG = logging.getLogger(__name__)


def write_binaries(build_plan):
    for binary in build_plan.target_definition.binaries:
        if not binary.is_py_binary():
            copy_non_py_binary(build_plan, binary)

        write_wrapped_binary(binary, build_plan)


def copy_non_py_binary(build_plan, binary):
    src = binary.abs_path
    dst = build_plan.get_non_py_binary_destination(binary)

    shutil.copy2(src, dst)
    LOG.debug("Copied non-py binary %s --> %s", src, dst)


def render_wrapped_binary(binary, build_plan):
    manager = pkg_resources.ResourceManager()
    provider = pkg_resources.get_provider("pypack.build")

    template = provider.get_resource_string(manager,
                                            "wrapped_binary_template.txt")

    invocation = "$EXEC_DIR/.wrapped-binaries/%s" % binary.binary_name
    if binary.is_py_binary():
        invocation = "/usr/bin/env python -m $BINARY_PY_MODULE $*"


    template_vars = {"zip_file": build_plan.get_zip_base_name(),
                     "data_dir": build_plan.data_dir_rel,
                     "project_name": build_plan.target_definition.project_name,
                     "project_repo_rel_path":
                         build_plan.target_definition.project_repo_rel_path,
                     "binary_py_module":
                         binary.entry_module_path,
                     "invocation": invocation}

    return template % template_vars


def write_wrapped_binary(binary, build_plan):
    rendered = render_wrapped_binary(binary, build_plan)
    output_path = build_plan.get_binary_output_path(binary)

    f = open(output_path, "wb")
    f.write(rendered)
    f.close()

    os.chmod(output_path, 0755)
    LOG.info("Wrote binary %s", output_path)

