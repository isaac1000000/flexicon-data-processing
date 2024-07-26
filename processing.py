"""This is the code that I used to generate the database for flexicon. 

If you'd like to recreate, you'll have to create a .env file with HOST, 
DATABASE, USER, and PASSWORD tokens for your Postgres database, then run 

python processing.py -w <wordlist-source> -r <wiki-dir>

Where <wordlist> is a plaintext file with line-separated words and <wiki-dir>
is a directory with a collection of json files generated by or according to
the json scheme in https://github.com/daveshap/PlainTextWikipedia.

You can download the necessary wordlist at https://github.com/dwyl/english-words 
(I used the alpha version for simplicity) and the compressed wiki dumps at 
https://dumps.wikimedia.org/. You'll need to find a way to un-bz2 them yourself.

You can view the source code for the entire project at my GitHub 
https://github.com/isaac1000000/
"""



import psycopg2
import argparse
import requests
import os
import json
import re
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
WORD_COUNT = 370104 # Hardcoding because I've included the txt file
	# and this is only used for the loading bar (not worth computing).
REL_THRESHOLD = 5 # Radius of words considered to be in a relationship.

with open("stopwords.txt", "r") as fr:
	stopwords = [word.rstrip("\n") for word in fr]

def create_word_table(source):
	"""Add all words from given wordlist source into the word database.

	Does not include definitions. The Postgres database initializes the
	instance count to 0 and generates a hashed word id. A replication of this
	conversion from string to id is found in utils.wordToIntId().

	Args:
		source - The source location for the wordlist. The list should be
			plaintext and separated by linebreaks.
	"""
	print("Parsing words at source " + source)
	load_words_bar = IncrementalBar("Loading words into database...", max=370104)
	with open(source, "r") as fread:
		words = [word.rstrip("\n") for word in fread]

	# SQL command to insert a single word into the database.
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

	conn.commit()
	load_words_bar.finish()


def read_text(source_title, source_text_ids, loading_bar):
	"""Parse text and add all relations to rel database.

	Hashes the words to get compound relationship keys. Increments 
	instance counts of base word and creates/increments rel by key.
	Checks both words against stop word list.

	Args:
		source_title - a string containing the title of the article to be parsed
		source_text_ids - a list containing the ids of words to be parsed from the text. 
		loading_bar - the progress bar used by parse_articles
	"""
	loading_bar.suffix = ": " + source_title
	loading_bar.suffix = loading_bar.suffix[:60]

	# SQL command to increment a word's instances count. Postgres automatically
	# returns the number of rows altered, so a response of 0 means it wasn't found
	increment_word_command = """
		UPDATE words
			SET instances = words.instances + 1
		WHERE id = %s;
	"""

	# SQL command to insert a single relation. If the relation already exists,
	# simple increment the instance count
	insert_rel_command = """
		DO'
			BEGIN
				IF (EXISTS(SELECT 1 FROM words WHERE id=%(base_id)s) AND
				EXISTS(SELECT 1 FROM words WHERE id=%(target_id)s)) THEN
					INSERT INTO rels(baseId, targetId)
						VALUES(%(base_id)s, %(target_id)s)
						ON CONFLICT (baseId, targetId) DO UPDATE
							SET instances = rels.instances + 1;
				END IF;
			END;
		' LANGUAGE plpgsql;
	"""

	# Loop through all word id pairs within radius specified by REL_THRESHOLD
	# and execute insert_rel_command with the id pair
	for i in range(len(source_text_ids) - REL_THRESHOLD):
		for j in range(i+1, i+1+REL_THRESHOLD):
			if source_text_ids[i] == source_text_ids[j]:
				continue
			try: 
				cur.execute(increment_word_command, (source_text_ids[i], ))
				cur.execute(insert_rel_command, {"base_id": source_text_ids[i], 
					"target_id": source_text_ids[j]})
			except (Exception, psycopg2.DatabaseError) as error:
				print(error)

	conn.commit()


def parse_articles(source):
	"""Read all articles in a directory and pass them to the parser

	Extracts the plain text from the article then passes it to read_text
	for processing. Also removes all stopwords and otherwise normalizes the text

	Args:
		source - a path to the directory containing the json files
	"""
	filelist = [file for file in os.listdir(source) if file.endswith(".json")]
	total_article_bar = IncrementalBar("Parsing article: ", max=len(filelist))

	for file in filelist:
		with open(os.path.join(source, file), "r", encoding="utf-8") as fr:
			data = json.load(fr)
			title = data["title"]
			text = data["text"]

			text = text.lower() # Make text lowercase.
			text = re.sub(r"\d+", "", text) # Remove numbers from text.
			text = re.sub(r"[^\w\s]", "", text) # Remove punctuation.
			text = text.strip() # Remove whitespace.
			text = text.split() # Split text into list of words.

			text_ids = [wordToIntId(word) for word in text
				if word not in stopwords and len(word) > 1] # Remove stopwords.

			read_text(title, text_ids, total_article_bar)
			total_article_bar.next()

	total_article_bar.finish()



if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog="flexicon"
	)
	parser.add_argument("-w", "--wordlist-source")
	parser.add_argument("-r", "--wikipedia-source")
	cmdargs = parser.parse_args()
	if cmdargs.wordlist_source is not None:
		create_word_table(cmdargs.wordlist_source)
	if cmdargs.wikipedia_source is not None:
		parse_articles(cmdargs.wikipedia_source)
	if cmdargs.wordlist_source is None and cmdargs.wikipedia_source is None:
		raise InvalidSourceException("No sources given, so no processing can be done")

conn.close()
print("Connection closed from database: " + dbname)