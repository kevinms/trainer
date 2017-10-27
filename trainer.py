#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses, os, sys, getopt, random
import locale, unicodedata, json
from curses import wrapper
import db

# Disable support for terminal colors.
os.environ["TERM"] = "vt220"
locale.setlocale(locale.LC_ALL, '')

db = db.DB('data.db')

doNumberChoice = False

def indexToChoice(num):
	if doNumberChoice:
		return str(num)
	return chr( num + (ord('a') - 1) )

def choiceToIndex(choice):
	n = ord(choice)
	if n >= ord('a'):
		n -= ord('a') - ord('1')
	return int(chr(n))

doInvert = False

def getSides(card):
	if doInvert:
		return 'side3', 'side2', 'side1'
	return 'side2', 'side3', 'side1'

logFile = open('trainer.log', 'w')

def debug(s):
	#logFile.write(str(s.encode('utf-8')) + '\n')
	logFile.write(str(s) + '\n')
	logFile.flush()

def pretty(obj):
	print(json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': ')))

def getAllLessons():
	return {'lessons': db.query('SELECT ROWID, * FROM lesson')}

def getCardsInLessons(lessonIDs):
	if len(lessonIDs) > 0:
		sql = '''
			SELECT * FROM card JOIN lesson_card ON (card.ROWID == lesson_card.fk_card)
			WHERE lesson_card.fk_lesson in ({0})
		'''.format(','.join('?' for _ in lessonIDs))
		data = db.query(sql, lessonIDs)
	else:
		data = db.query('''
			SELECT * FROM card JOIN lesson_card ON (card.ROWID == lesson_card.fk_card)
		''')
	return {'cards': data}

def drawCenterXY(w, s, yoff = 0, xoff = 0, cursorReset=True):
	(y, x) = w.getmaxyx()
	l = len(s.encode('utf-8'))
	try:
		w.addstr(int(y/2 + yoff), int(xoff), s.encode('utf-8'))
	except Exception as e:
		debug('addstr() failed: ' + str(e))
	if cursorReset:
		w.move(0, 0)

def drawCenter(w, s, yoff = 0):
	drawCenterXY(w, s, yoff, 4)

class Counter():
	def __init__(self, pmin, pmax, start=0, prandom=True):
		self.count = start
		self.cmin = pmin
		self.cmax = pmax
		self.crandom = prandom
		self.randomHistory = []
		self.randomIndex = 0
		if self.crandom:
			self.randnext()
	def randnext(self):
		if self.randomIndex < len(self.randomHistory):
			# Here we replay history forwards.
			self.randomIndex += 1
		else:
			if self.randomIndex >= 100:
				self.randomHistory.pop(0)
			else:
				self.randomIndex += 1
			n = random.randint(self.cmin, self.cmax - 1)
			self.randomHistory.append(n)
		self.count = self.randomHistory[self.randomIndex - 1]
	def randprev(self):
		if self.randomIndex > 1:
			self.randomIndex -= 1
			self.count = self.randomHistory[self.randomIndex - 1]
	def next(self):
		if self.crandom:
			self.randnext()
		else:
			self.count += 1
			if self.count >= self.cmax:
				self.count = self.cmin
	def prev(self):
		if self.crandom:
			self.randprev()
		else:
			self.count -= 1
			if self.count <= self.cmin:
				self.count = self.cmax
	def get(self):
		return self.count

def randomCard(cards, notThisCard):
	card = notThisCard
	while card == notThisCard:
		n = random.randint(0, len(cards) - 1)
		card = cards[n]
	return card

def drawCard(win, card, showAll = False):
	win.clear()
	pri, sec, ter = getSides(card)
	drawCenter(win, card[pri])
	if showAll:
		drawCenter(win, card[ter], -1)
		drawCenter(win, card[sec], 1)
	win.refresh()
	t = len(card[pri]) * 0.75 * 1000
	win.timeout(int(t))

def drawChoiceQuestion(win, card, cardList):
	win.clear()
	pri, sec, ter = getSides(card)
	drawCenterXY(win, card[pri], -1, 4)

	answers = [randomCard(cardList, card) for i in range(3)]
	answers.append(card)
	random.shuffle(answers)
	
	(y, x) = win.getmaxyx()
	hw = x / 2

	i = 1
	for c in answers:
		xoff = hw if i % 2 == 0 else 0
		yoff = 0 if i <= 2 else 1
		choice = indexToChoice(i)
		drawCenterXY(win, '%s: %s' % (choice, c[sec]), yoff, xoff)
		i += 1
	win.refresh()
	win.timeout(-1)

	for n, c in enumerate(answers):
		if c == card:
			return n+1
	raise Exception('Couldn\'t find card in answer list?!')

