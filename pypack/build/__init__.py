"""
This is kind of a hack, but distutils isn't super friendly
to programmatic access. It really likes to be called from
the shell.
"""
import os
import logging
from pypack.build.plan import BuildPlan
from pypack.build.dependencies import copy_dependencies
from pypack.build.external_data import copy_external_data
from pypack.build.binaries import symlink_binaries

LOG = logging.getLogger(__name__)


def init_dirs(build_plan):
    if not os.path.exists(build_plan.output_directory):
        LOG.debug("Making output directory %s", build_plan.output_directory)
        os.makedirs(build_plan.output_directory)


def build_project(definition, output_directory):
    build_plan = BuildPlan(definition, output_directory)

    init_dirs(build_plan)

    copy_dependencies(build_plan)
    copy_external_data(build_plan)
    symlink_binaries(build_plan)

