import os
import ConfigParser
import subprocess

from util import cached_property

_DEFINITION_CACHE = {}

class MissingBuildDefinition(Exception):
    pass

class BinaryDefinition(object):
    def __init__(self, pypack_definition, binary_name, invocation_file):
        self.pypack_definition = pypack_definition
        self.binary_name = binary_name
        self.invocation_file = invocation_file


    @cached_property
    def entry_module_path(self):
        # TODO: check to see if the invocation file is there
        local_module_name = self.invocation_file
        if self.invocation_file.endswith(".py"):
            local_module_name = local_module_name[:-3]

        qualified_module_path = "%s.%s" % (
            self.pypack_definition.module_py_path, local_module_name)
        return qualified_module_path


class PypackDefinition(object):

    def __init__(self):
        self.repository_root = None
        self.project_absolute_path = None
        self.project_repo_rel_path = None
        self.module_py_path = None # A.B.C.D, not an FS path
        self._config = ConfigParser.SafeConfigParser(allow_no_value=True)

        self._dependent_definitions = None # The dependency tree


    @classmethod
    def from_project_directory(cls, project_dir, repo_root):
        definition = cls()
        definition.init_definition_fs_paths(project_dir, repo_root)
        pypack_file_path = os.path.join(definition.project_absolute_path,
                                        "PYPACK")
        if _DEFINITION_CACHE.get(pypack_file_path, None):
            return _DEFINITION_CACHE.get(pypack_file_path)

        try:
            definition.init_config(pypack_file_path)
        except MissingBuildDefinition:
            # Assume a module with no depends
            pass

        _DEFINITION_CACHE[pypack_file_path] = definition
        return definition


    def init_config(self, pypack_file_path):
        f = None
        try:
            f = open(pypack_file_path, "rb")
            self._config.readfp(f)
        except IOError, e:
            raise MissingBuildDefinition(e)
        finally:
            if f:
                f.close()

    def init_definition_fs_paths(self, project_directory, repo_root):
        self.project_absolute_path = os.path.abspath(project_directory)
        self.repository_root = repo_root
        self.project_repo_rel_path = os.path.relpath(self.project_absolute_path,
                                                     self.repository_root)

        # While we're here, init the module "python" path, as if
        # it were an import
        self.module_py_path = self.project_repo_rel_path.replace(
            os.path.sep, ".")


    @cached_property
    def external_data_paths(self):
        """
        Return the paths to the files and directories in the
        [external_data] section of the PYPACK file.
        Paths are returned relative to the repo root.
        """
        return self._data_paths("external_data")


    @cached_property
    def internal_data_paths(self):
        """
        Return the paths to the files and directories in the
        [internal_data] section of the PYPACK file.
        Paths are returned relative to the repo root
        """
        return self._data_paths("internal_data",
                                relative_to=self.project_absolute_path)


    def _data_paths(self, config_section, relative_to=None):
        """
        Read and expand the data paths. For example, if someone
        specifies:

        templates/

        this method will recursively expand that to all files
        in the subtree.

        When you want to support glob syntax, do it here.
        """
        if not self._config or not self._config.has_section(config_section):
            return []

        if relative_to is None:
            relative_to = self.repository_root

        def visit(append_to, dirname, file_names):
            for file_name in file_names:
                path = os.path.join(dirname, file_name)
                if os.path.isfile(path):
                    append_to.append(path)


        # Given the defined paths (relative to the project root),
        # expand the entries to absolute paths
        all_abs_paths = []
        project_rel_paths = [k for k, _ in self._config.items(config_section)]
        for rel_path in project_rel_paths:
            abs_path = os.path.join(self.project_absolute_path, rel_path)
            if not os.path.isdir(abs_path):
                all_abs_paths.append(abs_path)
            else:
                # Recurse directories
                os.path.walk(abs_path, visit, all_abs_paths)

        # Return the paths relative to the method arg
        return [os.path.relpath(a, relative_to) for a in all_abs_paths]

    @cached_property
    def direct_dependency_definitions(self):
        """PypackDefinition objects for this one's dependencies,
        as defined in the [depends] block in the PYPACK file.

        Further, a package depends on its sub-packages, so add
        entries for all directories in this subtree.
        """
        dependency_defs = []

        # Packages in this sub-tree
        for file_name in os.listdir(self.project_absolute_path):
            abs_path = os.path.join(self.project_absolute_path, file_name)
            if not os.path.isdir(abs_path):
                continue
            definition = PypackDefinition.from_project_directory(
                abs_path, self.repository_root)
            dependency_defs.append(definition)


        if not self._config.has_section("depends"):
            return dependency_defs

        # Explicitly stated dependencies
        depends_rel_paths = [k for k, _ in self._config.items("depends")]
        for depend_rel_path in depends_rel_paths:
            abs_path = os.path.join(self.repository_root,
                                    depend_rel_path)

            definition = PypackDefinition.from_project_directory(abs_path,
                                                                 self.repository_root)
            dependency_defs.append(definition)


        return dependency_defs


    @cached_property
    def module_tree_parents(self):
        """If the module is at A.B.C.D, this returns A, A.B, A.B.C, A.B.C.D"""
        tree_parents = []

        module_parent_list = self.project_repo_rel_path.split(os.path.sep)
        for i in xrange(1, len(module_parent_list) + 1):
            path_segment = ".".join(module_parent_list[:i])
            tree_parents.append(path_segment)

        return tree_parents



    @cached_property
    def all_dependencies(self):
        """
        Return the following dependencies, as a dictionary:
          - Modules
          - External data
          - Internal (package) data
        """

        dependencies = {"modules": set(self.module_tree_parents),
                        "external_data_paths": set(self.external_data_paths),
                        "internal_data_paths":
                            {self.module_py_path: self.internal_data_paths}}
        dependent_defs = self.all_dependent_definitions()
        for def_ in dependent_defs:
            dependencies["modules"].update(def_.module_tree_parents)
            dependencies["external_data_paths"].update(def_.external_data_paths)
            if def_.internal_data_paths:
                # distutils requires a map of module -> relative path
                # That's relative patch from the *package*, not the root
                dependencies["internal_data_paths"][def_.module_py_path] = \
                    def_.internal_data_paths

        return dependencies


    def all_dependent_definitions(self, processed_defs=set([])):
        """
        Return the transitive closure of dependency PypackDefinition
        objects.
        """
        if self._dependent_definitions is not None:
            return self._dependent_definitions

        dependent_defs = set([])
        for dependency_def in self.direct_dependency_definitions:
            if dependency_def in processed_defs:
                continue
            processed_defs.add(dependency_def)
            dependent_defs.add(dependency_def)
            dependent_defs.update(
                dependency_def.all_dependent_definitions(processed_defs))

        self._dependent_definitions = dependent_defs
        return self._dependent_definitions


    @cached_property
    def project_name(self):
        if not self._config:
            return None
        return self._config.get("project", "name")


    @cached_property
    def binaries(self):
        if not self._config or not self._config.has_section("binaries"):
            return []
        binaries = []
        for binary_name, entry_point in self._config.items("binaries"):
            b = BinaryDefinition(self, binary_name, entry_point)
            binaries.append(b)

        return binaries
