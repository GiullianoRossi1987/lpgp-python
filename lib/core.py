# coding = utf-8
# using namespace std
from pymysql.connections import Connection as MySQLConnection
from time import strftime
from json import loads, dumps, JSONDecodeError
from typing import AnyStr
from pymysql import connect
from base64 import b64encode
from base64 import b64decode
import hashlib


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
						if type(l) is not str or len(l) == 0:
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
					elif i == "RootMode":
						if type(l) is not bool:
							raise self.InvalidConfigurationsFile("Invalid value [RootMode::] expecting boolean type")
					elif i == "Mode":
						if type(l) is not int or l not in [0, 1]:
							# 0 => proprietary; 1 => normal
							raise self.InvalidConfigurationsFile("Invalid value [Mode::] expecting 1, 0")
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
			chars = ["{", "}", ","]
			for ck in chars:
				if ck == "{": tmp = dumped.replace(ck, ck+"\n")
				else:
					if ck == "}": tmp = tmp.replace(ck, "\n"+ck)
					tmp = tmp.replace(ck, ck+"\n")
			dumped = tmp
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


class MySQLExternalConnection(object):
	"""
	That class have the main methods and exceptions to manage the MySQL database external (original LPGP). It use the
	MySQLConnectionOptions class to work with a extra protective form. The access to the database is only gave to the
	class when the client file (actualy it's in lib/auth/auth.lpgp) was authenticated by the official server.
	That authentication is made using the lib.auth.authcore.Client4 class to connect the server.
	After all that process the server will return, if the client's valid obviously, the username to access the database.

	:cvar connection: The MySQL (pymysql) connection object to the MySQL database
	:cvar con_data: The main connection options and important info
	:cvar got_conn: Reports if the class got a connection with a MySQL database or not.

	:type connection: MySQLConnection
	:type con_data: MySQLConnectionOptions
	:type got_conn: bool
	"""
	connection: MySQLConnection
	con_data: MySQLConnectionOptions
	got_conn: bool = False

	class RootRequiredError(PermissionError):
		"""
		Exception raised when the MySQL client try to do a action that requires a root client, actions like changing self
		data or self signatures data. Also access some data like the hashed password or the signature pure hash or other
		data such as the ID.
		"""

	class ConnectionError(Exception):
		"""
		Exception raised when the class try to load a MySQL client and connection data, but there's another client created
		or configured already as a attribute. Also raised when the class try to access the client and/or the connection
		data but there's no connection configured or loaded.
		"""

	def add_log(self, action: str, success: bool = True):
		"""
		That method writes every action the client do in the default connection logs file, the file path is defined by
		the client configurations file.
		:param action: The action that the client did
		:param success: If it was successfully executed
		:except ConnectionError: If there's no client or connection options loaded.
		"""
		if not self.got_conn: raise self.ConnectionError("There's no connection or connections configurations file loaded!")
		with open(self.con_data.document['General']['Connection-Logs'], "a+", encoding="UTF-8") as logs:
			today = strftime("%Y-%m-%d %H:%M:%S")
			err = "{ERROR}" if not success else ""
			logs.write(f"[{today}] {err} {action}")
			del today, err

	def connect(self, config: MySQLConnectionOptions, usr_access: str, passwd_access: str = ""):
		"""
		That method configure the MySQL client and set the main class attributes
		:param config: The MySQLConnectionOptions object to load, to get the connection options.
		:param usr_access: The user access received from the server
	
		:except ConnectionError: If the class already got a connection
		"""
		if self.got_conn: raise self.ConnectionError("There's a MySQL connection already configured!")

		self.con_data = config
		self.connection = connect(
			host=self.con_data.document['General']['Primary-Host'],
			port=int(self.con_data.document['General']['Default-Port']),
			user=usr_access,
			db="LPGP_WEB"
		)
		self.got_conn = True
		self.add_log(f"STARTED CONNECTION WITH {self.con_data.document['General']['Primary-Host']}::{self.con_data.document['General']['Default-Port']}")

	def disconnect(self):
		"""
		That class unset the class attributes. Used to generate another connection but with the same class object/instance.
		:except ConnectionError: If the class isn't connected
		"""
		if not self.got_conn: raise self.ConnectionError("The class must be connected!")
		self.connection.commit()
		self.connection.close()
		self.con_data.unload()
		self.got_conn = False

	def __init__(self, config: MySQLConnectionOptions = None, usr_access: str = None):
		"""
		That method initialize the class instance/object creating a connection with a MySQL database server. If any of
		the methods parameters is None then the class will set default values for the attributes.
		:param config: The MySQLConnectionOptions object to load
		:param usr_access: The user access received
		"""
		if config is not None and usr_access is not None: self.connect(config, usr_access)

	def __del__(self):
		"""
		Disconnect the client before deleting the class object/instance. Used only for the garbage collection.
		"""
		if self.got_conn: self.disconnect()


