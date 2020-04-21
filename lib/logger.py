# coding = UTF-8
# using namespace std
from typing import AnyStr
from time import strftime
from yaml import load as yamlLoad
from yaml import dump as yamlDump
from yaml.loader import Loader
from yaml.dumper import Dumper
from yaml import YAMLError, MarkedYAMLError


class DefaultLogger(object):
	"""
	That class writes and reads a logs file, doing the management of the system actions.
	It also have the logs files uses and definitions.

	:cvar logsFile: The logs file loaded to manage
	:cvar gotFile: If the class have a logs file loaded.

	:type logsFile: AnyStr
	:type gotFile: bool
	"""
	logsFile: AnyStr
	gotFile: bool = False

	class NoLogFileFound(Exception):
		"""
		<Exception> raised when the logger try to access the logsFile, but it isn't configured
		"""

	class LogFileAlreadyLoaded(Exception):
		"""
		<Exception> raised when the logger try to load a logsFile, but the class already loaded a logs file.
		"""

	@classmethod
	def errorLogs(cls):
		"""
		Creates a new instance of the class, but with the errors logs file loaded.
		:return: The new class instance with the error log file of the SDK
		"""
		if cls.gotFile: raise cls.LogFileAlreadyLoaded("There's a logs file already loaded.")
		cls.logsFile = "logs/error.log"
		cls.gotFile = True
		return cls

	@classmethod
	def mysqlLogs(cls):
		"""
		Creates a new instance of the class, but with the mysql client default logs file loaded.
		:return: The new class instance with the mysql client default logs file.
		"""
		if cls.gotFile: raise cls.LogFileAlreadyLoaded("There's a logs file already loaded")
		cls.logsFile = "logs/client-mysql.log"
		cls.gotFile = True

	@classmethod
	def genLogs(cls):
		"""
		Creates a new instance of the class, but with the system general logs file loaded.
		:return: The new class instance witht the system general logs file loaded.
		"""
		if cls.gotFile: raise cls.LogFileAlreadyLoaded("There's a logs file already loaded")
		cls.logsFile = "logs/general.log"
		cls.gotFile = True

	def __init__(self, logs_file: AnyStr = None):
		"""
		Starts the class and set up a logs file chosen by the instance.
		:type logs_file: basestring
		:param logs_file: The logsFile to load
		"""
		if self.gotFile: raise self.LogFileAlreadyLoaded("There's a logs file already loaded.")
		if logs_file is None:
			self.logsFile = ""
			self.gotFile = False
		else:
			self.logsFile = logs_file
			self.gotFile = True

	def unloadFile(self):
		"""
		That method unset the logs file loaded, making possible load a new logs file.
		"""
		if not self.gotFile: raise self.NoLogFileFound("There's no logs file loaded")
		self.logsFile = ""
		self.gotFile = False

	def __del__(self):
		"""
		That method is used for the default garbage collection of the class instances and objects.
		:return:
		"""
		if self.gotFile: self.unloadFile()

	def addLog(self, action: str, success: bool = True, err_msg: str = None, err_code: int = None):
		"""
		That method adds a record on the logs file loaded by the class.
		:param action: The action performed
		:param success: If it was successful
		:param err_msg: If there was a error, the error message.
		:param err_code: If there was a error the error code.
		:except NoLogFileFound: If the class don't have any logs file laoded.
		:return: Nothing
		"""
		if not self.gotFile: raise self.NoLogFileFound("There's no logs file loaded")
		with open(self.logsFile, "a+", encoding="UTF-8") as logs:
			logToJoin = [
				"[" + strftime("%Y-%m-%d %H:%M:%S") + "]",
				str(err_code) if not success else "",
				action,
				"ERROR: " + err_msg if not success else "",
				"\n"]
			logs.write("    ".join(logToJoin))
			del logToJoin


