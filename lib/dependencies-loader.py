# coding = utf-8
# using namespace std
from json import loads
from json import dumps
from json import JSONDecodeError
from os import system
from sys import version
from typing import AnyStr


class DependenciesManager(object):
    """
    That class read the lib/dependencies.json, to see what packages it have to install before the system
    execution. That class also manages in a general way those dependencies, setting if need to add a dependency
    or install one.
    :cvar dep_file : The dependencies file loaded.
    :cvar document: The dependencies file content parsed with the JSON methods
    :cvar got_file: If the class got a dependencies file loaded.
    :type dep_file: AnyStr
    :type document: dict
    :type got_file: bool
    """
    dep_file: AnyStr
    document: dict
    got_file: bool = False

    class DependenciesLoadError(Exception):
        """
        <Exception> Raised when the dependencies manager don't have a dependencies file, and try to do any action. Or
        when the dependencies  manager try to load a dependencies file, but already have another file loaded instead.
        """

    class InvalidDependencies(Exception):
        """
        <Exception> Raised when the dependencies manager try to load a invalid dependencies file (To see what the file
        requirements to be a valid, see the docs of the ck_depf method).
        """

    class DependencyNotFound(Exception):
        """
        <Exception> Raised when the dependencies manager try to get data about a dependency but the dependency required
        don't exist.
        """

    @staticmethod
    def ext_countref(ref: str, doc: dict) -> int:
        """
        Count how many dependencies with the same reference have  on a external dependencies document
        :param ref: The reference to search
        :param doc: The parsed JSON document of the dependencies file
        :return: The number of references found
        """
        c = 0
        for dep in doc['Dependencies']:
            if dep['Name'] == ref: c += 1
        return c

    def countref(self, ref: str) -> int:
        """
        Count how many dependencies with the same reference have on the loaded document
        :param ref: The reference to search.
        :return: The number of dependencies found with the same reference.
        """
        if not self.got_file: raise self.DependenciesLoadError("There's no dependencies document loaded yet!")
        return self.ext_countref(ref, self.document)

    def ck_depf(self, depf: AnyStr) -> tuple:
        """
        Check the structure of the dependencies file is valid or not. To be a valid dependencies file it need to have
        the following structure:
            * Dependencies (list):
                - general-object (dict):
                    * Name: (string)     => The name reference
                    * Package: (string)  => The package name to install
                    * Installed: (bool)  => If the package is already installed
            * GenInfo (dict):
                - Version: (string/int)  => The version of the dependencies manager.
                - Restrict: (bool)       => If the document will require all the dependencies installed.
        :param depf: The dependencies file installed.
        :return: It return one tuple, at the 0 index of the tuple we have the error code,
                    The error code can be :
                    * 0 => If the file is valid.
                    * 1 => If the file isn't a .json file;
                    * 2 => if the method can't access the file (caused by a PermissionError or a FileNotFoundError)
                    * 3 => If there're missing fields at any document part
                    * 4 => If there're invalid value types at any field.
                And the 1 index of the tuple is the specific error message of the file invalidation
        """
        if str(depf).split(".")[-1] != "json": return 1, "expecting a .json file"
        try:
            with open(depf, "r") as doc:
                prs = loads(doc.read())
                try:
                    for dep in prs['Dependencies']:
                        if dep is not dict: return 4, "expecting a list with dicts at the Dependencies field"
                        try:
                            if dep['Name'] is not str or len(dep['Name']) <= 0: return 4, "expecting string with more then one character to refer the dependency"
                            elif dep['Package'] is not str or len(dep['Package']) <= 0: return 4, "expecting string with more then one character to refer the dependency installation name"
                            elif dep['Installed'] is not bool: return 4, "expecting, bool to refer if the dependency '" + dep['Name'] + "' is installed"
                            elif self.ext_countref(dep['Name'], prs) > 1: return 4, f"duplicate reference '{dep['Name']}'!"
                            else: pass
                        except IndexError or KeyError: return 3, "Invalid Structure"
                        else: continue
                except KeyError: return 3, "Invalid Structure"
                try:
                    ver = prs['GenInfo']['Version']
                    restrict = prs['GenInfo']['Restrict']
                    if restrict is not bool: return 4, "expecting bool to the restrict value."
                    if ver is not str or int: return 4, "expecting int/str to the version value."
                except KeyError: return 3, "Invalid structure"
        except FileNotFoundError or PermissionError as e: return 2, "Cant access the file, cause: " + e
        except JSONDecodeError: return 1, "Can't parse the JSON document!"
        else: return 0, None

    def load_file(self, dep: AnyStr):
        """
        Set a dependencies file to the class attributes.
        :param dep: The dependencies file to load.
        :except DependenciesLoadError: If there's a dependencies file loaded already
        :except InvalidDependencies: If the dependencies file isn't valid
        """
        if self.got_file: raise self.DependenciesLoadError("There's a dependencies file loaded already")
        code, msg = self.ck_depf(dep)
        if code != 0: raise self.InvalidDependencies(msg)
        del code, msg
        self.dep_file = dep
        with open(dep, "r") as dependencies: self.document = loads(dependencies.read())
        self.got_file = True

    def commit(self):
        """
        Commit all the changes made on the document attribute, to the loaded dependencies file.
        :except DependenciesLoadError: If there's no dependencies file loaded yet!
        """
        if not self.got_file: raise self.DependenciesLoadError("There's no dependencies file loaded yet!")
        with open(self.dep_file, "w") as dp:
            dumped = dumps(self.document)
            dp.write(dumped)

    def reload(self):
        """
        Reload all the JSON content of the loaded file to the document attribute
        :except DependenciesLoadError: If there's no dependencies file loaded.
        """
        if not self.got_file: raise self.DependenciesLoadError("There's no dependencies file loaded yet!")
        with open(self.dep_file, "r") as doc: self.document = loads(doc.read())

    def unload_file(self):
        """
        Commit the changes at the document and unset the class attributes, closing the dependencies file loaded.
        :except DependenciesLoadError: If there's no dependencies file loaded
        """
        if not self.got_file: raise self.DependenciesLoadError("There's no dependencies file loaded yet!")
        self.commit()
        self.document = dict()
        self.dep_file = ""
        self.got_file = False

    def __init__(self, dep: AnyStr = None):
        """
        Initialize the class
        :param dep: The dependencies file to load automatically
        """
        if dep is not None: self.load_file(dep)

    def __del__(self):
        """
        Method called when the class instance/object is deleted. It unload the file loaded before deleting it self.
        """
        if self.got_file: self.unload_file()

    def install(self, ref: str):
        """
        Install a listed dependency from the dependencies file
        :param ref: The dependency name reference.
        :except DependenciesLoadError: If there's no dependencies file loaded yet!
        :except DependencyNotFound> If there's no dependency with that name reference
        :return: None
        """
        if not self.got_file: raise self.DependenciesLoadError("There's no dependencies file loaded yet!")
        if self.countref(ref) == 0: raise self.DependencyNotFound(f"There's no dependency '{ref}'!")
        for dep in self.document['Dependencies']:
            if dep['Name'] == ref:
                if dep['Installed']: pass
                else:
                    if "2." in version:
                        system("pip install " + dep['Package'])
                    else:
                        system("pip3 install " + dep['Package'])
                    dep['Installed'] = True
            else: pass

    def install_all(self):
        """
        Install all the dependencies that aren't installed yet.
        :except DependenciesLoadError: If there's no dependencies file loaded yet
        """
        if not self.got_file: raise self.DependenciesLoadError("There's no dependencies file loaded yet")
        for dep in self.document['Dependencies']:
            if dep['Installed']: pass
            else:
                if "2." in version:
                    system("pip install " + dep['Package'])
                else:
                    system("pip3 install " + dep['Package'])
                dep['Installed'] = True
    




