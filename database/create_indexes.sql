ALTER TABLE ONLY rels ADD CONSTRAINT rels_pkey PRIMARY KEY (baseId, targetId);
CREATE INDEX baseIdStrengthIndex ON rels (baseId, strength DESC);

CREATE INDEX idFrequencyIndex ON words(id, frequency DESC);

GRANT SELECT ON words TO api;
GRANT SELECT ON rels TO api;
GRANT SELECT, INSERT, UPDATE, DELETE ON decks TO api;