class Envvars(object):
	"""
	That class loads and manages the environment variables of the system. Those environment variables are setted in the
	lib/envvars.yml file. Those variables are miscellaneous for the system, but we must have then working.

	:cvar envFile: The environment vars file loaded
	:cvar gotVars: If the class got a envFile attribute configured
	:cvar __logger: That's the logs file managed to use.
	:cvar envvars:  Here's the YAML file content parsed, ready for use as the variables.
	"""
	envFile: AnyStr = ""
	gotVars: bool = False
	__logger: DefaultLogger = DefaultLogger("logs/general.log")
	envvars: dict = dict()

	class NoEnvVarsLoaded(Exception):
		"""
		<Exception> Raised when the class try to access the envvars file or the envvars parsed and both, or one of those
		isn't configured
		"""
		ERR_CODE = 1098

	class EnvVarsLoaded(Exception):
		"""
		<Exception> Raised when the class try to reconfigure the loaded envvars file, which is already configured
		"""
		ERR_CODE = 1099

	def loadFile(self, envfile: AnyStr):
		"""
		That method loads a envvars file to the class and parses it.
		:param envfile: The envvars file to load.
		:raise EnvVarsLoaded: If the class already have a envvars file loaded
		:return: Nothing
		"""
		if self.gotVars:
			self.__logger.addLog(f"Tried to load file '{envfile}'", False,
								 f"EnvVars '{self.envFile}' file loaded already! ", self.EnvVarsLoaded.ERR_CODE)
			raise self.EnvVarsLoaded("EnvVars file loaded already!")
		try:
			with open(envfile, "r", encoding='utf-8') as envvars:
				try:
					self.envvars = yamlLoad(envvars.read(), Loader)
				except MarkedYAMLError or YAMLError as yml_err1:
					self.__logger.addLog(f"Tried to read file {envfile}", False, f"PACK_ERROR [yaml::YAMLError]: {yml_err1}", 100)
					raise yml_err1
				else:
					self.envFile = envfile
					self.gotVars = True
					self.__logger.addLog(f"Loaded envvars file {envfile}", True)
		except FileNotFoundError or PermissionError as internal:
			self.__logger.addLog(f"Tried to load file {envfile}", False, f"INTERNAL [{internal}]: {internal}", 404)
		else: pass

	def reparse(self):
		"""
		That method reparses a envvars file loaded. Reloading the envvars parseds
		:raises NoEnvVarsLoaded: If the class don't have a envvars file loaded.
		:return: Nothing
		"""
		if not self.gotVars:
			self.__logger.addLog("Tried to load internal envvars file", False, "No envvars file found!", self.NoEnvVarsLoaded.ERR_CODE)
			raise self.NoEnvVarsLoaded("No envvars file loaded!")
		with open(self.envFile, "r", encoding="utf-8") as reparse:
			try:
				self.envvars = yamlLoad(reparse.read(), Loader)
			except MarkedYAMLError or YAMLError as yml_err1:
				self.__logger.addLog(f"Tried to reparse file {self.envFile}", False, f"PACK_ERROR [yaml::YAMLError]: {yml_err1}", 100)
				raise yml_err1
			else: self.__logger.addLog(f"Reloaded envvars file {self.envFile}", True)

	def dumpsFile(self):
		"""
		That method writes in the envvars file loaded.
		:raises NoEnvVarsLoaded: If the class don't have a envvars file loaded.
		"""
		if not self.gotVars:
			self.__logger.addLog("Tried to load internal envvars file", False, "No envvars file found!", self.NoEnvVarsLoaded.ERR_CODE)
			raise self.NoEnvVarsLoaded("No envvars file loaded!")
		with open(file=self.envFile, mode="w", encoding="utf-8") as toDump:
			try:
				dumped = yamlDump(data=self.envvars, Dumper=Dumper)
				toDump.write(dumped)
			except YAMLError or MarkedYAMLError as yml_err2:
				self.__logger.addLog(f"Tried to write in {self.envFile}", False, f"PACK_ERROR [yaml::]: {yml_err2}", 100)
				raise yml_err2
			except FileNotFoundError or PermissionError as internal:
				self.__logger.addLog(f"Tried to write/access the file {self.envFile}", False, f"INTERNAL: {internal}", 404)
				raise internal
			else:
				self.__logger.addLog(f"Wrote file {self.envFile}")

	def __init__(self, envfile: AnyStr = "lib/envvars.yml"):
		"""
		Starts the class with a envvars file loaded
		:param envfile: The envvars file to load.
		"""
		if envfile is not None:
			self.loadFile(envfile)
		else:
			self.envFile = ""
			self.envvars = {}
			self.gotVars = False

	def unloadFile(self):
		"""
		That method closes any envvars file loaded by the class.
		:raises NoEnvVarsLoaded: If there's no logs file loaded yet.
		"""
		if not self.gotVars:
			self.__logger.addLog("Tried to load internal envvars file", False, "No envvars file loaded", self.NoEnvVarsLoaded.ERR_CODE)
			raise self.NoEnvVarsLoaded("No envvars file loaded !")
		self.dumpsFile()
		toLog = self.envFile
		self.envFile = ""
		self.envvars = {}
		self.gotVars = False
		self.__logger.addLog(f"Closed envvars file {toLog}")
		del toLog

	def __del__(self):
		"""
		Method normally used for the garbage collection of the class instance and objects.
		It will close any envvars file loaded before terminating the instance.
		"""
		if self.gotVars: self.unloadFile()

	@property
	def mysqlInstances(self) -> int:
		"""
		That property represents the MySQL instancces open referred in the envvars file.
		:raises NoEnvVarsLoaded: If the class don't have a envvars file loaded yet.
		:return: The MySQL instances value from the envvars file.
		"""
		if not self.gotVars:
			self.__logger.addLog("Tried to load internal envvars file", False, "No envvars file loaded", self.NoEnvVarsLoaded.ERR_CODE)
			raise self.NoEnvVarsLoaded("There's no envvars file loaded.")
		else:
			self.__logger.addLog("Access permitted to the MySQL instances field")
			return int(self.envvars['temp']['mysqlInstances'])

	@mysqlInstances.setter
	def mysqlInstances(self, value: int):
		"""
		Overwrite the envvars file field mysqlInstances with another number
		:param value: The value to set.
		:raises NoEnvVarsLoaded: If there's no envvars file loaded.
		"""
		if not self.gotVars:
			self.__logger.addLog("Tried to load internal envvars file", False, "No envvars file loaded",
								 self.NoEnvVarsLoaded.ERR_CODE)
			raise self.NoEnvVarsLoaded("There's no envvars file loaded.")
		else:
			self.envvars['temp']['mysqlInstances'] = value
			self.dumpsFile()
			self.__logger.addLog(f"Overwrote mysqlInstances field value, to: {value}")

	@property
	def signaturesCount(self) -> int:
		"""
		That property represents the signature authenticated times.
		:raises NoEnvVarsLoaded: If the class don't have a envvars file laaded yet.
		:return: The envvars file field value
		"""
		if not self.gotVars:
			self.__logger.addLog("Tried to load internal envvars file", False, "No envvars file loaded",
								 self.NoEnvVarsLoaded.ERR_CODE)
			raise self.NoEnvVarsLoaded("There's no envvars file loaded.")
		else:
			self.__logger.addLog("Access permitted to the signatures counts field")
			return int(self.envvars['temp']['signaturesLoadeds'])

	@signaturesCount.setter
	def signaturesCount(self, value: int):
		"""
		That method set a new value to the property signaturesCount of the class, it also will overwrite the envvars file
		after the value changing.
		:param value: The new field value
		:raises NoEnvVarsLoaded: If the class don't have a envvars file loaded yet.
		"""
		if not self.gotVars:
			self.__logger.addLog("Tried to load internal envvars file", False, "No envvars file loaded",
								 self.NoEnvVarsLoaded.ERR_CODE)
			raise self.NoEnvVarsLoaded("There's no envvars file loaded.")
		else:
			self.envvars['temp']['signaturesLoadeds'] = value
			self.dumpsFile()
			self.__logger.addLog(f"Overwrote the envvars file, seated the signaturesLoadeds field to: {value}")

	@property
	def timesAuth(self) -> int:
		"""
		That property represents how many times the client was authenticated.
		:raises NoEnvVarsLoaded: If the class don't have a envvars file loaded yet
		:return: The field timesAuthenticated value
		"""
		if not self.gotVars:
			self.__logger.addLog("Tried to load internal envvars file", False, "No envvars file loaded",
								 self.NoEnvVarsLoaded.ERR_CODE)
			raise self.NoEnvVarsLoaded("There's no envvars file loaded.")
		else:
			self.__logger.addLog("Access permitted to timesAuthenticated field")
			return int(self.envvars['temp']['timesAuthenticated'])

	@timesAuth.setter
	def timesAuth(self, value: int):
		"""
		That method sets a new integer value to the timesAuth property.
		:param value: The new timesAuthenticated field value.
		:raises NoEnvVarsLoaded: If the class don't have a envvars file loaded yet.
		"""
		if not self.gotVars:
			self.__logger.addLog("Tried to load internal envvars file", False, "No envvars file loaded",
								 self.NoEnvVarsLoaded.ERR_CODE)
			raise self.NoEnvVarsLoaded("There's no envvars file loaded.")
		else:
			self.envvars['temp']['timesAuthenticated'] = value
			self.dumpsFile()
			self.__logger.addLog(f"Overwrote the field timesAuthenticated to value: {value}")

	def resetVals(self):
		"""
		That method will reset all the values of the fields to 0, used when the class terminates it self.
		:raises NoEnvVarsLoaded: If the class don't have any envvars file loaded yet.
		"""
		if not self.gotVars:
			self.__logger.addLog("Tried to load internal envvars file", False, "No envvars file loaded",
								 self.NoEnvVarsLoaded.ERR_CODE)
			raise self.NoEnvVarsLoaded("There's no envvars file loaded.")
		self.mysqlInstances = 0
		self.signaturesCount = 0
		self.timesAuth = 0
		self.__logger.addLog("Reset the values of the vars.")
