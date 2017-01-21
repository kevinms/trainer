CREATE TABLE IF NOT EXISTS lesson (
	name TEXT
);

CREATE TABLE IF NOT EXISTS card (
	side1 TEXT,
	side2 TEXT,
	note TEXT
);

CREATE TABLE IF NOT EXISTS lesson_card (
	fk_lesson INTEGER,
	fk_card INTEGER,
	last_seen INTEGER,
	wrong_answer INTEGER,
	FOREIGN KEY(fk_lesson) REFERENCES lesson(ROWID),
	FOREIGN KEY(fk_card) REFERENCES card(ROWID),
	UNIQUE(fk_lesson, fk_card)
);
