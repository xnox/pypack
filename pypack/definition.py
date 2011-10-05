import os
import ConfigParser
import subprocess

_DEFINITION_CACHE = {}

class MissingBuildDefinition(Exception):
    pass

class BinaryDefinition(object):
    def __init__(self, pypack_definition, binary_name, invocation_file):
        self.pypack_definition = pypack_definition
        self.binary_name = binary_name
        self.invocation_file = invocation_file

    @property
    def output_path(self):
        return os.path.join(self.pypack_definition.repository_root,
                            self.binary_name)

    @property
    def entry_module_path(self):
        # TODO: check to see if the invocation file is there
        local_module_name = self.invocation_file
        if self.invocation_file.endswith(".py"):
            local_module_name = local_module_name[:-3]
        module_path = self.pypack_definition.project_repo_rel_path.replace(
            os.path.sep, ".")
        qualified_module_path = "%s.%s" % (module_path, local_module_name)
        return qualified_module_path


class PypackDefinition(object):
    def __init__(self):
        self.repository_root = None
        self.project_absolute_path = None
        self.project_repo_rel_path = None
        self.module_path = None

        self._config = ConfigParser.SafeConfigParser(allow_no_value=True)


    @classmethod
    def from_project_directory(cls, project_dir):
        definition = cls()
        definition.init_definition_fs_paths(project_dir)
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

    def init_definition_fs_paths(self, project_directory):
        self.project_absolute_path = os.path.abspath(project_directory)

        self.repository_root = self._determine_repo_root(
            self.project_absolute_path)

        self.project_repo_rel_path = os.path.relpath(self.project_absolute_path,
                                                     self.repository_root)


    def _determine_repo_root(self, project_directory):
        # Only supports git right now
        # TODO: don't call this when computing dependencies
        git_dir = subprocess.check_output(["git", "rev-parse",
                                           "--show-toplevel"],
                                          cwd=project_directory)
        return git_dir.strip()


    @property
    def direct_dependency_definitions(self):
        """PypackDefinition objects for this one's dependencies,
        as defined in the [depends] block in the PYPACK file.
        """
        dependency_defs = []
        if not self._config.has_section("depends"):
            return []

        depends_rel_paths = [k for k, _ in self._config.items("depends")]
        for depend_rel_path in depends_rel_paths:
            abs_path = os.path.join(self.repository_root,
                                    depend_rel_path)

            definition = PypackDefinition.from_project_directory(abs_path)
            dependency_defs.append(definition)

        return dependency_defs


    @property
    def module_tree_parents(self):
        """If the module is at A.B.C.D, this returns A, A.B, A.B.C, A.B.C.D"""
        tree_parents = []

        module_parent_list = self.project_repo_rel_path.split(os.path.sep)
        for i in xrange(1, len(module_parent_list) + 1):
            path_segment = ".".join(module_parent_list[:i])
            tree_parents.append(path_segment)

        return tree_parents

    def all_dependent_modules(self, processed_defs=set([])):
        # TODO: cycle detection
        # Presently that's an infinite loop, so don't do that.
        dependent_modules = set(self.module_tree_parents)
        for dependency_def in self.direct_dependency_definitions:
            if dependency_def in processed_defs:
                continue
            processed_defs.add(dependency_def)
            dependent_modules.update(
                dependency_def.all_dependent_modules(processed_defs))
        return dependent_modules


    @property
    def project_name(self):
        if not self._config:
            return None
        return self._config.get("project", "name")


    @property
    def binaries(self):
        if not self._config:
            return []
        binaries = []
        for binary_name, entry_point in self._config.items("binaries"):
            b = BinaryDefinition(self, binary_name, entry_point)
            binaries.append(b)

        return binaries
