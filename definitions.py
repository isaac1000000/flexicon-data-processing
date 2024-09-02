"""This is the code that I used to add definitions to all my words in flexicon. 

If you'd like to recreate, you'll have to create a .env file with HOST, 
DATABASE, USER, and PASSWORD tokens for your Postgres database, then run 

python definitions.py -w <wordlist-source> -d <dictionary-source>

Where <wordlist> is a plaintext file with line-separated words and <dictionary-source>
is a plaintext file containing stemmed words (grammatical inflections removed) and
their definitions separated by a double-space.

You can download the necessary wordlist at https://github.com/dwyl/english-words 
(I used the alpha version for simplicity) and the dictionary I used at
https://github.com/sujithps/Dictionary.

You can view the source code for my entire project at my GitHub 
https://github.com/stars/isaac1000000/lists/flexicon
"""


import psycopg2
import requests
import argparse
import json
import re
from progress.bar import IncrementalBar
from utils import wordToIntId
from nltk.stem.porter import PorterStemmer
from config import load_env_config

config = load_env_config()
conn = psycopg2.connect(**config)
cur = conn.cursor()
dbname = conn.info.dbname
print("Connection established to database: " + dbname)

PER_COMMIT = 2500
WORD_COUNT = 370104

stemmer = PorterStemmer()

DICTIONARY_PARSE_SUBS = [
	(";", " -"),
	(r"\[.*?\]", "")
]

dictionary = {} # Will be filled via the dictionary source provided via command line

def get_from_dictionary(word):
	"""Get a single word's definition from the dictionary source provided.

	Args:
		word - The unstemmed word to search the dictionary for.
	"""
	stemmed_word = stemmer.stem(word).lower()

	return dictionary.get(stemmed_word, None)


def add_definitions_to_word_table(wordlist_source, dictionary_source):
	global dictionary
	"""Add definitions for all words from given wordlist source into the word database.

	Args:
		wordlist_source - The source location for the wordlist. The list should be
			plaintext and separated by linebreaks.
		dictionary_source - The source location for the dictionary. The list should be
			stemmed, plaintext and separated by linebreaks.
	"""
	print("Adding definitions to database from " + dictionary_source)
	load_defs_bar = IncrementalBar("Loading words into database...", max=WORD_COUNT)
	with open(wordlist_source, "r") as fread:
		words = [word.rstrip("\n") for word in fread]

	with open(dictionary_source, "r", encoding="utf-8") as fread:
		for line in fread:
			if line == "\n":
				continue
			parts = line.split("\x7f")[0] # Removes unnecessary content
			parts = parts.split("  ") # Splits word and definition
			if len(parts) == 1:
				continue
			for old, new in DICTIONARY_PARSE_SUBS:
				parts[1] = re.sub(old, new, parts[1])
			dictionary[stemmer.stem(parts[0]).lower()] = parts[1].strip()

	# SQL command to insert a single definition into the database.
	add_def_command = """
		UPDATE words
			SET definition = %s
		WHERE id = %s
	"""

	for word in words:
		try:
			definition = get_from_dictionary(word)
			if definition != None:
				cur.execute(add_def_command, (definition, wordToIntId(word)))
		except (Exception, psycopg2.DatabaseError) as error:
			print(error)
		load_defs_bar.next()
		if load_defs_bar.index % PER_COMMIT == 0:
			conn.commit()

	conn.commit()
	load_defs_bar.finish()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog="flexicon"
	)
	parser.add_argument("-w", "--wordlist-source")
	parser.add_argument("-d", "--dictionary-source")
	cmdargs = parser.parse_args()
	if cmdargs.wordlist_source is not None and cmdargs.dictionary_source is not None:
		add_definitions_to_word_table(cmdargs.wordlist_source, cmdargs.dictionary_source)

conn.close()
print("Connection closed from database: " + dbname)