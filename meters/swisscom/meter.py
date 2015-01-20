import sys

class Fail:
	def __init__(self, reason):
		self.reason = reason

	def __nonzero__(self):
		return False

D = 1
A = 2
O = 4
L = 8
U = 16
ABC = "abcdefghijklmnopqrstuvwxyz"
CBA = "zyxwvutsrqponmlkjihgfedcba"

def analyze(p):
	classes = 0
	l = len(p)
	lenok = False
	uniq = set()

	for c in list(p):
		if ord(c) > 127:
			return Fail("unicode")

		uniq.add(c)

		if c.isdigit():
			classes |= D
		elif c.isalpha():
			classes |= A
			if c.isupper():
				classes |= U
			else:
				classes |= L
		elif c.isspace():
			return Fail("spaces not allowed")
		else:
			classes |= O

	if classes == D:
		return Fail("digits")

	if len(uniq) < 3:
		return Fail("need at least 3 different chars")

	if (classes & A and classes & D) or (classes & A and classes & O) or (classes & D and classes & O):
		if l < 8:
			return Fail("too short")
	else:
		if l < 12:
			return Fail("too short")

		if classes & A and not (classes & L and classes & U):
			return Fail("need upper & lowercase")

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

