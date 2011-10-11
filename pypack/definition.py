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


    @cached_property
    def relative_pythonpath_additions(self):
        return self.pypack_definition.all_dependencies["pythonpath_additions"]


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
        Paths returned are absolute.
        """
        if not self._config or not self._config.has_section("external_data"):
            return []

        project_rel_paths = [k for k, _ in self._config.items("external_data")]
        return [os.path.join(self.project_absolute_path, p)
                for p in project_rel_paths]



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
    def dependency_list(self):
        """
        Return a flat list of PypackDefinition objects for this one's
        dependencies.
        """

        tree = self._compute_dependency_list()
        return tree


    def _compute_dependency_list(self, processed_defs=set([])):
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
        noslash_path = self.project_absolute_path
        if noslash_path.endswith("/"):
            noslash_path = noslash_path[:-1]
        return os.path.basename(noslash_path)


    @cached_property
    def binaries(self):
        if not self._config or not self._config.has_section("binaries"):
            return []
        binaries = []
        for binary_name, entry_point in self._config.items("binaries"):
            b = BinaryDefinition(self, binary_name, entry_point)
            binaries.append(b)

        return binaries


    @cached_property
    def pythonpath_additions(self):
        """
        Typically, your repository would be laid out like this:
        my_repo/
          src/
          third_party/

        With code in src/ importing third_party libs like this:

        from sqlalchemy import Integer

        However, in the context of the build, the fully qualified
        import path would be:

        from third_party.sqlalchemy import Integer

        Which works fine for *your* code, but when the library imports
        from itself, shit gets ill fast, as it is not importing the fully
        qualified path, so you get ImportErrors when you import a library.

        However, if PYTHONPATH=my_repo/src:my_repo/third_party, it will
        work fine, provided your third party libs are installed in third_party.

        So, we will automatically add third_party/ to the PYTHONPATH of
        the output binary, so your imports would work just as they would if
        you were importing a package installed via pip.

        The downside to this is that your development version may be importing
        the pip version of the package, not the third_party/ version, so
        you should make sure you've got that straight.
        """

        # TODO: add a config parameter so you can set arbitrary
        # PYTHONPATH additions.
        if self.module_py_path == "third_party":
            return ["third_party"]

        return []
