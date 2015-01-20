# https://passwordday.org/en/
# <script type="text/javascript" src="//www.microsoft.com/global/security/RenderingAssets/passwdcheck.js"></script>
import sys

while True:
	x = sys.stdin.readline()
	if not x:
		break

	x = x.rstrip('\n\r')

	if len(x) >= 14:
		print "OK: %s" % x
	else:
		print "Bad: %s (%s)" % (x, 'too short')

