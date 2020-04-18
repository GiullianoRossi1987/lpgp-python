# coding = UTF-8
# using namespace std
from typing import AnyStr
from time import strftime


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
			logToJoin = [strftime("%Y-%m-%d %H:%M:%S"), str(err_code) if not success else "", action,
						 err_msg if not success else "", "\n"]
			logs.write("    ".join(logToJoin))
			del logToJoin
