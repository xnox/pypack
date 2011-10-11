import os
import shutil
import logging

LOG = logging.getLogger(__name__)


def copy_external_data(build_plan):
    dependency_defs = build_plan.target_definition.dependency_list
    for dependency_def in dependency_defs:
        _copy_data_entries(dependency_def, build_plan)


def _copy_data_entries(definition, build_plan):
    """
    Copy both the external data definitions.
    "external data" gets written to a projectname_data directory,
    outside of the zipped package of dependencies.
    """
    external_paths = definition.external_data_paths
    if external_paths:
        LOG.info("Copying external data for %s", definition.module_py_path)

    for external_path in external_paths:
        LOG.info("Processing external data dependency %s", external_path)
        # These are yet un-expanded
        for dir_path, directories, files in os.walk(external_path):
            for file_name in files:
                src_path = os.path.join(dir_path, file_name)
                dst_path = build_plan.get_external_data_file_dest(src_path)

                dst_dir = os.path.dirname(dst_path)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                shutil.copy2(src_path, dst_path)
                LOG.debug("Copied external data %s --> %s", src_path, dst_path)
