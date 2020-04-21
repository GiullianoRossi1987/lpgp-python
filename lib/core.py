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
from os import listdir
from sys import platform
from lib.client_data import ClientDataAuto
from lib.logger import DefaultLogger as Logger
from lib.logger import Envvars

gbl_err = Logger("logs/error.log")
gbl_signatures = Logger("logs/signatures-gen.log")
gbl_connection = Logger("logs/mysql-con.log")
gbl_vars = Envvars()


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
		ERR_CODE = 1432

	class InvalidConfigurationsFile(Exception):
		"""
		Exception raised when the configurations file class try to load a configurations file, but that isn't a valid
		configurations file. To see the valid configurations file requirements just read the docs of the ckconfig
		method
		"""
		ERR_CODE = 1433

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
							gbl_connection.addLog(f"[MySQLConnectionOptions] tried to load the file {config}", False,
												  "Invalid value [Primary-Host::] expecting IP on string", 1433)
							raise self.InvalidConfigurationsFile("Invalid value [Primary-Host::] expecting IP on string")
					elif i == "Default-Port":
						if type(l) is not int or l <= 0:
							gbl_connection.addLog(f"[MySQLConnectionOptions] tried to load the file {config}", False,
												  "Invalid value [Default-Port::] expecting int more then 0", 1433)
							raise self.InvalidConfigurationsFile("Invalid value [Default-Port::] expecting int more then 0")
					elif i == "Connection-Logs":
						if type(l) is not str or len(l) == 0:
							gbl_connection.addLog(f"[MySQLConnectionOptions] tried to load the file {config}", False,
												  "Invalid value [Connection-Logs::] expecting file path", 1433)
							raise self.InvalidConfigurationsFile("Invalid value [Connection-Logs::] expecting file path")
						else:
							try:
								a = open(l, "a", encoding="UTF-8")
								a.close()
								del a
							except FileNotFoundError or PermissionError:
								gbl_connection.addLog(f"[MySQLConnectionOptions] tried to load the file {config}", False,
													  "Invalid value [Connectiong-Logs::] unreachable file", 1433)
								raise self.InvalidConfigurationsFile("Invalid file path [Connection-Logs::] unreachable file")
					else:
						gbl_connection.addLog(f"[MySQLConnectionOptions] tried to load the file {config}", False,
											  f"Invalid field {i} [General::]", 1433)
						raise self.InvalidConfigurationsFile(f"Invalid field '{i}' [General::]")
				del loaded
		except FileNotFoundError or PermissionError:
			gbl_connection.addLog(f"[MySQLConnectionOptions] tried to load the file {config}", False, "Unreachable file", 1433)
			raise self.InvalidConfigurationsFile("Unreachable file")
		except JSONDecodeError:
			gbl_connection.addLog(f"[MySQLConnectionOptions] tried to load the file {config}", False,
								  "Invalid JSON content", 1433)
			raise self.InvalidConfigurationsFile("Invalid JSON content.")
		except KeyError:
			gbl_connection.addLog(f"[MySQLConnectionOptions] tried to load the file {config}", False,
								  "Structure error", 1433)
			raise self.InvalidConfigurationsFile("Structure error, please check the fields")
		return True

	def load_config(self, config: AnyStr):
		"""
		Loads a configurations file to the class attributes.
		:param config: The configurations file to load.
		:except FileError: If there's a configurations file loaded already
		"""
		if self.got_file:
			gbl_connection.addLog("[MySQLConnectionOptions] Tried to load file", False,
								  "There's a configurations file loaded already", 1432)
			raise self.FileError("There's a configurations file loaded already")
		if self.ckconfig(config):
			with open(config, "r", encoding="UTF-8") as conf:
				self.file_load = config
				self.document = loads(conf.read())
				self.got_file = True
			gbl_connection.addLog(f"[MySQLConnectionsOptions] Loaded file {config}")

	def __init__(self, config: AnyStr = None):
		"""
		That method loads the MySQL database configurations file.
		:param config: The configurations file to load, if None then will set up the attributes with default values
		"""
		if config is not None: self.load_config(config)
		else:
			self.document = {}
			self.file_load = ""
			self.got_file = False
			gbl_connection.addLog("[MySQLConnectionOptions] Started empty class")

	def commit(self):
		"""
		Writes all the changes at the configurations content <document attr> to the original file <file_load attr>
		:except FileError: If there's no configurations file loaded yet;
		"""
		if not self.got_file:
			gbl_connection.addLog("[MySQLConnectionOptions] Tried to load internal file", False,
								  "No configurations file loaded", 1432)
			raise self.FileError("There's no configurations file loaded yet!")
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
			gbl_connection.addLog(f"[MySQLConnectionOptions] Dumped data at file {self.file_load}")
			del dumped

	def unload(self):
		"""
		That method unset the class attributes, making it ready for load another configurations file or just close't
		before deleting the class object/instance
		:except FileError: If there's no configurations file loaded yet
		"""
		if not self.got_file:
			gbl_connection.addLog("[MySQLConnectionOptions] Tried to load internal file", False,
								  "No configurations file loaded", 1432)
			raise self.FileError("There's no configurations file loaded yet")
		tmp_log = self.file_load
		self.commit()
		self.document = {}
		self.file_load = ""
		self.got_file = False
		gbl_connection.addLog(f"[MySQLConnectionOptions Unloaded file {tmp_log}")
		del tmp_log

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
	:cvar gen_cl: The client configurations

	:type connection: MySQLConnection
	:type con_data: MySQLConnectionOptions
	:type got_conn: bool
	:type gen_cl: ClientDataAuto
	"""
	connection: MySQLConnection
	con_data: MySQLConnectionOptions
	got_conn: bool = False
	gen_cl: ClientDataAuto

	class RootRequiredError(PermissionError):
		"""
		Exception raised when the MySQL client try to do a action that requires a root client, actions like changing self
		data or self signatures data. Also access some data like the hashed password or the signature pure hash or other
		data such as the ID.
		"""
		ERR_CODE = 1502

	class MySQLConnectionError(Exception):
		"""
		Exception raised when the class try to load a MySQL client and connection data, but there's another client created
		or configured already as a attribute. Also raised when the class try to access the client and/or the connection
		data but there's no connection configured or loaded.
		"""
		ERR_CODE = 1503

	def __str__(self) -> str: return "[MySQLExternalConnection]"

	def add_log(self, action: str, success: bool = True):
		"""
		That method writes every action the client do in the default connection logs file, the file path is defined by
		the client configurations file.
		:param action: The action that the client did
		:param success: If it was successfully executed
		:except MySQLConnectionError: If there's no client or connection options loaded.
		"""
		if not self.got_conn:
			raise self.MySQLConnectionError("There's no connection or connections configurations file loaded!")
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
	
		:except MySQLConnectionError: If the class already got a connection
		"""
		if self.got_conn:
			gbl_connection.addLog(f"[{self.__str__}] Tried to load internal connection", False,
								  "Not connected yet.", 1432)
			raise self.MySQLConnectionError("There's a MySQL connection already configured!")

		self.con_data = config
		self.connection = connect(
			host=self.con_data.document['General']['Primary-Host'],
			port=int(self.con_data.document['General']['Default-Port']),
			user=usr_access,
			db="LPGP_WEB"
		)
		self.got_conn = True
		self.gen_cl = ClientDataAuto(
			host=self.con_data.document['General']['Primary-Host'],
			usr=usr_access,
			passwd=passwd_access,
			db="LPGP_WEB",
			port=self.con_data.document['General']['Default-Port']
		)
		gbl_connection.addLog(f"{self.__str__} STARTED CONNECTION WITH {self.con_data.document['General']['Primary-Host']}:{self.con_data.document['General']['Default-Port']}")

	def disconnect(self):
		"""
		That class unset the class attributes. Used to generate another connection but with the same class object/instance.
		:except MySQLConnectionError: If the class isn't connected
		"""
		if not self.got_conn:
			gbl_connection.addLog("[MySQLConnectionOptions] Tried to load internal file", False,
								  "No configurations file loaded", 1432)
			raise self.MySQLConnectionError("The class must be connected!")
		self.connection.commit()
		self.connection.close()
		tmp_host, tmp_port = self.con_data.document['General']['Primary-Host'], self.con_data.document['General']['Default-Port']
		self.con_data.unload()
		self.got_conn = False
		gbl_connection.addLog(f"{self.__str__} DISCONNECTED FROM {tmp_host}:{tmp_port}")

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
		ERR_CODE = 5202

	def get_info(self) -> tuple:
		"""
		That method return the owner info, such as him name, email, password, if it was checked or not.
		The method don't require root account.
		:except MySQLConnectionError: If there's no database connected.
		:return: A tuple with it data
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"[{self.__str__()}] Tried to load connection", False,
								  "Not connected", 1432)
			raise self.MySQLConnectionError("There's no database connected")
		with self.connection.cursor() as cursor:
			rt = cursor.execute(f"SELECT nm_proprietary, vl_email, vl_password, dt_creation FROM tb_proprietaries WHERE cd_proprietary = {self.gen_cl.propId};")
			raw = cursor.fetchone()
			return tuple(raw) + tuple([self.gen_cl.mode])

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
		:except MySQLConnectionError: If the class didn't got a database connected
		:except RootRequiredError: If the client isn't a root client to do that action
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"[{self.__str__()}] Tried to access connection", False,
								  "Not connected", 1432)
			raise self.MySQLConnectionError("There's no database connected")
		if self.gen_cl.mode == 0:
			gbl_connection.addLog(f"{self.__str__()} Tried to change name", False, "Permission denied", 404)
			raise self.RootRequiredError("The client don't have permission to do that!")
		with self.connection.cursor() as cursor:
			rt = cursor.execute(f"UPDATE tb_proprietaries SET nm_proprietary = \"{new_name}\" WHERE cd_proprietary = {self.gen_cl.propId};")
			gbl_connection.addLog(f"{self.__str__()} Changed owner name to: {new_name}")
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
		:except MySQLConnectionError: If the client isn't connected
		:except RootRequiredError: If the client isn't a root client
		:except InvalidEmail: If the email address isn't valid
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"[{self.__str__()}] Tried to access connection", False,
								  "Not connected", 1432)
			raise self.MySQLConnectionError("The class isn't connected!")
		if self.gen_cl.mode == 0:
			gbl_connection.addLog(f"{self.__str__()} Tried to change name", False, "Permission denied", 404)
			raise self.RootRequiredError("The root permission is required for that action!")
		if not self.ck_email(new_email):
			gbl_connection.addLog(f"{self.__str__()} Tried to change owner email address", False, "Invalid Email", 5202)
			raise self.InvalidEmail("Invalid e-mail address! Please verify if it have '@' and '.com'")
		with self.connection.cursor() as cursor:
			rq = cursor.execute(f"UPDATE tb_proprietaries SET vl_email = \"{new_email}\" WHERE cd_proprietary = {self.gen_cl.propId};")
			gbl_connection.addLog(f"{self.__str__()} Changed owner e-mail address to: {new_email}")
			del rq

	def ch_passwd(self, new_passwd: str, encoded: bool = False):
		"""
		That method changes the owner password.
		:param new_passwd: The new password to set
		:param encoded: If the password is encrypted, if not it'll encrypt it
		:except MySQLConnectionError: If the class ins't connected to the database.
		:except RootRequiredError: If the client isn't a root client
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"[{self.__str__()}] Tried to access connection", False,
								  "Not connected", 1432)
			raise self.MySQLConnectionError("The class isn't connected!")
		if self.gen_cl.mode == 0:
			gbl_connection.addLog(f"{self.__str__()} Tried to change name", False, "Permission denied", 404)
			raise self.RootRequiredError("The root permission is required for that action!")
		with self.connection.cursor() as cursor:
			passwd_new = b64encode(new_passwd) if not encoded else new_passwd
			rt = cursor.execute(f"UPDATE tb_proprietaries SET vl_password = \"{passwd_new}\" WHERE cd_proprietary = {self.gen_cl.propId}")
			gbl_connection.addLog(f"{self.__str__()} Changed owner password")
			del rt

	def __str__(self) -> str: return "[MySQLAccountManager]"


