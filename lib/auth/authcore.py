# coding = utf-8
# using namespace std
from socket import socket, AF_INET, SOCK_STREAM, SOL_TCP, SOL_UDP, AF_INET6
from typing import AnyStr
from json import loads
from json import dumps
from json import JSONDecodeError


class SocketConfig(object):
	"""
	That class manages the configurations file of the socket client for the authentication.
	The configurations file of the socket client is very important for the authentication of
	the client signature.
	:cvar config: The configurations parsed.
	:cvar got_file: If the class got a configurations file.
	:cvar file_got: The configurations file that the class got.
	:type file_got: basestring
	:type got_file: False
	:type config: dict
	:author Giulliano Rossi <giulliano.scatalon.rossi@gmail.com>
	"""
	file_got: AnyStr
	config: dict
	got_file: bool = False

	################################################################################
	# Exceptions

	class ConfigLoadError(Exception):
		"""
		<Exception> Raised when the class try to load a configurations file, but there's another configurations file
		loaded already. Also raised when the class try to do any action with the configurations file, but there's no
		configurations file loaded yet
		"""

	class InvalidFile(Exception):
		"""
		<Exception> Raised when the class try to load a invalid configurations file. To see the valid file requirements
		check the ckfile method.
		"""

	def ckfile(self, file_to: AnyStr) -> True:
		"""
		Check if the client configurations file is valid or not. To be a valid configurations file the file must have
		the following structure:
			* Addr
			  |   Port        (int)
			  |   Name        (str)
			  |   IP          (str)
			  |   IP Protocol (int) [4/6]
			* Action:
			  |   auth-file   (AnyStr)
			  |   Permissive  (bool)
			  |   SendingMode (int)
			* Server:
			  |	  Port         (int)
			  |   Name         (str)
			  |   IP           (str)
			  |   WaitHS       (bool)
			  |   IP Protocol  (int) [4/6]
		:param file_to: The file to check
		:except InvalidFile: If there's errors in the file structure
		:return: True if the file is valid.
		"""
		try:
			with open(file_to, "r") as conf:
				prs = loads(conf.read())
				for addr_con in prs['Addr'].keys():
					if addr_con == "Port" and int(prs['Addr']['Port']) <= 0:
						raise self.InvalidFile("Invalid Port value at the Addr field")
					elif addr_con == "Name" and len(str(prs['Addr']['Name'])) <= 0:
						raise self.InvalidFile("Invalid Name value at the Addr field")
					elif addr_con == "IP" and len(str(prs['Addr']['IP'])) <= 0:
						raise self.InvalidFile("Invalid IP address at the Addr field")
					elif addr_con == "IP Protocol" and int(prs['Addr']['IP Protocol']) not in [4, 6]:
						raise self.InvalidFile("Invalid IP Protocol at the Addr field")
					elif addr_con not in ["Port", "Name", "IP", "IP Protocol"]:
						raise self.InvalidFile(f"Invalid Field '{addr_con}' at the Addr field")
				for action_con in prs['Action'].keys():
					if action_con == "auth-file":
						try:
							o = open(prs['Action']['auth-file'], "r")
							del o
						except FileNotFoundError or PermissionError as e:
							raise self.InvalidFile(f"Invalid client signature file [{e.args}] at the Actions field")
						else: continue
					elif action_con == "Permissive":
						try: bool(prs['Action']['Permissive'])
						except ValueError or TypeError:
							raise self.InvalidFile("Invalid value at Permissive field at the Action field")
						else: continue
					elif action_con == "SendingMode" and int(prs['Action']['SendingMode']) not in [0, 1, 2]:
						raise self.InvalidFile("Invalid value at the SendingMode in Action field")
					elif action_con not in ["auth-file", "Permissive", "SendingMode"]:
						raise self.InvalidFile(f"Invalid field {action_con} at the Action field")
				for server_con in prs['Server'].keys():
					if server_con == "Port" and int(str(prs['Server']['Port'])) <= 0:
						raise self.InvalidFile("Invalid Port value at the Server Field")
					elif server_con == "Name" and len(str(prs['Server']['Name'])) <= 0:
						raise self.InvalidFile("Invalid Name value at the Server field")
					elif server_con == "IP" and len(str(prs['Server']['IP'])) <= 0:
						raise self.InvalidFile("Invalid IP address at the Server field")
					elif server_con == "IP Protocol" and int(prs['Server']['IP Protocol']) not in [4, 6]:
						raise self.InvalidFile("Invalid IP Protocol at the Server field")
					elif server_con == "WaitHS":
						try: bool(prs['Server']['WaitHS'])
						except ValueError or TypeError:
							raise self.InvalidFile("Invalid WaitHS value at the Server field")
					elif server_con not in ["Port", "IP", "Name", "IP Protocol", "WaitHS"]:
						raise self.InvalidFile(f"Invalid field '{server_con}' at the Server Field")
				return True
		except FileNotFoundError or PermissionError: raise self.InvalidFile("Unrecheable file")
		except JSONDecodeError as e: raise self.InvalidFile("Can't read the content: " + e.msg)
		else: return True

	def load_file(self, config: AnyStr):
		"""
		Loads a configurations file to the class attributes.
		:param config: The configurations file to load.
		:except ConfigurationsLoadError: If there's another configurations file loaded already
		"""
		if self.got_file: raise self.ConfigLoadError("There's another configurations file loaded already", 1)
		if self.ckfile(config):
			self.file_got = config
			with open(self.file_got, "r") as config_sock: self.config = loads(config_sock.read())
			self.got_file = True

	def commit(self, format_json: bool = False):
		"""
		Write all the changes done on the loaded document to the configurations file loaded.
		:except ConfigLoadError: If there's no configurations file loaded yet;
		:param format_json: If the "{" and "," at the document will be succeeded by a new line
		:return: None
		"""
		if not self.got_file: raise self.ConfigLoadError("There's no configurations file loaded yet!")
		with open(self.file_got, mode="w", encoding="utf-8") as file:
			dumped = dumps(self.config)
			if format_json:
				chars = ["{", "}", ","]
				for ck in chars:
					if ck == "{": tmp = dumped.replace(ck, ck+"\n")
					else:
						if ck == "}": tmp = tmp.replace(ck, "\n"+ck)
						tmp = tmp.replace(ck, ck+"\n")
				dumped = tmp
			file.write(dumped)
			del dumped

	def unload(self):
		"""
		Unload the configurations file loaded, unseting the class attributes that the class just loaded.
		:except ConfigLoadError: If the configurations file wasn't loaded yet.
		:return: Nothing
		"""
		if not self.got_file: raise self.ConfigLoadError("There's no configurations file loaded yet;")
		self.commit()
		self.config   = dict()
		self.file_got = ""
		self.got_file = False

	def __init__(self, config: AnyStr = None):
		"""
		Starts the class and set up the attributes, if the config param is not None.
		:param config: The configurations file to autoload with the __init__ method.
		"""
		if config is not None: self.load_file(config)

	def __del__(self):
		"""
		Method used for the garbage collection, when the class instance/object will be deleted from memory. It just
		unload any configurations file before deleting the instance/object from the memory.
		:return: Nothing
		"""
		if self.got_file: self.unload()


class Client4(object):
	"""
	Socket client for IPV4 connections, using the normal stream. It loads a configurations class and uses it to the socket.
	:cvar config: The configurations loaded using the SocketConfig class.
	:cvar sock: The socket to use.
	"""
	config: SocketConfig
	sock: socket = socket(AF_INET, SOCK_STREAM)

	class SocketNotConfigured(Exception):
		"""
		Raised if the class try to access the own socket object but the socket object wasn't configured yet.
		"""

	class SocketAlreadyConfigured(Exception):
		"""
		Raised when the class try to configure the socket object, but the object is already configured. Normally it's
		raised at the chsk method, but if you want to overwrite the configurations of the socket object use the method
		oversk.
		"""

	class ConfigNotLoaded(Exception):
		"""
		Raised when the class try to access the SocketConfig object, but it wasn't loaded
		"""

