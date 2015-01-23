# Custom implementation of http://technet.microsoft.com/en-us/library/jj943764.aspx
import sys

class Fail:
	def __init__(self, reason):
		self.reason = reason

	def __nonzero__(self):
		return False

D = 1
L = 2
U = 4
O = 8

lowercase = "abcdefghijklmnopqrstuvwxyz"
uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
numerics = "0123456789"
special = "@#$%^&*-_+=[]{}|\\:`,.?/'~\"();"
abc = lowercase + uppercase + numerics + special

def analyze(p):
	classes = 0
	l = len(p)

	if l < 8:
		return Fail("too short")

	if l > 16:
		return Fail("too long")

	if ".@" in p:
		return Fail("strange .@ rule")

	for c in list(p):
		if ord(c) > 127:
			return Fail("unicode")

		if c not in abc:
			return Fail("forbidden character")

		if c.isdigit():
			classes |= D
		elif c.islower():
			classes |= L
		elif c.isupper():
			classes |= U
		else:
			classes |= O

	if bin(classes).count('1') < 3:
		return Fail("need at least 3 different char classes")

	return True

while True:
	x = sys.stdin.readline()
	if not x:
		break

	x = x.rstrip('\n\r')
	passok = analyze(x)

	if passok:
		print "OK: %s" % x
	else:
		print "Bad: %s (%s)" % (x, passok.reason)
