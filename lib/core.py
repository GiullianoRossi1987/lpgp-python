# coding = utf-8
# using namespace std
from lib.auth.authcore import Client4
from pymysql.cursors import Cursor
from pymysql.connections import Connection
from time import strftime
from json import loads, dumps, JSONDecodeError
from typing import AnyStr


class MySQLConnectionOptions(object):
	"""
	That class manages the MySQL external database configurations file. That configurations file have the main data
	about the MySQL database server, data such as the Primary host to connect and the database port. There're the default
	values to use, but using that class you can also change they.
	:cvar file_load: The configurations file loaded.
	:cvar document: The configurations parsed content.
	:cvar got_file: If the class got a configurations file.
	"""
	file_load: AnyStr
	document: dict = dict()
	got_file: bool = False

	class FileError(Exception):
		"""
		Exception raised when the class try to access the loaded file, but there's no configurations file loaded yet.
		Also raised when the configurations class try to load a configurations file but there's another one loaded already
		"""

	class InvalidConfigurationsFile(Exception):
		"""
		Exception raised when the configurations file class try to load a configurations file, but that isn't a valid
		configurations file. To see the valid configurations file requirements just read the docs of the ckconfig
		method
		"""

	def ckconfig(self, config: AnyStr) -> True:
		"""
		That method checks if a configurations file referred is valid or not. That method will return True only if the
		structure is valid. To be valid, the file must have the following structure:
			* General (master index)
				Primary-Host: string ( The MySQL database IP)
				Default-Port: integer (The MySQL database Port)
				Connection-Logs: string (The local connection logs.)
		:param config: The configurations file to load.
		:except InvalidConfigurationsFile: If the file isn't valid.
		:return: If the file is valid will return True
		"""
		try:
			with open(config, "r", encoding="UTF-8") as to_check:
				loaded = loads(to_check.read())
				for i, l in loaded['General'].items():
					if i == "Primary-Host":
						if type(l) is not str or len(l) == 0:
							raise self.InvalidConfigurationsFile("Invalid value [Primary-Host::] expecting IP on string")
					elif i == "Default-Port":
						if type(l) is not int or l <= 0:
							raise self.InvalidConfigurationsFile("Invalid value [Default-Port::] expecting int more then 0")
					elif i == "Connection-Logs":
						if (type(l) is not AnyStr or str) or len(l) == 0:
							raise self.InvalidConfigurationsFile("Invalid value [Connection-Logs::] expecting file path")
						else:
							try:
								a = open(l, "a", encoding="UTF-8")
								a.close()
								del a
							except FileNotFoundError or PermissionError:
								raise self.InvalidConfigurationsFile("Invalid file path [Connection-Logs::] unreachable file")
					elif i == "LocalAccountID":
						if type(l) is not int or l <= 0:
							raise self.InvalidConfigurationsFile("Invalid value [LocalAccountID::] expecting integer more then 0")
					else:
						raise self.InvalidConfigurationsFile(f"Invalid field '{i}' [General::]")
				del loaded
		except FileNotFoundError or PermissionError:
			raise self.InvalidConfigurationsFile("Unreachable file")
		except JSONDecodeError:
			raise self.InvalidConfigurationsFile("Invalid JSON content.")
		except KeyError:
			raise self.InvalidConfigurationsFile("Structure error, please check the fields")
		return True

	def load_config(self, config: AnyStr):
		"""
		Loads a configurations file to the class attributes.
		:param config: The configurations file to load.
		:except FileError: If there's a configurations file loaded already
		"""
		if self.got_file: raise self.FileError("There's a configurations file loaded already")
		if self.ckconfig(config):
			with open(config, "r", encoding="UTF-8") as conf:
				self.file_load = config
				self.document = loads(conf.read())
				self.got_file = True

	def __init__(self, config: AnyStr = None):
		"""
		That method loads the MySQL database configurations file.
		:param config: The configurations file to load, if None then will set up the attributes with default values
		"""
		if config is not None: self.load_config(config)

	def commit(self):
		"""
		Writes all the changes at the configurations content <document attr> to the original file <file_load attr>
		:except FileError: If there's no configurations file loaded yet;
		"""
		if not self.got_file: raise self.FileError("There's no configurations file loaded yet!")
		with open(self.file_load, "w", encoding="UTF-8") as original:
			dumped = dumps(self.document)
			original.write(dumped)
			del dumped

	def unload(self):
		"""
		That method unset the class attributes, making it ready for load another configurations file or just close't
		before deleting the class object/instance
		:except FileError: If there's no configurations file loaded yet
		"""
		if not self.got_file: raise self.FileError("There's no configurations file loaded yet")
		self.commit()
		self.document = {}
		self.file_load = ""
		self.got_file = False

	def __del__(self):
		"""
		Method used for the class object/instance garbage collection. that method unload any configurations file loaded
		in the class.
		"""
		if self.got_file: self.unload()

