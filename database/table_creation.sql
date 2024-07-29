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

CREATE OR REPLACE VIEW wordView AS (
	WITH maxCount AS (
		SELECT MAX(words.instances) as max
		FROM words
	)
	SELECT *, frequency(id, (SELECT max FROM maxCount))
	FROM words
);
CREATE OR REPLACE VIEW relView AS (
	WITH maxCount AS (
		SELECT MAX(words.instances) as max
		FROM words
	), groupMaxCount AS (
		SELECT rels.baseId, MAX(rels.instances) AS max
		FROM rels
		GROUP BY rels.baseId
	)
	SELECT rels.baseId,
		w1.word AS base,
		rels.targetId,
		w2.word AS target,
		w2.definition AS targetDefinition,
		frequency(rels.targetId, (SELECT max FROM maxCount)),
		strength(rels.instances, (SELECT max FROM groupMaxCount WHERE groupmaxcount.baseid = rels.baseid)),
		rels.instances
	FROM rels
		JOIN words w1 ON rels.baseId = w1.id
		JOIN words w2 ON rels.targetId = w2.id
);

SELECT * FROM relView;