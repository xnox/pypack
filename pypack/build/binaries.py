import os
import logging
import pkg_resources

LOG = logging.getLogger(__name__)


def symlink_binaries(build_plan):
    binaries_to_build = build_plan.target_definition.binaries
    for def_ in build_plan.target_definition.dependency_list:
        binaries_to_build.extend(def_.binary_depends)

    _write_environment(build_plan)

    for binary in binaries_to_build:
        _symlink_binary(binary, build_plan)


def _write_environment(build_plan):
    manager = pkg_resources.ResourceManager()
    provider = pkg_resources.get_provider("pypack.build")

    template = provider.get_resource_string(manager,
                                            "environment.txt")


    template_vars = {"data_dir": build_plan.data_dir_rel,
                     "project_name": build_plan.target_definition.project_name,
                     "project_repo_rel_path":
                         build_plan.target_definition.project_repo_rel_path}
    rendered = template % template_vars

    envpath = build_plan.get_environment_path()
    f = open(envpath, "wb")
    f.write(rendered)
    f.close()

    LOG.info("Wrote environment file %s", envpath)


def _symlink_binary(binary, build_plan):
    source = build_plan.get_binary_symlink_source(binary)
    name = build_plan.get_binary_symlink_name(binary)

    os.symlink(source, name)
    LOG.info("Symlinked %s --> %s", name, source)

