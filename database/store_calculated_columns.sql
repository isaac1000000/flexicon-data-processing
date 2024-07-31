ALTER TABLE words ADD COLUMN
frequency NUMERIC(8,7);

WITH maxCount AS (
	SELECT MAX(instances) FROM words
)
UPDATE words
SET frequency = frequency(id, (SELECT max FROM maxCount));

SELECT baseId, max(instances) INTO TEMPORARY TABLE groupMaxCount
FROM rels
GROUP BY baseId;

CREATE INDEX ididx ON groupMaxCount (baseId);

CREATE TABLE rels2 AS
SELECT *, strength(instances, (SELECT max FROM groupMaxCount WHERE baseId=rels.baseId)) FROM rels;

DROP TABLE rels;

ALTER TABLE rels2 RENAME TO rels;

ALTER TABLE ONLY rels ADD CONSTRAINT rels_pkey PRIMARY KEY (baseId, targetId);
CREATE INDEX baseIdStrengthIndex ON rels (baseId, strength DESC);
