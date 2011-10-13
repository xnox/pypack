import os

class BuildPlan(object):
    """
    A high-level object that expresses everything
    the build will have to do.
    """


    def __init__(self, target_definition, output_directory):
        """
        Parameters:
          target_definition: the PypackDefinition of the project we
            are building.
          output_directory: the absolute path to the build output
            directory.
        """
        self.build_dir_name = "pythonpath"
        self.target_definition = target_definition
        self.output_directory = output_directory
        self.build_directory = os.path.join(output_directory,
                                            self.build_dir_name)
        self.data_dir_rel = "%s_data" % self.target_definition.project_name
        self.external_data_dir = os.path.join(output_directory,
                                              self.data_dir_rel)

    def _repo_rel_path(self, file_abs_path):
        return os.path.relpath(file_abs_path,
                               self.target_definition.repository_root)

    def get_module_build_dest(self, module_def):
        """
        The absolute path that a given module PypackDefinition
        will end up in the build directory
        """
        return os.path.join(self.build_directory,
                            module_def.project_repo_rel_path)


    def get_file_build_dest(self, file_abs_path):
        """
        Parameters:
          file_abs_path: the absolute path to the file on disk
        Returns:
          Where this file will land in the build dir, as an absolute
          path.
        """

        # Assume the target pypack def is in the same repo as
        # the file you are asking about.

        repo_rel_path = self._repo_rel_path(file_abs_path)
        dest_abs_path = os.path.join(self.build_directory, repo_rel_path)
        return dest_abs_path


    def get_external_data_file_dest(self, file_abs_path):
        repo_rel_path = self._repo_rel_path(file_abs_path)
        dest_abs_path = os.path.join(self.external_data_dir, repo_rel_path)
        return dest_abs_path


    def get_zip_base_name_shutil(self):
        """
        This is dump, shutil's make_archive function wants a basename
        with no file extension.
        """
        return os.path.join(self.output_directory,
                            self.target_definition.project_name)

    def get_zip_base_name(self):
        """
        Used for setting PYTHONPATH in the wrapped binaries.
        """
        return "%s.zip" % self.target_definition.project_name


    def get_environment_path(self):
        return os.path.join(self.output_directory, "environment")


    def get_binary_symlink_name(self, binary):
        return os.path.join(self.output_directory, binary.binary_name)


    def get_binary_symlink_source(self, binary):
        """
        Returns a path relative to self.output_directory.
        """
        abs_path = self.get_file_build_dest(binary.abs_path)
        return os.path.relpath(abs_path, self.output_directory)
