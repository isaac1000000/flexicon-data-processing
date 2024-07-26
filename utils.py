from hashlib import md5

class InvalidCredentialsException(Exception):
	pass

class InvalidSourceException(Exception):
	pass

def wordToIntId(word):
	"""Replicates the database's default string to id hash function.

	Uses md5 hash on the word then truncates to 64 bits to fit the
	Postgres BIGINT type size convention. Collisions are possible but
	rare, so particularly nasty bugs might be related.

	Args:
		word - the word to be converted to an id
	Returns:
		An integer value representing the word's unique hashed id
	"""
	bytesobj = md5(word.encode()).digest()
	return int.from_bytes(bytesobj[:8], byteorder="big", signed=True)

if __name__ == "__main__":
	print(wordToIntId("invisible"))