class MySQLAccountManager(MySQLExternalConnection):
	"""
	That class represents the account of the client proprietary or simple user. That manage the account which have the
	client. Those methods are to get the client owner data or change it.
	"""

	class InvalidEmail(Exception):
		"""
		Exception raised when the client try to change the owner e-mail, but it isn't valid. To be valid the e-mail
		address must have '@' character and '.com'
		"""

	def get_info(self) -> tuple:
		"""
		That method return the owner info, such as him name, email, password, if it was checked or not.
		The method don't require root account.
		:except ConnectionError: If there's no database connected.
		:return: A tuple with it data
		"""
		if not self.got_conn: raise self.ConnectionError("There's no database connected")
		with self.connection.cursor() as cursor:
			if self.con_data.document["Mode"] == 0:
				rt = cursor.execute(f"SELECT nm_proprietary, vl_email, vl_password, dt_creation FROM tb_proprietaries WHERE cd_proprietary = {self.con_data.document['LocalAccountID']};")
			else:
				rt = cursor.execute(f"SELECT nm_user, vl_email, vl_password, dt_creation FROM tb_users WHERE cd_user = {self.con_data.document['LocalAccountID']};")
			raw = cursor.fetchone()
			return tuple(raw) + tuple([self.con_data.document['Mode']])

	@staticmethod
	def dump_dict(data: tuple) -> dict:
		"""
		That method return the user main data in a dictionary. That method can be used even without a database connected.
		:param data: The user data on the tuple
		:return: The dictionary with the tuple data.
		"""
		return {
			'Name': data[0],
			"Email": data[1],
			"Password": b64decode(data[2]),
			"Date-Creation": data[3],
			"Type-mode": "proprietary" if data[4] == 0 else "normal"
		}

	@staticmethod
	def dump_list(data: tuple) -> list:
		"""
		That method return the user main data in a list. That method can be used even without a database connected
		:param data: The tuple with the user data
		:return: A list with the data dumped
		"""
		dt = []
		for index, data_item in enumerate(data):
			if index == 4:
				dt.append("proprietary" if data_item == 0 else "normal-user")
			else:
				dt.append(data_item)
		return dt

	# Root Methods
	####################################################################################################################

	def ch_nm(self, new_name: str):
		"""
		That method changes the user name. That method can only be done with a
		:param new_name: The new name value
		:except ConnectionError: If the class didn't got a database connected
		:except RootRequiredError: If the client isn't a root client to do that action
		"""
		if not self.got_conn: raise self.ConnectionError("There's no database connected")
		if not self.con_data.document['RootMode']:
			raise self.RootRequiredError("The client don't have permission to do that!")
		with self.connection.cursor() as cursor:
			if self.con_data.document['Mode'] == 0:
				rt = cursor.execute(f"UPDATE tb_proprietaries SET nm_proprietary = \"{new_name}\" WHERE cd_proprietary = {self.con_data.document['LocalAccountID']};")
			else:
				rt = cursor.execute(f"UPDATE tb_users SET nm_user = \"{new_name}\" WHERE cd_user = {self.con_data.document['LocalAccountID']};")
			del rt

	@staticmethod
	def ck_email(email: str) -> bool:
		"""
		That method checks if a e-mail address is or isn't valid. To be valid it must have the '@'character and '.com'
		string it end
		:param email: The email address to check
		:return: True if the email is valid and False if it isn't
		"""
		dp = email.split(".")
		if '@' not in email: return False
		if dp[-1] != ".com": return False
		del dp
		return True

	def ch_email(self, new_email: str):
		"""
		That method changes the email address of the client owner.
		:param new_email: The new email address to set
		:except ConnectionError: If the client isn't connected
		:except RootRequiredError: If the client isn't a root client
		:except InvalidEmail: If the email address isn't valid
		"""
		if not self.got_conn: raise self.ConnectionError("The class isn't connected!")
		if not self.con_data.document['RootMode']:
			raise self.RootRequiredError("The root permission is required for that action!")
		if not self.ck_email(new_email):
			raise self.InvalidEmail("Invalid e-mail address! Please verify if it have '@' and '.com'")
		with self.connection.cursor() as cursor:
			if self.con_data.document['Mode'] == 0:
				rq = cursor.execute(f"UPDATE tb_proprietaries SET vl_email = \"{new_email}\" WHERE cd_proprietary = {self.con_data.document['LocalAccountID']};")
			else:
				rq = cursor.execute(f"UPDATE tb_users SET vl_email = \"{new_email}\" WHERE cd_user = {self.con_data.document['LocalAccountID']};")
			del rq

	def ch_passwd(self, new_passwd: str, encoded: bool = False):
		"""
		That method changes the owner password.
		:param new_passwd: The new password to set
		:param encoded: If the password is encrypted, if not it'll encrypt it
		:except ConnectionError: If the class ins't connected to the database.
		:except RootRequiredError: If the client isn't a root client
		"""
		if not self.got_conn: raise self.ConnectionError("The class isn't connected")
		if not self.con_data.document['RootMode']:
			raise self.RootRequiredError("The root client is required for that action")
		with self.connection.cursor() as cursor:
			passwd_new = b64encode(new_passwd) if not encoded else new_passwd
			if self.con_data.document['Mode'] == 0:
				rt = cursor.execute(f"UPDATE tb_proprietaries SET vl_password = \"{passwd_new}\" WHERE cd_proprietary = {self.con_data.document['LocalAccountID']}")
			else:
				rt = cursor.execute(
					f"UPDATE users SET vl_password = \"{passwd_new}\" WHERE cd_user = {self.con_data.document['LocalAccountID']}")
			del rt


class MySQLOwnerHistory(MySQLExternalConnection):
	"""
	That class manages the client owner signature check history. That management is just add and list the history records
	"""

	def get_tb(self) -> str:
		"""
		That method is simple, it just return one table if the owner is a proprietary or a normal user.
		:except ConnectionError: If the class isn't connected
		:return: The table used for the owner account type.
		"""
		if not self.got_conn: raise self.ConnectionError("The client isn't connected!")
		return "tb_signatures_prop_h" if self.con_data.document["Mode"] == 0 else "tb_signature_check_history"

