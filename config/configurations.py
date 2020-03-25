# coding = utf-8
# using namespace std
from typing import AnyStr, Type
from json import loads
from json import dumps
from json import JSONDecodeError


class Configurations(object):
	"""
	That class manages the configurations file loaded, that file is a simple JSON file that contains the complete
	LPGP application configurations.
	:cvar config_f: The configurations file loaded
	:cvar document: The configurations JSON parsed content
	:cvar got_file: If the class got a configurations file loaded
	:type config_f: basestring
	:type document: dict
	:type got_file: bool
	"""
	config_f: AnyStr
	got_file: bool = False
	document: dict = dict()

	class ConfigurationsLoadError(Exception):
		"""
		<Exception> Raised when the class try to call the configurations file content, or path, but there's no configurations
		file loaded yet. Also raised when the class try to load a configurations file but there's another file loaded
		already
		"""

	class InvalidConfig(Exception):
		"""
		<Exception> Raised when the configurations file received have a invalid structure. To see the structure required
		see the docs of ckconfig method.
		"""

	def ckconfig(self, conff: AnyStr) -> True:
		"""
		That method check if a configurations file is valid or not. To be a valid configurations file, the file need
		to have the following structure:
			Dependencies:
				* AutoCheck  (bool)
				* RunWithout (bool)
				* Checked    (bool)
			CLI:
				* Color (bool)
				* Min   (bool)
				* VerboseAlways (bool)
				* ErrorSource   (bool)
				* LogsActivity  (bool)
			GUI:
				* Min (bool)
				* ShowErrors (bool)
				* LogActivity (bool)
			Login:
				* Enabled (bool)
				* UsingToken (bool)
				* Data:
					* Username (string)
					* Token (string)
					* Password (string/null)
			* Logs:
				* Auth (string)
				* Database (string)
				* GUI (string)
				* CLI (string)
				* General (string)
		:param conff: The path to the configurations file to load.
		:except InvalidConfig: If the file isn't valid
		:return: True if the configurations file is valid. If the file isn't valid, the method will throw the InvalidConfig
					Exception
		"""
		try:
			with open(conff, "r", encoding="utf-8") as config:
				prs = loads(config.read())
				main_fields = ["Dependencies", "CLI", "GUI", "Login", "Logs"]
				login_fields = ["Username", "Token", "Password"]
				for mf in prs.keys():
					if mf not in main_fields:
						raise self.InvalidConfig(f"Invalid field '{mf}' [::JSON_WHOLE]")
					# start field checking
					if mf == "Dependencies":
						for dp in prs['Dependencies'].keys():
							if dp in ['AutoCheck', 'RunWithout', 'Checked']:
								if not type(prs['Dependencies'][dp]) is bool:
									raise self.InvalidConfig(f"Invalid value [Dependencies::{dp}]")
							else: raise self.InvalidConfig(f"Invalid field '{dp}' [::Dependencies]")
					elif mf == "CLI":
						for cli in prs['CLI'].keys():
							if cli in ["Color", 'Min', 'VerboseAlways', 'ErrorSource', 'LogActivity']:
								if not type(prs['CLI'][cli]) is bool:
									raise self.InvalidConfig(f"Invalid value [CLI::{cli}]")
							else:
								raise self.InvalidConfig(f"Invalid field '{cli}' [::CLI]")
					elif mf == "GUI":
						for gui in prs['GUI'].keys():
							if gui in ["Min", "ShowErrors", "LogActivity"]:
								if not type(prs['GUI'][gui]) is bool:
									raise self.InvalidConfig(f"Invalid value [GUI::{gui}]")
							else:
								raise self.InvalidConfig(f"Invalid field '{gui}' [::GUI]")
					elif mf == "Login":
						for lg in prs['Login'].keys():
							if lg in ["Enabled", "UsingToken"]:
								if not type(prs['Login'][lg]) is bool:
									raise self.InvalidConfig(f"Invalid value [Login::{prs}]")
							elif lg == "Data":
								for dt in prs['Login'][lg].keys():
									if dt not in login_fields:
										raise self.InvalidConfig(f"Invalid field [::Data::Login]")
									# also checking the fields
									if dt == "Username":
										if type(prs['Login']['Data'][dt]) is not str:
											raise self.InvalidConfig(f"Invalid value [Login::Data::{dt}]")
									elif dt == "Token" or dt == "Password":
										if type(prs['Login']['Data'][dt]) is not str and prs['Login']['Data'][dt] is not None:
											raise self.InvalidConfig(f"Invalid value [Login::Data::{dt}]")
									else:
										raise self.InvalidConfig(f"Invalid field '{dt}' [::Data::Login]")
							else:
								raise self.InvalidConfig(f"Invalid field '{lg}' [::Login]")
					else:
						for log in prs['Logs'].keys():
							if log in ['Auth', 'Database', 'GUI', 'CLI', "General"]:
								if type(prs['Logs'][log]) is not str:
									raise self.InvalidConfig(f"Invalid value [Logs::{log}]")
							else: raise self.InvalidConfig(f"Invalid field '{log}' [::Logs]")
				return True
		except FileNotFoundError or PermissionError as error:
			raise self.InvalidConfig(f"Can't access the file '{conff}' [{error.errno}::{error.args}]")
		except JSONDecodeError as json_e:
			raise self.InvalidConfig(f"Can't read the JSON content! [{json_e.msg}::{json_e.pos}]")

	def load_config(self, config_file: AnyStr):
		"""
		Loads a configurations file to the class attributes. If the file is valid (obviously)
		:param config_file: The File to load.
		:except ConfigurationsLoadError: If there's another configurations file loaded already.
		:return: Nothing
		"""
		if self.got_file: raise self.ConfigurationsLoadError("There's another configurations file loaded already;")
		if self.ckconfig(config_file):
			self.config_f = config_file
			with open(self.config_f, mode="r", encoding="UTF-8") as fl: self.document = loads(fl.read())
			self.got_file = True

	@staticmethod
	def format_json(json_content: str) -> str:
		"""
		Format a JSON  inserting a new line (\n) on the following chars:
			* {, }, [, ], ','
		:param json_content: The JSON content string to format
		:return: The formatted JSON content
		"""
		tmp = ""
		for char in ["{", "}", "[", "]", ","]:
			if char == "{": tmp = json_content.replace(char, char+"\n")
			else: tmp = tmp.replace(char, char+"\n")
		return tmp

	def commit(self, formatting: bool = True):
		"""
		Writes all the changes on the configurations file loaded. Normally used when the configurations file is unloaded.
		:param formatting: If the JSON content will be formatted, adding a new line at every '{', '}', "[", "]", ","
		:except ConfigurationsLoadError: If there's no configurations file loaded yet.
		:return: Nothing
		"""
		if not self.got_file: raise self.ConfigurationsLoadError("There's no configurations file loaded yet")
		with open(self.config_f, mode="w", encoding="UTF-8") as fl:
			dumped = dumps(self.document)
			fl.write(dumped if not formatting else self.format_json(dumped))
			del dumped

	def unload_file(self):
		"""
		Unset the class attributes, unparsing the configurations file loaded.
		:except ConfigurationsLoadError: If there's no configurations file loaded yet.
		:return: Nothing
		"""
		if not self.got_file: raise self.ConfigurationsLoadError("There's no configurations file loaded yet")
		self.commit()
		self.document = {}
		self.config_f = ""
		self.got_file = False

	def __init__(self, config: AnyStr = None):
		"""
		Class constructor, it can already load a configurations file.
		:param config: The configurations file to load, if it's None, will set the default values of the attributes
		"""
		if config is not None: self.load_config(config)
		else:
			self.document = {}
			self.config_f = ""
			self.got_file = False

	def __del__(self):
		"""
		Class destructor, that before destructing the class will unparse/unload any configurations file
		:return: Nothing
		"""
		if self.got_file: self.unload_file()






