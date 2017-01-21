#!/usr/bin/env python
# -*- coding: utf-8 -*-

import curses, os, sys, getopt
import locale, unicodedata, json
from curses import wrapper
import db

# Disable support for terminal colors.
os.environ["TERM"] = "vt220"
locale.setlocale(locale.LC_ALL, '')

db = db.DB('data.db')

def json_load_byteified(file_handle):
	return _byteify(
		json.load(file_handle, object_hook=_byteify),
		ignore_dicts=True
	)

def json_loads_byteified(json_text):
	return _byteify(
		json.loads(json_text, object_hook=_byteify),
		ignore_dicts=True
	)

def _byteify(data, ignore_dicts = False):
	if isinstance(data, unicode):
		return data.encode('utf-8')
	if isinstance(data, list):
		return [ _byteify(item, ignore_dicts=True) for item in data ]
	if isinstance(data, dict) and not ignore_dicts:
		return {
			_byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
			for key, value in data.iteritems()
		}
	return data


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

def run(win, lessonIDs):
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

options = [ 
    ('h','help','This help.'),
    ('t:','train=','Training mode.'),
    ('l','list','List of all lessons.')]
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
	doList = False
	for o, a in opts:
		if o in ('-h', '--help'):
			usage()
		elif o in ('-t', '--train'):
			lessonIDs.append(int(a))
		elif o in ('-l', '--list'):
			doList = True
		else:
			assert False, 'Unhandled option: ' + str(o)
	
	if doList:
		print json.dumps(getAllLessons(),
			sort_keys=True, indent=4, separators=(',', ': '))
	else:
		wrapper(run, lessonIDs)

if __name__ == "__main__":
	main()
