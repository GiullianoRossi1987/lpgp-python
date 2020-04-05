# coding = utf-8
# using namespace std
from json import loads, JSONDecodeError
from typing import AnyStr


class ClientData(object):
	"""
	That class manage the client configurations file. That class loads the configurations JSON file, but the class
	don't write anything in the file, it also change the file permissions to 744 (linux mode).
	:cvar file_loaded: The configurations file that the class loaded
	:cvar got_file: If the class got a configurations file loaded
	:cvar raw_doc: The JSON parsed dict of the configurations file content.

	:type file_loaded: basestring
	:type got_file: bool
	:type raw_doc: dict
	"""
	file_loaded: AnyStr
	got_file: bool = False
	raw_doc: dict

	class FileError(Exception):
		"""
		<Exception> raised when the class try to access a configurations file loaded, but the configurations file
		wasn't loaded yet. Also raised when the class try to load a configurations file, but there's a configurations
		file loaded already.
		"""

	class InvalidFile(Exception):
		"""
		<Exception> raised when the class try to load a configurations file but the file structure or values aren't valid.
		"""

	def ck_file(self, config_file: AnyStr) -> True:
		"""
		That method checks if a configurations file is valid or not. To be valid the configurations file must be a
		JSON file with those fields:
			Warning (optional): string => Optional field that contains the JSON comments and alerts about the file.
			RootMode: boolean => Boolean value that means if the client have root permissions
			Mode: integer [0, 1] => Binary like value that means if the client owner is a proprietary or a normal client.
									0 -> Proprietary; 1 -> Normal Client
			LocalAccountID: integer => The client owner account primary key reference, only used by the MySQL client.
		:param config_file: The configurations file to load.
		:except InvalidFile: Raised if the file isn't valid, by any reason
		:return: True at the process end
		"""
		try:
			if str(config_file).split(".")[-1] != "json":
				raise self.FileError("ERROR: The client configurations file must be a .json file")
			with open(config_file, mode="r", encoding="utf-8") as config:
				ld = loads(config.read())  # DICT
				if type(ld['RootMode']) is not bool:
					raise self.InvalidFile("Invalid value at the 'RootMode' field.")
				elif type(ld['Mode']) is not int or ld['Mode'] not in [0, 1]:
					raise self.InvalidFile("Invalid value at the 'Mode' field")
				elif type(ld['LocalAccountID']) is not int or ld['LocalAccountID'] <= 0:
					raise self.InvalidFile("Invalid value at the 'LocalAccountID' field")
				else:
					pass
		except FileNotFoundError or PermissionError: raise self.InvalidFile("File unreadable")
		except JSONDecodeError as json_e: raise self.InvalidFile("JSON syntax error: " + json_e.msg)
		except KeyError as field_e:
			raise self.InvalidFile("Missing field/index. RAW_ERROR: " + field_e.args[0])
		finally: return True

	def load_file(self, config: AnyStr):
		"""
		That method checks and loads a configurations file to set the class attributes and get the configurations.
		:param config: The configurations file to load.
		:except FileError: If the class already have a configurations file loaded.
		"""
		if self.got_file: raise self.FileError("The class already got a configurations file loaded")
		if self.ck_file(config):
			with open(config, mode="r", encoding="utf-8") as to_load:
				self.raw_doc = loads(to_load.read())
				self.file_loaded = config
				self.got_file = True

	def unload_file(self):
		"""
		That method unset all the class attributes, it's used for the garbage collection and for turn the class object
		able to load another file instead the actual loaded file.
		:except FileError: If the class don't have a configurations file loaded yet
		"""
		if not self.got_file: raise self.FileError("The class don't have a configurations file loaded yet")
		self.raw_doc = dict()
		self.got_file = False
		self.file_loaded = ""

	def __init__(self, config: AnyStr = "lib/client_config.json"):
		"""
		That method loads a configurations file, initializing the class with a file loaded.
		:param config: The configurations file to load, if it's None will set the class attributes with default values.
		"""
		if config is not None: self.load_file(config)
		else:
			self.file_loaded = ""
			self.got_file = False
			self.raw_doc = dict()

	def __del__(self):
		"""
		That method is used for the class garbage collection. It unload any configurations file loaded before deleting
		the class object/instance
		"""
		if self.got_file: self.unload_file()

	@property
	def rootMode(self) -> bool:
		"""
		That property represents the RootMode field from the configurations file loaded.
		:except FileError: If the class don't have a configurations file loaded yet
		:return: The configurations file "RootMode" value.
		"""
		if not self.got_file: raise self.FileError("Can't reach any property, there's no configurations file loaded.")
		else: return bool(self.raw_doc['RootMode'])

	@property
	def mode(self) -> int:
		"""
		That property represents the Mode field value from the configurations file loaded.
		:except FileError: If the class don't have a configurations file loaded yet.
		:return: The configurations file loaded 'Mode' value
		"""
		if not self.got_file: raise self.FileError("Can't reach any property, there's no configurations file loaded.")
		else: return int(self.raw_doc['Mode'])

	@property
	def ownerID(self) -> int:
		"""
		That property represents the LocalAccountID field value from the configurations file loaded.
		:except FileError: If the class don't have a configurations file loaded.
		:return: The 'LocalAccountID' field value.
		"""
		if not self.got_file: raise self.FileError("Can't reach any property, there's no configurations file loaded!")
		else: return int(self.raw_doc['LocalAccountID'])

	@property
	def warnings(self):
		"""
		That property represents the optional field 'Warning' on the configurations file.
		:except FileError: If the class don't have a configurations file loaded.
		:return: The warning on the document. If it don't have a warning field, then will return None
		"""
		if not self.got_file: raise self.FileError("Can't reach any property, there's no configurations file loaded.")
		else:
			if "Warning" in self.raw_doc.keys(): return self.raw_doc['Warning']
			else: return None
