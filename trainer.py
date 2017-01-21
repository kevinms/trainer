#!/env/python
# -*- coding: utf-8 -*-

import curses, os, locale, unicodedata
from curses import wrapper
import db

# Disable support for terminal colors.
os.environ["TERM"] = "vt220"
locale.setlocale(locale.LC_ALL, '')

db = db.DB('data.db')

def getAllLessons():
	return {'lessons': db.query('SELECT ROWID, * FROM lesson')}

def getCardsInLessons(lessonIDs):
	ids = ','.join(str(x) for x in lessonIDs)
	r = {'cards': db.query('''
		SELECT * FROM card JOIN lesson_card ON (card.ROWID == lesson_card.fk_card)
		WHERE lesson_card.fk_lesson IN (?)
	''', (ids,) )}
	return r

def drawCenter(w, s, offset = 0):
	(y, x) = w.getmaxyx()
	l = len(s.encode('utf-8'))
	w.addstr(y/2 + offset, 4, s.encode('utf-8'))
	w.move(0, 0)

class Counter():
	def __init__(self, pcount, pmin, pmax):
		self.count = pcount
		self.min = pmin
		self.max = pmax
	def next(self):
		self.count += 1
		if self.count >= self.max:
			self.count = self.min
	def prev(self):
		self.count -= 1
		if self.count <= self.min:
			self.count = self.max
	def get(self):
		return self.count

def drawCard(win, card, showAll = False):
	win.clear()
	drawCenter(win, card['side1'])
	if showAll:
		drawCenter(win, card['side2'], 2)
	win.refresh()
	t = len(card['side1']) * 0.75 * 1000
	win.timeout(int(t))

def main(win):
	lessonIDs = [1]
	cards = getCardsInLessons(lessonIDs)['cards']
	i = Counter(0, 0, len(cards)-1)
	card = cards[i.get()]
	drawCard(win, card)
	showAll = False
	while 1:
		try:
			key = win.getkey()
			if key in ('KEY_RIGHT', ' '):
				i.next()
			elif key in ('KEY_LEFT'):
				i.prev()
			elif key in ('z'):
				showAll = not showAll
				drawCard(win, card, showAll)
				continue
			else:
				i.next()

			#win.addstr(0, 4, key.encode('utf-8'))
			#win.move(0, 0)
			#win.refresh()
			#key = win.getkey()
		except curses.error:
			i.next()
		card = cards[i.get()]
		drawCard(win, card, showAll)

wrapper(main)
