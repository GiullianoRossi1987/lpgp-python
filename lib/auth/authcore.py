# coding = utf-8
# using namespace std
from socket import socket, AF_INET, SOCK_STREAM, SOL_TCP, SOL_UDP, AF_INET6
from typing import AnyStr
from json import loads
from json import dumps
from json import JSONDecodeError


class GenericBlock(object):
	"""
	That class is a generic way to get the configurations block data. That class work only returning the specific field
	of the block. To avoid calling the config attribute directly from the SocketConfig class.
	:cvar bcontent: The configurations block content received
	:cvar got_cont: If the class got a block content.
	:type bcontent: dict
	:type got_cont: bool
	"""
	bcontent: dict = {}
	got_cont: bool = False

	class InvalidBlock(Exception):
		"""
		<Exception> Raised when the class checks the block and it's invalid. The validation method is make by the
		subclass
		"""

	class ContentError(Exception):
		"""
		<Exception> Raised when the class try to access the configurations block but that isn't loaded yet. Or the class
		try to load a configurations block but there's another block loaded.
		"""

	def __str__(self):
		"""
		Return the JSON string parsed block content
		:return:
		"""
		return dumps(self.bcontent) if self.got_cont else ""


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

	class AddrConfig(GenericBlock):
		"""
		That class represents the Address Configurations block of the configurations file loaded. That class have the main
		methods to get only and directly with the Address configurations block.
		"""
		def ckblock(self, block: dict) -> True:
			"""
			Checks if a configurations block is valid. To be valid the block need to have the following structure:
			  *   Port        (int)
			  *   Name        (str)
			  *   IP          (str)
			  *   IP Protocol (int) [4/6]
			:param block: The block to validate.
			:except InvalidBlock: If there're errors in the block structure
			:return: True if the structure is valid
			"""
			for field in block.keys():
				if field == "Port" and int(block['Port']) <= 0:
					raise self.InvalidBlock("Invalid Port value!")
				elif field == "Name" and (len(block['Name']) <= 0):
					raise self.InvalidBlock("Invalid Name value")
				elif field == "IP" and (len(block['IP']) <= 0):
					raise self.InvalidBlock("Invalid IP value")
				elif field == "IP Protocol" and int(block['IP Protocol']) not in [4, 6]:
					raise self.InvalidBlock("Invalid IP Protocol value")
				elif field not in ["Port", "Name", "IP", "IP Protocol"]: raise self.InvalidBlock(f"Invalid field '{field}'")
			return True

		def parse_block_str(self, block: str, full: bool = True):
			"""
			Loads the configurations block to the class attributes. Using the configurations file string content.
			:param block: The configurations string, directly from the file.
			:param full: If the file have the all blocks, or if it's only the address block content.
			:except ContentError: If there's another block loaded already.
			:return: Nothing
			"""
			if self.got_cont: raise self.ContentError("There're another block loaded!")
			if full:
				prs = loads(block)
				if self.ckblock(prs['Addr']):
					self.bcontent = prs['Addr']
					self.got_cont = True
			else:
				prs = loads(block)
				if self.ckblock(prs):
					self.bcontent = prs
					self.got_cont = True

		def unload_block(self):
			"""
			Unset the class attributes. Making possible load another block
			:except BlockExistanceError: if there's no block loaded.
			:return:
			"""
			if not self.got_cont: raise self.ContentError("There's no block loaded")
			self.bcontent = {}
			self.got_cont = False

		def __init__(self, str_block: str = None):
			"""
			Start the class and set up the attributes, loading the block
			:param str_block: The parsed configurations file content.
			"""
			if str_block is not None: self.parse_block_str(str_block)

		def __del__(self):
			"""
			Garbage collection method, called when a class instance is removed from the memory.
			:return:
			"""
			if self.got_cont: self.unload_block()

	class ActionConfig(GenericBlock):
		"""
		That class contains the main methods to get the attributes of the action configurations block
		"""

		def ckblock(self, block: dict) -> True:
			"""
			Checks if a configurations block is valid. To be valid the block need to have the following structure:
			  * auth-file (str)
			  * Permissive (bool)
			  * SendingMode (int)
			:param block: The block to validate.
			:except InvalidBlock: If there're errors in the block structure
			:return: True if the structure is valid
			"""
			for field in block.keys():
				if field == "auth-file" and len(block['auth-file']) <= 0:
					raise self.InvalidBlock("Invalid Authentication file  value!")
				elif field == "Permissive":
					try:
						b = bool(block[field])
						del b
					except TypeError or ValueError:
						raise self.InvalidBlock("Invalid Name value")
				elif field == "SendingMode" and (int(block['SendingMode']) not in [0, 1, 2]):
					raise self.InvalidBlock("Invalid SendingMode value")
				elif field not in ["auth-file", "Permissive", "SendingMode"]: raise self.InvalidBlock(f"Invalid field '{field}'")
			return True

		def parse_block_str(self, block: str, full: bool = True):
			"""
			Loads the configurations block to the class attributes. Using the configurations file string content.
			:param block: The configurations string, directly from the file.
			:param full: If the file have the all blocks, or if it's only the address block content.
			:except ContentError: If there's another block loaded already.
			:return: Nothing
			"""
			if self.got_cont: raise self.ContentError("There're another block loaded!")
			if full:
				prs = loads(block)
				if self.ckblock(prs['Action']):
					self.bcontent = prs['Action']
					self.got_cont = True
			else:
				prs = loads(block)
				if self.ckblock(prs):
					self.bcontent = prs
					self.got_cont = True

		def unload_block(self):
			"""
			Unset the class attributes. Making possible load another block
			:except BlockExistanceError: if there's no block loaded.
			:return:
			"""
			if not self.got_cont: raise self.ContentError("There's no block loaded")
			self.bcontent = {}
			self.got_cont = False

		def __init__(self, str_block: str = None):
			"""
			Start the class and set up the attributes, loading the block
			:param str_block: The parsed configurations file content.
			"""
			if str_block is not None: self.parse_block_str(str_block)

		def __del__(self):
			"""
			Garbage collection method, called when a class instance is removed from the memory.
			:return:
			"""
			if self.got_cont: self.unload_block()

	class ServerConfig(GenericBlock):
		"""
		That class manages the server configurations block from the configurations file loaded.
		It's a subclass of the GenericBlock class.
		"""

		def ckblock(self, block: dict) -> True:
			"""
			Checks if a configurations block is valid. To be valid the block need to have the following structure:
			  *   Port        (int)
			  *   Name        (str)
			  *   IP          (str)
			  *   IP Protocol (int) [4/6]
			:param block: The block to validate.
			:except InvalidBlock: If there're errors in the block structure
			:return: True if the structure is valid
			"""
			for field in block.keys():
				if field == "Port" and int(block['Port']) <= 0:
					raise self.InvalidBlock("Invalid Port value!")
				elif field == "Name" and (len(block['Name']) <= 0):
					raise self.InvalidBlock("Invalid Name value")
				elif field == "IP" and (len(block['IP']) <= 0):
					raise self.InvalidBlock("Invalid IP value")
				elif field == "IP Protocol" and int(block['IP Protocol']) not in [4, 6]:
					raise self.InvalidBlock("Invalid IP Protocol value")
				elif field == "WaitHS":
					try:
						b = bool(block['WaitHS'])
						del b
					except TypeError or ValueError:
						raise self.InvalidBlock("Invalid WaitHS Value")
				elif field not in ["Port", "Name", "IP", "IP Protocol", "WaitHS"]: raise self.InvalidBlock(f"Invalid field '{field}'")
			return True

		def parse_block_str(self, block: str, full: bool = True):
			"""
			Loads the configurations block to the class attributes. Using the configurations file string content.
			:param block: The configurations string, directly from the file.
			:param full: If the file have the all blocks, or if it's only the address block content.
			:except ContentError: If there's another block loaded already.
			:return: Nothing
			"""
			if self.got_cont: raise self.ContentError("There're another block loaded!")
			if full:
				prs = loads(block)
				if self.ckblock(prs['Server']):
					self.bcontent = prs['Server']
					self.got_cont = True
			else:
				prs = loads(block)
				if self.ckblock(prs):
					self.bcontent = prs
					self.got_cont = True

		def unload_block(self):
			"""
			Unset the class attributes. Making possible load another block
			:except BlockExistanceError: if there's no block loaded.
			:return:
			"""
			if not self.got_cont: raise self.ContentError("There's no block loaded")
			self.bcontent = {}
			self.got_cont = False

		def __init__(self, str_block: str = None):
			"""
			Start the class and set up the attributes, loading the block
			:param str_block: The parsed configurations file content.
			"""
			if str_block is not None: self.parse_block_str(str_block)

		def __del__(self):
			"""
			Garbage collection method, called when a class instance is removed from the memory.
			:return:
			"""
			if self.got_cont: self.unload_block()

	def get_addr(self) -> AddrConfig:
		"""
		Return the Address Configurations block parsed using the AddrConfig class.
		:except ConfigLoadError: If there's no configurations file loaded yet.
		:return: The address configurations block
		"""
		if not self.got_file: raise self.ConfigLoadError("There's no configurations file loaded yet!")
		addr = self.AddrConfig() # empty for while
		with open(self.file_got, "r") as conf_tmp: addr.parse_block_str(conf_tmp.read())
		return addr

	def get_server(self) -> ServerConfig:
		"""
		Return the Server Configurations block, parsed using the ServerConfig class.
		:except ConfgiLoadError: If there's no configurations file loaded yet
		:return: The server configurations block
		"""
		if not self.got_file: raise self.ConfigLoadError("There's no configurations file loaded yet")
		server = self.ServerConfig()
		with open(self.file_got, "r") as tmp: server.parse_block_str(tmp.read())
		return server

	def get_action(self) -> ActionConfig:
		"""

		:return:
		"""


class Client4(object):
	"""
	Socket client for IPV4 connections, using the normal stream. It loads the
	"""