class MySQLOwnerHistory(MySQLExternalConnection):
	"""
	That class manages the client owner signature check history. That management is just add and list the history records
	"""

	class ParameterLogicError(Exception):
		"""
		Exception raised when illogical parameters are received from a method, maybe a code different then 0 to a successful
		action.
		"""
		ERR_CODE = 1012

	def __str__(self) -> str: return "[MySQLOwnerHistory]"

	def add_record(self, signature_ref: int, valid: bool = True, code: int = 0, dt_: str = strftime("%Y-%m-%d %H:%M:%S")):
		"""
		That method add a new history record to the owner history table. That method is normally used at the end of each
		signature verification.
		:param signature_ref: The signature checked ID
		:param valid: If the operation was successful, in this case the code have to be 0.
		:param code: The error code. In no errors case, then it'll be 0
		:param dt_: The date to set at the database
		:except MySQLConnectionError: If the client isn't connected yet
		:except ParameterLogicalError: If there're discrepancies between the valid and the code parameter. For example
										the action was a success but the code isn't 0
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"{self.__str__()} Tried to access connection", False, "Not connected", 1432)
			raise self.MySQLConnectionError("The client isn't connected!")
		if (valid and code != 0) or (not valid and code == 0):
			gbl_connection.addLog(f"{self.__str__()} Tried to add record", False, f"Programming Logic error vl: {valid} code:{code}")
			raise self.ParameterLogicError("There're programming logical errors with the parameters ::valid and ::code received")
		with self.connection.cursor() as cursor:
			owner_ref = self.gen_cl.propId
			val = 1 if valid else 0
			crs = cursor.execute(f"INSERT INTO tb_signatures_prop_h (id_prop, id_signature, vl_code, vl_valid, dt_reg) VALUES ({owner_ref}, {signature_ref}, {code}, {val}, {dt_});")
			gbl_connection.addLog(f"{self.__str__()} Added record [{signature_ref, valid, code, dt_}]")
			del crs

	def get_records(self) -> tuple:
		"""
		That method returns all the records of the owner history.
		:except MySQLConnectionError: If the client isn't connected
		:except RootRequiredError: If the client doesn't have the root permission
		:return: A tuple with the owner history records
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"{self.__str__()} Tried to access connection", False, "Not connected", 1432)
			raise self.MySQLConnectionError("The client isn't connected")
		if self.gen_cl.mode == 0:
			gbl_connection.addLog(f"{self.__str__()} Tried to access the history records", False, "Permission denied", 1052)
			raise self.RootRequiredError("The client must be root to do that action!")
		with self.connection.cursor() as cursor:
			c = cursor.execute(f"SELECT * FROM tb_signatures_prop_h WHERE id_prop = {self.gen_cl.propId};")
			gbl_connection.addLog(f"{self.__str__()} Accessed owner history")
			return cursor.fetchall() if c > 0 else None


