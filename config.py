import os
from utils import InvalidCredentialsException
from dotenv import load_dotenv, dotenv_values

def load_env_config():
	config = {}

	# Gets environment variables from .env
	load_dotenv()
	
	config["host"] = os.getenv("HOST")
	config["database"] = os.getenv("DATABASE")
	config["user"] = os.getenv("USER")
	config["password"] = os.getenv("PASSWORD")

	for key in config.keys():
		if config[key] == None:
			raise InvalidCredentialsException("No credentials found for environment variable " + key)

	return config


if __name__ == "__main__":
	config = load_env_config()
	print(config)