import psycopg2
import argparse
import requests
from progress.bar import IncrementalBar
import xml.etree.ElementTree as et
from utils import InvalidSourceException, wordToIntId
from config import load_env_config

config = load_env_config()
conn = psycopg2.connect(**config)
cur = conn.cursor()
dbname = conn.info.dbname
print("Connection established to database: " + dbname)

PER_COMMIT = 2500

def create_word_table(source):
	print("Parsing words at source " + source)
	load_words_bar = IncrementalBar("Loading words into database...", max=370104)
	with open(source, "r") as fread:
		words = [word.rstrip("\n") for word in fread]

	# Database gives generated id and default instances value
	insert_word_command = """
		INSERT INTO words(word)
			VALUES(%s)
	"""

	for word in words:
		try:
			cur.execute(insert_word_command, (word, ))
		except (Exception, psycopg2.DatabaseError) as error:
			print(error)
		load_words_bar.next()
		if load_words_bar.index % PER_COMMIT == 0:
			conn.commit()


def read_text(source):
	pass


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog="flexicon"
	)
	parser.add_argument("-w", "--wordlist-source")
	parser.add_argument("-r", "--wikipedia-source")
	cmdargs = parser.parse_args()
	if cmdargs.wordlist_source == None:
		raise InvalidSourceException("No wordlist source source given")
	if cmdargs.wikipedia_source == None:
		raise InvalidSourceException("No wikipedia source given")

	create_word_table(cmdargs.wordlist_source)
	read_text(cmdargs.wikipedia_source)

conn.close()
print("Connection closed from database: " + dbname)