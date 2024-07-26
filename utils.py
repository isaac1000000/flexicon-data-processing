from hashlib import md5

class InvalidCredentialsException(Exception):
	pass

class InvalidSourceException(Exception):
	pass

def wordToIntId(word):
	# Word ids are stored in the database as 8-byte (truncated) md5 hashes.
	# Postgres auto-generates the id, but it might be useful to have a way
	# To retrieve a word with the key
	bytesobj = md5(word.encode()).digest()
	return int.from_bytes(bytesobj[:8], byteorder="big")
