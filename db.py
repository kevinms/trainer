import sqlite3, os, datetime

class DB():
	def __init__(self, name):
		self.db = self.initDatabase(name)
	def query(self, sql, args=(), one=False):
		c = self.db.cursor()
		c.execute(sql, args)
		r = [dict((c.description[i][0], value) for i, value in enumerate(row)) for row in c.fetchall()]
		return (r[0] if r else None) if one else r

	def rawQuery(self, sql, args=()):
		c = self.db.cursor()
		c.execute(sql, args)
		return c

	def encode(self, arg):
		return json.dumps(arg, sort_keys=True, indent=4)

	def initDatabase(self, name):

		if os.path.isfile(name):
			db = sqlite3.connect(name)
			db.row_factory = sqlite3.Row
			return db

		db = sqlite3.connect(name)
		db.row_factory = sqlite3.Row
		c = db.cursor()

		schema = open('schema.sql', 'r').read()
		c.executescript(schema)
		#self.loadLessonData(db, c)
		self.preloadTableData(db,c)

		db.commit()

		return db

	def preloadTableData(self, db, c):
		lang = open('data-lang.txt', 'r')
		lessons = open('data-lessons.txt', 'r')

		for l in lessons:
			if len(l) <= 0:
				continue
			row = l.rstrip().split(',')
			c.execute("INSERT INTO lesson(rowid,name) VALUES (?,?)", row)

		for r in lang:
			if len(r) <= 0:
				continue
			lesson_rowid, jp, en = r.rstrip().split(',')
			en = unicode(en, "utf-8").rstrip()
			jp = unicode(jp, "utf-8").rstrip()
			c.execute("INSERT INTO card VALUES (?,?,?)", (en, jp, ""))

			card_rowid = c.lastrowid
			last_seen = datetime.datetime.utcnow()
			wrong_answer = card_rowid % 2
			c.execute("INSERT INTO lesson_card VALUES(?,?,?,?)",
				(lesson_rowid, card_rowid, last_seen, wrong_answer))

	def loadLessonData(self, db, c):
		# Populate tables with dictionary.
		en = open('jp.txt', 'r')
		jp = open('en.txt', 'r')

		for enl, jpl in zip(en, jp):
			enl = unicode(enl, "utf-8").rstrip()
			jpl = unicode(jpl, "utf-8").rstrip()
			if len(enl) == 0 and len(jpl) == 0:
				continue
			c.execute("INSERT INTO card VALUES (?,?,?)", (enl, jpl, ""))

		c2 = db.cursor()
		c3 = db.cursor()
		
		c.execute("INSERT INTO lesson VALUES ('Lesson 1')")
		for lesson_row in c.execute("SELECT ROWID FROM lesson"):
			lesson_rowid = lesson_row["ROWID"]
			for card_row in c2.execute("SELECT ROWID FROM card"):
				card_rowid = card_row["ROWID"]
				last_seen = datetime.datetime.utcnow()
				wrong_answer = card_rowid % 2
				c3.execute("INSERT INTO lesson_card VALUES(?,?,?,?)",
					(lesson_rowid, card_rowid, last_seen, wrong_answer))

