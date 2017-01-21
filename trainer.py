#!/usr/bin/env python
# -*- coding: utf-8 -*-

import curses, os, sys, getopt, random
import locale, unicodedata, json
from curses import wrapper
import db

# Disable support for terminal colors.
os.environ["TERM"] = "vt220"
locale.setlocale(locale.LC_ALL, '')

db = db.DB('data.db')

def pretty(obj):
	print json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))

def getAllLessons():
	return {'lessons': db.query('SELECT ROWID, * FROM lesson')}

def getCardsInLessons(lessonIDs):
	if len(lessonIDs) > 0:
		ids = ','.join(str(x) for x in lessonIDs)
		data = db.query('''
			SELECT * FROM card JOIN lesson_card ON (card.ROWID == lesson_card.fk_card)
			WHERE lesson_card.fk_lesson IN (?)
		''', (ids,))
	else:
		data = db.query('''
			SELECT * FROM card JOIN lesson_card ON (card.ROWID == lesson_card.fk_card)
		''')
	return {'cards': data}

def drawCenter(w, s, offset = 0):
	(y, x) = w.getmaxyx()
	l = len(s.encode('utf-8'))
	w.addstr(y/2 + offset, 4, s.encode('utf-8'))
	w.move(0, 0)

class Counter():
	def __init__(self, pmin, pmax, start=0, prandom=True):
		self.count = start
		self.cmin = pmin
		self.cmax = pmax
		self.crandom = prandom
		if self.crandom:
			self.randnext()
	def randnext(self):
		self.count = random.randint(self.cmin, self.cmax - 1)
	def next(self):
		if self.crandom:
			self.randnext()
		else:
			self.count += 1
			if self.count >= self.cmax:
				self.count = self.cmin
	def prev(self):
		self.count -= 1
		if self.count <= self.cmin:
			self.count = self.cmax
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

def run(win, lessonIDs, doRandom):
	cards = getCardsInLessons(lessonIDs)['cards']
	i = Counter(0, len(cards)-1, prandom=doRandom)
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

options = [ 
    ('h','help','This help.'),
    ('t:','train=','Training mode.'),
    ('l','lessons','List of all lessons.'),
    ('c','cards','List all cards in lessons fro -t.'),
    ('r','random','Randomize cards when training.')]
shortOpt = "".join([opt[0] for opt in options])
longOpt = [opt[1] for opt in options]

def usage():
    pad = str(len(max(longOpt, key=len)))
    fmt = '  -%s, --%-'+pad+'s : %s'
    print('Usage: '+sys.argv[0]+' [options]\n')
    for opt in options:
        print(fmt%(opt[0][0], opt[1], opt[2]))
    sys.exit(2)

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], shortOpt, longOpt)
	except getopt.GetoptError as err:
		print(str(err))
		usage()

	lessonIDs = []
	doLessonList = False
	doCardList = False
	doRandom = False
	for o, a in opts:
		if o in ('-h', '--help'):
			usage()
		elif o in ('-t', '--train'):
			if int(a) != 0:
				lessonIDs.append(int(a))
		elif o in ('-l', '--lessons'):
			doLessonList = True
		elif o in ('-c', '--cards'):
			doCardList = True
		elif o in ('-r', '--random'):
			doRandom = True
		else:
			assert False, 'Unhandled option: ' + str(o)
	
	if doLessonList:
		pretty(getAllLessons())
	if doCardList:
		pretty(getCardsInLessons(lessonIDs))
	else:
		wrapper(run, lessonIDs, doRandom)

if __name__ == "__main__":
	main()
