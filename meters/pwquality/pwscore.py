import sys
import pwquality

pwscore = pwquality.PWQSettings()

while True:
	ln = sys.stdin.readline()
	if not ln:
		break
	
	try:
		ln = ln.rstrip("\n\r")
		score = pwscore.check(ln)
		if score >= 55:
			print "OK: " + ln
		else:
			print "Bad: %d" % (score,)

	except pwquality.PWQError, e:
		print "Bad: %d" % (e.args[0],)
