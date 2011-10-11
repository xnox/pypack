"""
This is kind of a hack, but distutils isn't super friendly
to programmatic access. It really likes to be called from
the shell.
"""
import os
import shutil
import logging
from pypack.build.plan import BuildPlan
from pypack.build.dependencies import copy_dependencies
from pypack.build.external_data import copy_external_data
from pypack.build.compression import zip_build
from pypack.build.binaries import write_binaries

LOG = logging.getLogger(__name__)


def init_dirs(build_plan):
    if not os.path.exists(build_plan.output_directory):
        LOG.debug("Making output directory %s", build_plan.output_directory)
        os.makedirs(build_plan.output_directory)
    if not os.path.exists(build_plan.get_wrapped_binary_dir()):
        LOG.debug("Making wrapped binary dir %s",
                  build_plan.get_wrapped_binary_dir())
        os.makedirs(build_plan.get_wrapped_binary_dir())


def cleanup(build_plan):
    LOG.info("Cleaning up")
    if os.path.exists(build_plan.build_directory):
        LOG.debug("Deleting %s", build_plan.build_directory)
        shutil.rmtree(build_plan.build_directory)


def build_project(definition, output_directory):
    build_plan = BuildPlan(definition, output_directory)

    init_dirs(build_plan)

    copy_dependencies(build_plan)
    copy_external_data(build_plan)
    zip_build(build_plan)
    write_binaries(build_plan)

    cleanup(build_plan)
