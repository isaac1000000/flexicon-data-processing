CREATE INDEX baseIdStrengthIndex ON rels (baseId, strength DESC);

CREATE INDEX idFrequencyIndex ON words(id, frequency DESC);
