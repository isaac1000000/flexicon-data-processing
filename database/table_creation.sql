DROP TABLE IF EXISTS words CASCADE;
DROP TABLE IF EXISTS rels;

/* IMPORTANT: Works with big-endian encoding on my machine */
CREATE OR REPLACE FUNCTION generate_key(varchar) 
RETURNS bigint AS '
 SELECT (''x''||substr(md5($1),1,16))::bit(64)::bigint;
' LANGUAGE sql;

CREATE TABLE words (
	id BIGINT PRIMARY KEY GENERATED ALWAYS AS (generate_key(word)) STORED,
	word varchar(50) NOT NULL,
	instances BIGINT NOT NULL DEFAULT 0,
	definition TEXT
);
GRANT SELECT, INSERT, UPDATE, DELETE ON words TO processing;
CREATE TABLE rels (
	baseId BIGINT NOT NULL references words(id),
	targetId BIGINT NOT NULL references words(id),
	instances BIGINT NOT NULL DEFAULT 1,
	PRIMARY KEY (baseId, targetId)
);
GRANT SELECT, INSERT, UPDATE, DELETE ON rels TO processing;

CREATE TABLE decks (
	id BIGSERIAL PRIMARY KEY,
	type varchar(10) NOT NULL,
	name varchar(50),
	ext varchar(10),
	size int,
	createdAt date,
	minFrequency NUMERIC(3,2),
	maxFrequency NUMERIC(3,2),
	minStrength NUMERIC(3,2),
	maxStrength NUMERIC(3,2)
);
GRANT SELECT, INSERT, UPDATE, DELETE ON decks TO api;

CREATE OR REPLACE FUNCTION frequency(targetId BIGINT, maxCount BIGINT)
RETURNS NUMERIC AS '
DECLARE targetCount BIGINT;
BEGIN
	SELECT instances INTO targetCount FROM words
		WHERE targetId = words.id;
	RETURN cbrt((targetCount - 1)::NUMERIC / (maxCount - 1));
END;
' LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION frequency(targetId BIGINT)
RETURNS NUMERIC AS '
DECLARE maxCount BIGINT;
BEGIN
	SELECT MAX(instances) INTO maxCount FROM words;
	RETURN frequency(targetId, maxCount);
END;
' LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION strength(instances BIGINT, maxCount BIGINT)
RETURNS NUMERIC AS '
DECLARE res NUMERIC;
BEGIN
	SELECT instances::numeric / maxCount into res;
	RETURN res;
END;
' LANGUAGE plpgsql STABLE;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO api;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO api;