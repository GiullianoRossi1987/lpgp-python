# coding = utf-8
# using namespace std
from json import loads, JSONDecodeError
from typing import AnyStr
from pymysql.connections import Connection


class ClientData(object):  # deprecated
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
				elif type(ld['ClientName']) is str or len(ld['ClientName']) <= 0:
					raise self.InvalidFile("Invalid value at the 'ClientName'")
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

	@property
	def name(self) -> str:
		"""
		That method represents the client name field on the client configurations file.
		:return: The client name
		"""
		if not self.got_file: raise self.FileError("There's no configurations file loaded. Can't access the properties")
		else: return self.raw_doc['ClientName']


class ClientDataAuto(object):
	"""
	That new class works getting the client data without a client configurations file, it uses a client
	authentication file to search in the database for a client with the same token as the local client.
	That uses a temporary MySQL database connection, loading the MySQL connection configurations file.

	:cvar con_data: The server connection data, those data are used to connect to the MySQL database
	:cvar got_data: if the class got the connection data, used for the connection
	:cvar client_dt: The client loaded data, that data will have the client id, name, proprietary id
						client token and client permission type
	:cvar DELIMITER: The authentication file delimiter
	:cvar got_client: If the class loaded the client data.

	:type con_data: dict
	:type got_data: bool
	:type client_dt: tuple
	"""

	con_data: dict = {
		"host": None,
		"usr": None,
		'passwd': None,
		"port": None,
		"db": None
	}
	got_data: bool = False
	client_dt: tuple = ()
	got_client: bool = False
	DELIMITER = "/"

	class DataError(Exception):
		"""
		Exception raised when the class don't got the connection data and tries to access them, or when the class
		try to load the connection data without cleaning the attribute.
		"""

	class AuthenticationError(Exception):
		"""
		Exception raised when there was errors decoding the authentication file
		"""

	def load_data(self, host: str, usr: str, passwd: str, port: int = 3306, db: str = "LPGP_WEB"):
		"""
		That method loads the connection data received by parameters
		:param host: The server IP to connect
		:param usr: The server user used for the connection
		:param passwd: The user selected password
		:param port: The MySQL server port, by default it's 3306
		:param db: The MySQL server database using.
		:except DataError: If the class already loaded the connection data
		"""
		if self.got_data: raise self.DataError("The class already loaded the connection data")
		self.con_data = {
			"host": host,
			"usr": usr,
			"passwd": passwd,
			"port": port,
			"db": db
		}
		self.got_data = True

	def clean_data(self):
		"""
		That method remove all the data loaded and set the got_data attribute as False
		:except DataError: If the class don't loaded any data yet
		"""
		if not self.got_data: raise self.DataError("The class don't have any data already!")
		self.con_data = {
			"host": None,
			"usr": None,
			'passwd': None,
			"port": None,
			"db": None
		}
		self.got_data = False

	def __init__(self, host: str = None, usr: str = None, passwd: str = None, port: int = 3306, db: str = "LPGP_WEB"):
		"""
		Starts the class loading the connection data, if any of the parameters are None, then
		:param host: The MySQL server hostname
		:param usr: The user to connect
		:param passwd: The user password
		:param port: The MySQL server port
		:param db: The database to connect.
		"""
		# don't need to check the port and DB params 'cause they have default values.
		if not (host is None or usr is None or passwd is None):
			self.load_data(host, usr, passwd, port, db)
		else: pass  # default values

	def __del__(self):
		"""
		That method is used for a normal and simple garbage collection of the class.
		"""
		if self.got_data: self.clean_data()

	def fetch_auth(self, auth_file: AnyStr = "lib/auth/auth.lpgp"):
		"""
		That method loads the configurations of a client, it will get the client token by the authentication file
		and then will connect to the database and then return the data using a SQL simple query.
		:param auth_file: The authentication file to use.
		:except DataError: If the class don't have the connection data loaded yet.
		:except AuthenticationError: if the file received couldn't be decoded.
		"""
		if not self.got_data: raise self.DataError("There's no connection data to start a connection!")
		# decodes the file
		with open(auth_file, "r", encoding="UTF-8") as to_load:
			sep = str(to_load.read()).split(self.DELIMITER)
			json_con = "".join([chr(int(num)) for num in sep])
			dict_dt = loads(json_con)
			# starts the connection
			connection_tmp = Connection(
				host=self.con_data['host'],
				user=self.con_data['usr'],
				password=self.con_data['passwd'],
				db=self.con_data['db'],
				port=self.con_data['port']
			)
			with connection_tmp.cursor() as cursor:
				sql_query = f"""
SELECT cl.cd_client,
	   cl.nm_client,
	   cl.vl_root,
	   cl.id_proprietary,
	   pr.nm_proprietary
FROM tb_clients AS cl
INNER JOIN tb_proprietaries AS pr
ON pr.cd_proprietary = cl.id_proprietary
WHERE cl.tk_client = "{dict_dt['Token']}";
				"""
				rows = cursor.execute(sql_query)
				if rows <= 0 : raise self.AuthenticationError(f"Can't load the data from the file '{auth_file}'")
				else:
					self.client_dt = cursor.fetchone()
					self.got_client = True
			connection_tmp.close()

	@property
	def name(self) -> str:
		"""
		That property loads the client name of the data loaded. To access that and other properties you must have the
		client data loaded.
		:except DataError: If the instance don't have the client data from the MySQL database.
		:return: The second position of the client_dt attribute
		"""
		if not self.got_data or not self.got_client: raise self.DataError("There's no client data!")
		else: return str(self.client_dt[1])

	@property
	def id(self) -> int:
		"""
		That property loads the client id of the client data loaded. To access that and other properties you must have
		the client data loaded.
		:except DataError: If the instance don't have the client data from the MySQL database.
		:return: The first position of the client_dt attribute
		"""
		if not self.got_client or not self.got_data: raise self.DataError("There's no client data!")
		else: return int(self.client_dt[0])

	@property
	def propId(self) -> int:
		"""
		That property loads the client owner id of the client data loaded. To access that and other properties you must
		have the client data loaded.
		:except DataError: If the instance don't have the client data
		:return: The fourth item of the client_df attribute
		"""
		if not self.got_data or not self.got_client: raise self.DataError("There's no client data")
		else: return int(self.client_dt[3])

	@property
	def propNm(self) -> str:
		"""
		That property loads the client owner name of the client data loaded. To access that and other properties you
		must have loaded the client data.
		:except DataError: If the class don't have the client data
		:return: The last position of the client_dt attribute.
		"""
		if not self.got_client or not self.got_data: raise self.DataError("There's no client data")
		else: return str(self.client_dt[4])

	@property
	def mode(self) -> int:
		"""
		That property loads the client permissions type. To access that and other properties you must have the client
		data loaded.
		:except DataError: If the class don't have the client data.
		:return: The third position of the client_dt attribute
		"""
		if not self.got_data or not self.got_client: raise self.DataError("There's no client data")
		else: return int(self.client_dt[2])
