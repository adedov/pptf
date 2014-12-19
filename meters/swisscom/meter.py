import sets
import sys

class Fail:
	def __init__(self, reason):
		self.reason = reason

	def __nonzero__(self):
		return False

D = 1
A = 2
O = 4
ABC = "abcdefghijklmnopqrstuvwxyz"
CBA = "zyxwvutsrqponmlkjihgfedcba"

def analyze(p):
	classes = 0
	l = len(p)
	lenok = False
	uniq = sets.Set()

	for c in list(p):
		if ord(c) > 127:
			return Fail("unicode")

		uniq.add(c)

		if c.isdigit():
			classes |= D
		elif c.isalpha():
			classes |= A
		else:
			classes |= O

	if classes == D:
		return Fail("digits")

	if len(uniq) < 3:
		return Fail("need at least 3 different chars")

	if classes & A & D or classes & A & O or classes & D & O:
		if l < 8:
			return Fail("too short")
	else:
		if l < 12:
			return Fail("too short")
	
	if l > 32:
		return Fail("too long")

	p1 = p.lower()
	if p1 in ABC or p1 in CBA:
		return Fail("abcde or edcba")

	return True

while True:
	x = sys.stdin.readline()
	if not x:
		break

	x = x.rstrip('\n')
	passok = analyze(x)

	if passok:
		print "OK: %s" % x
	else:
		print "Bad: %s (%s)" % (x, passok.reason)

