ALTER TABLE words ADD COLUMN
frequency NUMERIC(8,7);

WITH maxCount AS (
	SELECT MAX(instances) FROM words
)
UPDATE words
SET frequency = frequency(id, (SELECT max FROM maxCount));

ALTER TABLE rels ADD COLUMN 
strength NUMERIC(8,7);

WITH groupMaxCount AS (
	SELECT baseId, max(instances)
	FROM rels
	GROUP BY baseId
)
UPDATE rels
SET strength = strength(instances, (SELECT max FROM groupMaxCount WHERE baseId = rels.baseId));