class MySQLSignaturesManager(MySQLExternalConnection):
	"""
	That class represents the signatures files operations and the owner signatures. That class creates, authenticates and
	manages the signatures files, also managing the owner signatures.
	:cvar algos: The options to decoding and encoding.
	:cvar delimiter: The root encryption delimiter
	"""
	algos: tuple = ("md5", 'sha1', 'sha256')
	delimiter: str = "/"

	class AccountError(Exception):
		"""
		Exception raised when the owner isn't a proprietary and try to access data or signatures that doesn't bellow to
		him
		"""
		ERR_CODE = 1455

	class AlgoError(Exception):
		"""
		Exception raised when the client can't find the referred algo.
		"""
		ERR_CODE = 1983

	class EncryptionError(Exception):
		"""
		Exception raised when the client try to authenticate a signature but the referred algo id don't exist.
		"""
		ERR_CODE = 9872

	class AuthenticationError(Exception):
		"""
		Exception raised when the class try to authenticate a signatures file, but the file isn't valid.
		"""
		ERR_CODE = 1092

	class DecodingError(Exception):
		"""
		Exception raised when the class try to decrypt a LPGP file but there're errors with the file encryption.
		"""
		ERR_CODE = 1093

	class SignatureNotFound(Exception):
		"""
		Exception raised when the class try to access a signature data record, using a primary key reference, but it
		doesn't exist
		"""
		ERR_CODE = 1440

	def ck_sigex(self, ref: int) -> bool:
		"""
		That method check if a signature reference exists.
		:param ref: The primary key reference of the signature record.
		:except MySQLConnectionError: If the client isn't connected
		:return: If the signature reference exists.
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"{self.__str__()} Tried to access connection data", False, "Not connected", 1432)
			raise self.MySQLConnectionError("The client isn't connected")
		with self.connection.cursor() as cursor:
			rr = cursor.execute(f"SELECT * FROM tb_signatures WHERE cd_signature = {ref};")
			return rr > 0

	def ck_own(self, ref: int) -> bool:
		"""
		That method check if the client owner have the referred signature.
		:param ref: The signature primary key reference
		:except MySQLConnectionError: If the client isn't connected to a MySQL database
		:except SignatureNotFound: If the signature referenced doesn't exist
		:return: True if the client owner also own the signature referred, False if not
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"{self.__str__()} Tried to access connection data", False, "Not connected", 1432)
			raise self.MySQLConnectionError("The client isn't connected!")
		if not self.ck_sigex(ref):
			gbl_connection.addLog(f"{self.__str__()} Access required to signature #{ref}", False, f"#{ref} Not found", 1440)
			raise self.SignatureNotFound(f"Can't find signature #{ref}")
		with self.connection.cursor() as cursor:
			rr = cursor.execute(f"SELECT id_proprietary FROM tb_signatures WHERE cd_signature = {ref};")
			id_or = cursor.fetchone()[0]
			del rr
		return id_or == self.gen_cl.propId

	def decode_root(self, code: str) -> dict:
		"""
		That method decodes the original encryption of the, and parsing the JSON decoded content.
		:param code: The file content or just content to decode
		:except DecodingError: If there were troubles decoding the content.
		:return: The json parsed content.
		"""
		try:
			exp = code.split(self.delimiter)
			dt = [chr(int(x)) for x in exp]
			json_to = "".join(dt)
			return loads(json_to, encoding="UTF-8")
		except JSONDecodeError as e:
			raise self.DecodingError("ERROR >> " + e.msg)

	@staticmethod
	def encode_root(data: str) -> str:
		"""
		That method encodes a string with signature data.
		:param data: The string with the signature data.
		:return: The encoded signature data.
		"""
		epl = data.split("")
		dumped = ""
		for i in epl: dumped += ord(i)
		del epl
		return dumped

	def encode_hash(self, data: str, hash_id: int) -> str:
		"""
		That method uses the hashlib to encode data with a hash id, normally received from the signatures
		database.
		:param data: The content to encode.
		:param hash_id: The hash id to encode.
		:except EncryptionError: If the hash id isn't valid for the class.
		:return: The hash encoded content.
		"""
		try:
			tt = self.algos[hash_id]
			del tt
		except IndexError:
			gbl_connection.addLog(f"{self.__str__()} Tried to generate hash", False, f"Code Error: #{hash_id} not found", 9872)
			raise self.EncryptionError(f"The code {hash_id} isn't valid")
		if hash_id == 0:
			md5 = hashlib.md5()
			md5.update(bytes(data, encoding="UTF-8"))
			gbl_connection.addLog(f"{self.__str__()} Generated MD5 hash")
			return md5.hexdigest()
		elif hash_id == 1:
			sha1 = hashlib.sha1()
			sha1.update(bytes(data, encoding="UTF-8"))
			gbl_connection.addLog(f"{self.__str__()} Generated SHA1 hash")
			return sha1.hexdigest()
		elif hash_id == 2:
			sha256 = hashlib.sha256()
			sha256.update(bytes(data, encoding="UTF-8"))
			gbl_connection.addLog(f"{self.__str__()} Generated SHA256 hash")
			return sha256.hexdigest()
		else:
			gbl_connection.addLog(f"{self.__str__()} Tried to generate hash", False, f"Code Error: #{hash_id} not found", 9872)
			raise self.EncryptionError(f"Code not found {hash_id}")

	@staticmethod
	def gen_filenm(path: AnyStr) -> AnyStr:
		"""
		That method generate a signature file name in a specific path. Verifying if the file exists or not.
		:param path: The path to check the signatures files existences.
		:return: The signature file name.
		"""
		while True:
			rec_num = 0
			nm = "signature-file-" + str(rec_num)
			if nm in listdir(path):
				rec_num+=1
				continue
			else: break
		return nm

	def authenticate_file(self, file_path: AnyStr, auto_raise: bool = True) -> tuple:
		"""
		That method checks if a signature file is valid or not. That method will decode and check the signature data at
		the file
		:param file_path: The .lpgp file to authenticate
		:param auto_raise: If the method will raise the AuthenticationError exception automatically
		:except MySQLConnectionError: If the client isn't connected yet
		:except AuthenticationError: If the signature file can't be decoded or is invalid
		:return: If the file is a valid signature or not, and the error message, if no errors will return the signature data
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"{self.__str__()} Tried to access connection", False, "Not connected", 1432)
			raise self.MySQLConnectionError("The client isn't connected")
		with open(file_path, "r", encoding="UTF-8") as signature:
			dt_sig = self.decode_root(signature.read())
			with self.connection.cursor() as cursor:
				if not self.ck_sigex(int(dt_sig['ID'])):
					gbl_connection.addLog(f"{self.__str__()} Authenticated signature {file_path} -> Invalid: ID don't exists.")
					if auto_raise:
						raise self.AuthenticationError("Invalid Signature -> The reference 'ID' doesn't exist")
					else: return False, "ID reference doesn't exist"
				rr = cursor.execute(f"SELECT vl_password FROM tb_signatures WHERE cd_signature = {dt_sig['ID']};")
				if cursor.fetchone()[0] != dt_sig['Signature']:
					gbl_connection.addLog(f"{self.__str__()} Authenticated signature {file_path} -> Invalid: Token error")
					if auto_raise: raise self.AuthenticationError("Invalid Signature -> Token invalid")
					else: return False, "Invalid token"
				rr2 = cursor.execute(f"SELECT cd_proprietary FROM tb_proprietaries WHERE nm_proprietary = \"{dt_sig['Proprietary']}\";")
				if rr2 < 0:
					gbl_connection.addLog(f"{self.__str__()} Authenticated signature {file_path} -> Invalid: Proprietary not found")
					if auto_raise: raise self.AuthenticationError("Invalid Signature -> Proprietary not found!")
					else: return False, "Proprietary not found"
				del rr, rr2
		gbl_connection.addLog(f"{self.__str__()} Authenticated signature {file_path} ->  Valid")
		return True, dt_sig

	# Root Actions
	##################################################################################

	def create_signature_file(self, path: AnyStr, ref: int):
		"""
		That method generate a signature file to a path.
		:param path: The path to create the signature file.
		:param ref: The primary key signature reference
		:except MySQLConnectionError: If the client isn't connected
		:except AccountError: If the owner account type isn't proprietary
		:except RootRequiredError: If the client isn't a root client
		:except SignatureNotFound: If the reference doesn't exist or if the owner don't own the referred signature
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"{self.__str__()} Tried to access connection data", False, "Not connected", 1432)
			raise self.MySQLConnectionError("The client isn't connected!")
		if self.gen_cl.mode == 0:
			gbl_connection.addLog(f"{self.__str__()} Tried to create signature file at {path}, sg: {ref}", False,
								"Root permission error", 1052)
			raise self.RootRequiredError("The client must be root to do that action")
		if not self.ck_sigex(ref):
			gbl_connection.addLog(f"{self.__str__()} Tried to create signature file at {path}, sg: {ref}", False,
								  f"Signature #{ref} don't exist", 1440)
			raise self.SignatureNotFound(f"The client can't find the signature #{ref}")
		if not self.ck_own(ref):
			gbl_connection.addLog(f"{self.__str__()} Tried to create signature file at {path}, sg: {ref}", False,
								  f"Signature #{ref} isn't onwers property", 1440)
			raise self.SignatureNotFound(f"The client can't find the signature #{ref}")
		nm_file = self.gen_filenm(path)
		with self.connection.cursor() as cursor:
			rr = cursor.execute(f"SELECT prp.nm_proprietary, sg.vl_password FROM tb_signatures AS sg INNER JOIN "
								f"tb_proprietaries AS prp ON prp.cd_proprietary = sg.id_proprietary WHERE "
								f"sg.cd_signature = {ref};")
			dt_now = strftime("%Y-%m-%d %H:%M:%S")
			json_data = {
				"Date-Creation": dt_now,
				"Proprietary": cursor.fetchone()[0],
				"ID": ref,
				"Signature": cursor.fetchone()[1]
			}
			content = self.encode_root(dumps(json_data))
			path_file = path + "/" if "windows" not in platform else "\\" + nm_file
			with open(path_file, "w+", encoding="utf-8") as signature:
				signature.write(content)
			del rr
			gbl_connection.addLog(f"{self.__str__()} Generated signature file {path_file}")

	def getLastSignatureRef(self) -> int:
		"""
		That method reads a query with all the signatures in the database and return the last signature created.
		:raises MySQLConnectionError: if the class isn't connected yet
		:return: The last signature primary key reference
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"{self.__str__()} Tried to access connection data", False, "Not connected", 1432)
			raise self.MySQLConnectionError("The client isn't connected")
		with self.connection.cursor() as cursor:
			qr_rows = cursor.execute("SELECT cd_signature FROM tb_signatures ORDER BY dt_creation;")
			if qr_rows == 0: return -1
			else:
				all_sig = cursor.fetchall()
				return int(all_sig[-1][0])

	def add_sig(self, code: int, password: str):
		"""
		That method creates a signature in the owner name.
		:param code: The algo index, a option to the encoding.
		:param password: The main word to create the signature.
		:except MySQLConnectionError: If the client isn't connected to a MySQL database.
		:except RootRequiredError: If the client don't have root permissions
		:except AccountError: If the owner is a normal user instead a proprietary
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"{self.__str__()} Tried to access connection data", False, "Not connected", 1432)
			raise self.MySQLConnectionError("The client isn't connected!")
		if self.gen_cl.mode == 0:
			gbl_connection.addLog(f"{self.__str__()} Tried to create a new signature", False, "Root permission error", 1052)
			raise self.RootRequiredError("The client need root permissions!")
		if code > len(self.algos) or code < 0:
			gbl_connection.addLog(f"{self.__str__()} Tried to create a new signature", False, f"Invalid code: {code}", 404)
			raise IndexError("Invalid signature code!")
		with self.connection.cursor() as cursor:
			_pass = self.encode_hash(password, code)
			rr = cursor.execute(f"INSERT INTO tb_signatures (vl_code, vl_password, id_proprietary) "
								f"VALUES ({code}, \"{_pass}\", {self.gen_cl.propId});")
			del rr
			del _pass
			generated_sig = self.getLastSignatureRef()  # Just for the logs
			gbl_connection.addLog(f"{self.__str__()} Created signature #{generated_sig}")
			del generated_sig

	def rm_sig(self, ref: int):
		"""
		That method deletes a signature data record from the owner, in other words it excludes a signature that owns
		to the client owner.
		:param ref: The signature referenced
		:except MySQLConnectionError: If the client isn't connected to a database
		:except RootRequiredError: If the client don't have root permissions
		:except SignatureNotFound: If the signature reference doesn't exist or the client owner don't own it.
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"{self.__str__()} Tried to access connection data", False, "Not connected", 1432)
			raise self.MySQLConnectionError("The client isn't connected!")
		if self.gen_cl.mode == 0:
			gbl_connection.addLog(f"{self.__str__()} Tried to remove signature #{ref}", False, "Root Permission denied", 1052)
			raise self.RootRequiredError("The client need root permissions")
		if not self.ck_sigex(ref) or not self.ck_own(ref):
			gbl_connection.addLog(f"{self.__str__()} Tried to remove signature #{ref}", False, "Signature don't exists", 1404)
			raise self.SignatureNotFound(f"The signature #{ref} doesn't exist or you don't own it.")
		with self.connection.cursor() as cursor:
			rr = cursor.execute(f"DELETE FROM tb_signatures WHERE cd_signature = {ref};")
			del rr
			gbl_connection.addLog(f"{self.__str__()} Removed signature #{ref}")

	def ch_sig_code(self, ref: int, new_code: int, pas_conf: str):
		"""
		That method changes the signature algo index reference.
		:param ref: The primary key of the referred signature to update
		:param new_code: The new hash index using to the process.
		:param pas_conf: The signature password confirmation to re-encode
		:except MySQLConnectionError: If the client isn't connected yet
		:except RootRequiredError: If the client don't have a root permission
		:except SignatureNotFound: If the referred signature doesn't exist.
		:except EncryptionError: If the hash index (new_code) isn't valid
		:except AuthenticationError: If the password confirmed received isn't the same.
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"{self.__str__()} Tried to access connection data", False, "Not connected", 1432)
			raise self.MySQLConnectionError("The client isn't connected!")
		if self.gen_cl.mode == 0:
			gbl_connection.addLog(f"{self.__str__()} Tried to change signature code #{ref} -> {new_code}", False,
								  "Root Permission Denied", 1052)
			raise self.RootRequiredError("The client need root permission to do that action!")
		if not self.ck_sigex(ref) or not self.ck_own(ref):
			gbl_connection.addLog(f"{self.__str__()} Tried to change signature code #{ref} -> {new_code}", False,
								  f"Signature #{ref} don't exist", 1404)
			raise self.SignatureNotFound(f"The referred signature #{ref} doesn't exist or you don't own it.")
		if new_code < 0 or new_code > len(self.algos):
			gbl_connection.addLog(f"{self.__str__()} Tried to change signautre code #{ref} -> {new_code}", False,
								  f"Invalid Code: {new_code}", 9872)
			raise self.EncryptionError(f"The numeric code reference {new_code} isn't valid")
		with self.connection.cursor() as cursor:
			rr = cursor.execute(f"SELECT vl_code, vl_password FROM tb_signatures WHERE cd_signature = {ref};")
			or_code = int(cursor.fetchone()[0])
			auth_hash = self.encode_hash(pas_conf, or_code)
			if auth_hash !=  cursor.fetchone()[1]:
				gbl_connection.addLog(f"{self.__str__()} Tried to change signature code #{ref} -> {new_code}", False,
									  f"Password error", 1092)
				raise self.AuthenticationError("The password doesn't matches")
			del rr
			hashed = self.encode_hash(cursor.fetchone()[1], new_code)
			rr = cursor.execute(f"UPDATE tb_signatures SET vl_code = {new_code}, vl_password = \"{hashed}\" WHERE cd_signature = {ref};")
			del rr, hashed
			gbl_connection.addLog(f"{self.__str__()} Changed signature code #{ref} -> {new_code}")

	def ch_sig_pas(self, ref: int, new_pass: str):
		"""
		That method changes the signature main password, that word is encoded to be the pure signature.
		:param ref: The signature referenced to change the password.
		:param new_pass: The new password value.
		:except MySQLConnectionError: If the client isn't connected
		:except SignatureNotFound: If the client owner doesn't own the signature or the signature doesn't exist.
		:except RootRequiredError: If the client isn't a root client
		:except ValueError: If the new password have less then 7 characters
		"""
		if not self.got_conn:
			gbl_connection.addLog(f"{self.__str__()} Tried to change signature password #{ref}", False, "Not connected", 1432)
			raise self.MySQLConnectionError("The client isn't connected")
		if self.gen_cl.mode == 0:
			gbl_connection.addLog(f"{self.__str__()} Tried to change signature password #{ref}", False, "Root permission denied", 1052)
			raise self.RootRequiredError("The client need root permission")
		if not self.ck_own(ref) or not self.ck_sigex(ref):
			gbl_connection.addLog(f"{self.__str__()} Tried to change signature password #{ref}", False, "Signature not found", 1404)
			raise self.SignatureNotFound(f"The signature #{ref} doesn't exist or you don't own it")
		if len(new_pass) < 7:
			gbl_connection.addLog(f"{self.__str__()} Tried to change signature password #{ref}", False, "Invalid password: less then 7 chars", 506)
			raise ValueError("The passwords must have more then 7 characters")
		with self.connection.cursor() as cursor:
			rr = cursor.execute(f"SELECT vl_code FROM tb_signatures WHERE cd_signature = {ref};")
			hashed = self.encode_hash(new_pass, cursor.fetchone()[0])
			del rr
			rr = cursor.execute(f"UPDATE tb_signatures SET vl_password = \"{hashed}\" WHERE cd_signature = {ref}")
			del hashed, rr
			gbl_connection.addLog(f"{self.__str__()} Changed signature #{ref} password")