def runChoiceQuiz(win, lessonIDs, doRandom):
	cards = getCardsInLessons(lessonIDs)['cards']
	i = Counter(0, len(cards)-1, prandom=doRandom)
	card = cards[i.get()]
	pri, sec, ter = getSides(card)
	answer = drawChoiceQuestion(win, card, cards)
	while 1:
		try:
			key = win.getkey()
			debug('key \'%s\', answer %d: %s' % (key, answer, card[sec]))
			if key in ('KEY_RIGHT', ' '):
				i.next()
			elif key in ('KEY_LEFT'):
				i.prev()
			elif key in ('KEY_RESIZE'):
				answer = drawChoiceQuestion(win, card, cards)
				continue
			elif key in ('1', '2', '3', '4', 'a', 'b', 'c', 'd'):
				#if ord(key) >= ord('a'):
				#	key = chr( ord(key) - (ord('a') - ord('1')) )
				#	debug('new key: %s' % key)
				#if int(key) == answer:
				if choiceToIndex(key) == answer:
					debug('Correct!')
					i.next()
				else:
					debug('Wrong!')
					drawCard(win, card, showAll=True)
					continue
			elif key in ('z'):
				debug('Showing info.')
				drawCard(win, card, showAll=True)
				continue
			else:
				i.next()
		except curses.error:
			debug('Timer: ' + str(curses.error))
			i.next()
		card = cards[i.get()]
		answer = drawChoiceQuestion(win, card, cards)

def drawTypingQuestion(win, card, cardList, userInput=[]):
	win.clear()
	pri, sec, ter = getSides(card)
	drawCenterXY(win, card[pri], 0, 4)

	s = ''.join(userInput)

	drawCenterXY(win, '> ' + s, 1, cursorReset=False)

	win.refresh()
	win.timeout(-1)

def runTypingQuiz(win, lessonIDs, doRandom):
	cards = getCardsInLessons(lessonIDs)['cards']
	i = Counter(0, len(cards)-1, prandom=doRandom)
	card = cards[i.get()]
	pri, sec, ter = getSides(card)
	showAnswer = False
	answer = []

	drawTypingQuestion(win, card, cards, answer)
	while 1:
		try:
			char = win.get_wch()

			debug('str: {} -> {}'.format(char, ord(char)))

			if showAnswer:
				# Goto next card.
				showAnswer = False
				i.next()
			elif ord(char) == 127:
				# Backspace
				answer = answer[:-1]
			elif char in ('\n'):
				s_answer = ''.join(answer)
				if s_answer == card[sec]:
					debug('{} matches {}'.format(s_answer, card[sec]))
					i.next()
					card = cards[i.get()]
				else:
					showAnswer = True
					debug('{} does not match {}'.format(s_answer, card[sec]))
				answer = []
			else:
				answer.append(char)
	
		except curses.error:
			debug('Timer: ' + str(curses.error))
			i.next()
			card = cards[i.get()]
			showAnswer = False

		try:
			if showAnswer:
				drawCard(win, card, showAll=True)
			else:
				drawTypingQuestion(win, card, cards, answer)
		except:
			debug('Draw exception: ' + str(curses.error))


def runCards(win, lessonIDs, doRandom):
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
			elif key in ('KEY_RESIZE'):
				drawCard(win, card, showAll)
				continue
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
	('r','random','Randomize cards when training.'),
	('q','choice-quiz','Present multiple choice quiz questions.'),
	('w','typing-quiz','Present typing quiz questions.'),
	('i','invert','Invert cards so you are quized on the card backs.')]
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

	global doInvert, doNumberChoice

	lessonIDs = []
	doLessonList = False
	doCardList = False
	doRandom = False
	doChoiceQuiz = False
	doTypingQuiz = False
	for o, a in opts:
		if o in ('-h', '--help'):
			usage()
		elif o in ('-t', '--train'):
			IDranges = a.split(",")
			for r in IDranges:
				start, sep, stop = r.partition('-')
				if stop == '':
					stop = start
				for i in range(int(start), int(stop) + 1):
					lessonIDs.append(i)
		elif o in ('-l', '--lessons'):
			doLessonList = True
		elif o in ('-c', '--cards'):
			doCardList = True
		elif o in ('-r', '--random'):
			doRandom = True
		elif o in ('-q', '--choice-quiz'):
			doChoiceQuiz = True
		elif o in ('-w', '--typing-quiz'):
			doTypingQuiz = True
		elif o in ('-i', '--invert'):
			doInvert = True
		elif o in ('-n', '--number-choice'):
			doNumberChoice = True
		else:
			assert False, 'Unhandled option: ' + str(o)
	
	if doLessonList:
		pretty(getAllLessons())
	elif doCardList:
		pretty(getCardsInLessons(lessonIDs))
	elif doChoiceQuiz:
		wrapper(runChoiceQuiz, lessonIDs, doRandom)
	elif doTypingQuiz:
		wrapper(runTypingQuiz, lessonIDs, doRandom)
	else:
		wrapper(runCards, lessonIDs, doRandom)

if __name__ == "__main__":
	main()
