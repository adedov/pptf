import os, sys
import json
import re
import sqlite3 as DB

from doit import tools
from doit.action import CmdAction

if "CASE" not in os.environ:
	print "Please set CASE environment variable."
	sys.exit(1)

class CaseConfig:
	def __init__(self, confname):
		conf_json = file("%s.json" % confname, "r").read()
		c = json.loads(conf_json)

		self.name = confname
		self.dbreport = ""
		self.passwords = c["passwords"]
		self.dicts = c["dicts"]
		self.rules = c["rules"]
		self.meters = c["meters"]
		self.meter_cmd = {}
		self.meter_files = {} # (p,m) -> file
		self.john_files = {} # (p,m) -> file
		self.pot_files = {} # (p,m,d) -> file 
		self.wc_files = []
		self.gen_dicts = []
		self.skip_guess = []

		if c.has_key("skip-guess"):
			self.skip_guess = c["skip-guess"]

		for m in self.meters:
			cmd = file("meters/%s.cmd" % m, "r").read()
			self.meter_cmd[m] = cmd

casename = os.environ["CASE"]
case_config = CaseConfig(casename)
print "Working with <%s> case study" % casename

def task__config():
	return {
		"actions" : [
			(tools.create_folder, ["output"]),
			(tools.create_folder, ["output/dict"]),
			(tools.create_folder, ["output/total"])
		]
	}

rm_action = lambda f: "rm -f %s" % (f)

#
# Run password meters
#

def make_task_for_meters(wordsets, sourcepath):
	for m in case_config.meters:
		for p in wordsets:
			target = "output/%s-%s.meter" % (p, m)
			source = "%s/%s.lst" % (sourcepath, p)
			case_config.meter_files[(p,m)] = target
			# meter command:
			meter_cmd = case_config.meter_cmd[m].rstrip() % {"source" : source} 
			meter_cmd += " | env LANG=C grep '^OK: ' | cut -b 5- >" + target

			yield {
				"name" : target,
				"actions" : [ meter_cmd ],
				"file_dep" : [ source ],
				"targets" : [ target ],
				"uptodate" : [ tools.config_changed(meter_cmd) ]
			}

def task_password_meters():
	yield make_task_for_meters(case_config.passwords, "passwords")

def task_generate_john():
	def generate_john(src, target):
		inp = file(src, "r")
		out = file(target, "w")
		while True:
			ln = inp.readline()
			if not ln:
				return
			pwd = ln.rstrip("\r\n")
			out.write("$dummy$%s\n" % (pwd.encode("hex"),))

	for x in case_config.meter_files.items():
		(p, m), f = x

		if p in case_config.skip_guess:
			continue

		target = "output/%s-%s.john" % (p, m)
		case_config.john_files[(p,m)] = target

		yield {
			"name" : target,
			"actions" : [ (generate_john, [f, target]) ],
			"file_dep" : [ f ],
			"targets" : [ target ],
			"verbosity" : 2
		}

def task_meters():
	yield {
		"name" : "meters",
		"actions" : None,
		"task_dep" : [ "password_meters", "generate_john" ]
	}

#
# Guessing passwords
#

def task_generate_dictionaries():
	for d in case_config.dicts:
		for r in case_config.rules:
			if r == "none":
				rules = ""
			elif r == "default":
				rules = "--rules"
			else:
				rules = "--rules=" + r

			source = "dict/%s.dict" % (d,)
			target = "output/dict/%s-%s.dict" % (d, r)
			case_config.gen_dicts.append(target)
			
			yield {
				"name" : target,
				"actions" : [ "run/john --nolog --wordlist=%s --session=%s %s --stdout > %s" % (source, target, rules, target) ],
				"targets" : [ target ],
				"file_dep" : [ source ]
			}

def task_guess_passwords():
	for jn in case_config.john_files.items():
		(p,m),j = jn

		for d in case_config.gen_dicts:
			dname = os.path.splitext(os.path.basename(d))[0]
			sess = "%s-%s" % (os.path.splitext(j)[0], dname)
			target = sess + ".pot"
			case_config.pot_files[(p,m,dname)] = target

			yield {
				"name" : target,
				"actions" : [
					rm_action(target),
					"run/john --nolog --format=dummy --fork=4 --wordlist=%s --session=%s %s --pot=%s >/dev/null" % (d, sess, j, target),
				],
				"targets" : [ target ],
				"file_dep" : [ j, d ]
			}

def task_crack():
	yield {
		"name" : "crack",
		"actions" : None,
		"task_dep" : [ "generate_dictionaries", "guess_passwords" ]
	}

#
# Reporting
#

def task_gen_password_tops():
	topn_task = lambda src, tgt:  CmdAction("sh gentop.sh 1000 %s %s" % (source, target)) 

	# top N for original password bases
	for p in case_config.passwords:
		source = "passwords/%s.lst" % (p,)
		target = "output/%s.top" % (p,)

		yield {
			"name" : target,
			"actions" : [ topn_task(source, target) ],
			"file_dep" : [ source ],
			"targets" : [ target ],
		}

	# top N for passwords passed polices
	for x in case_config.meter_files.items():
		(p, m), source = x
		target = "output/%s-%s.top" % (p, m)
 
		yield {
			"name" : target,
			"actions" : [ topn_task(source, target) ],
			"file_dep" : [ source ],
			"targets" : [ target ],
		}

def task_gen_total_pots():
	pots = {}
	for p in case_config.passwords:
		if p in case_config.skip_guess:
			continue

		for m in case_config.meters:
			t = (p, m)
			pots[t] = [ x for x in case_config.pot_files.values() if "-".join(t) in x ]

	for k in pots.keys():
		target = "output/total/%s-%s.pot" % k
		src_john = "output/%s-%s.john" % k

		yield {
			"name" : target,
			"actions" : [ "cat %s > %s" % (" ".join(pots[k]), target) ],
			"targets" : [ target ],
			"file_dep" : pots[k],
			"verbosity" : 2
		}

def task_wordcounts():
	def make_textwc_action(src, target):
		yield {
			"name" : target,
			"actions" : [ "wc -l < %s > %s" % (src, target) ],
			"file_dep" : [ src ],
			"targets" : [ target ]
		}

	def make_potwc_action(p, m, pot, target):
		j = case_config.john_files[(p,m)]
		yield {
			"name" : target,
			"actions" : [ "run/john --nolog --pot=%s --show %s | tail -1 | awk '{print $1;}' > %s" % (pot, j, target) ],
			"file_dep" : [ pot ],
			"targets" : [ target ]
		}

	def make_wc_action(seq, src, target):
		for x in seq:
			s = src % x
			t = target % x + ".wc"
			case_config.wc_files.append(t)
			yield make_textwc_action(s, t)

	yield make_wc_action(case_config.passwords, "passwords/%s.lst", "output/%s.lst")
	yield make_wc_action(case_config.gen_dicts, "%s", "%s")
	yield make_wc_action(case_config.meter_files.values(), "%s", "%s")

	for ((p,m,d),pot) in case_config.pot_files.items():
		case_config.wc_files.append(pot+".wc")
		yield make_potwc_action(p, m, pot, pot+".wc")
	
	# only cases with john files are crackable
	for (p,m) in case_config.john_files.keys():
		pot = "output/total/%s-%s.pot" % (p,m)
		case_config.wc_files.append(pot+".wc")
		yield make_potwc_action(p, m, pot, pot+".wc") 

def task_generate_database_report():
	def read_wc(filename):
		with file(filename, "r") as f:
			ln = f.read().strip()
			return int(ln)

	def file_to_name(filename):
		return os.path.splitext(os.path.basename(filename))[0]

	def generate_report_db(dbname):
		meters = case_config.meters
		dict_sizes = [ (file_to_name(x), read_wc(x + ".wc")) for x in case_config.gen_dicts ]
		password_sizes = [ (x, read_wc("output/%s.lst.wc" % x)) for x in case_config.passwords ]
		meter_sessions = [ (x[0], read_wc(x[1]+".wc")) for x in case_config.meter_files.items() ]
		crack_sessions = [ (x[0], read_wc(x[1]+".wc")) for x in case_config.pot_files.items() ]

		dict_sizes.append(("TOTAL", 0))
		for (p,m) in case_config.john_files.keys():
			potwc = "output/total/%s-%s.pot.wc" % (p,m)
			crack_sessions.append( ((p,m,"TOTAL"), read_wc(potwc)) )

		con = DB.Connection(dbname)
		cur = con.cursor()

		for x in dict_sizes:
			cur.execute("INSERT INTO dicts VALUES (?, ?)", (x[0], x[1]))

		for x in password_sizes:
			cur.execute("INSERT INTO passwords VALUES (?, ?)", (x[0], x[1]))

		for x in meter_sessions:
			print x
			(p, m), passok = x
			print p, m
			cur.execute("INSERT INTO meter_sessions VALUES (?, ?, ?)", (p, m, passok))

		for x in crack_sessions:
			(p, m, d), cnt = x
			cur.execute("INSERT INTO crack_sessions VALUES (?, ?, ?, ?)", (p, m, d, cnt)) 

		v_crack = "CREATE VIEW v_crack_report_abs AS SELECT passwords, dict, dict_size, "
		meter_cases = ", ".join([ "MAX(CASE WHEN meter = '%s' THEN success END) AS '%s'" % (m,m) for m in meters ])
		v_crack += meter_cases
		v_crack += " FROM v_effectiveness GROUP BY dict, passwords"
		print v_crack
		cur.execute(v_crack)

		v_crack = "CREATE VIEW v_crack_report AS SELECT passwords, dict, dict_size, "
		meter_cases = ", ".join([ "MAX(CASE WHEN meter = '%s' THEN success_part END) AS '%s'" % (m,m) for m in meters ])
		v_crack += meter_cases
		v_crack += " FROM v_effectiveness GROUP BY dict, passwords"
		cur.execute(v_crack)

		v_eff = "CREATE VIEW v_eff_report AS SELECT passwords, dict, dict_size, "
		meter_cases = ", ".join([ "MAX(CASE WHEN meter = '%s' THEN dict_to_success END) AS '%s'" % (m,m) for m in meters ])
		v_eff += meter_cases
		v_eff += " FROM v_effectiveness GROUP BY dict, passwords"
		cur.execute(v_eff)

		v_psy = "CREATE VIEW v_psy_abs_pivot AS SELECT passwords, "
		meter_cases = ", ".join([ "MAX(CASE WHEN meter = '%s' THEN pass_part END) AS '%s'" % (m,m) for m in meters ])
		v_psy += meter_cases
		v_psy += " FROM v_psychology_abs GROUP BY passwords"
		cur.execute(v_psy)

		v_psy = "CREATE VIEW v_psy_pivot AS SELECT passwords, "
		meter_cases = ", ".join([ "MAX(CASE WHEN meter = '%s' THEN pass_part END) AS '%s'" % (m,m) for m in meters ])
		v_psy += meter_cases
		v_psy += " FROM v_psychology GROUP BY passwords"
		cur.execute(v_psy)

		con.commit()

	case_config.dbreport = target = "output/report-%s.db" % (case_config.name,)
	yield {
		"name" : target,
		"actions" : [
			"rm -f %s" % (target,),
			"sqlite3 %s < sql/report_schema.sql" % (target,),
			(generate_report_db, [target])
		],
		"file_dep" : case_config.wc_files,
		"task_dep" : [ "wordcounts" ],
		"targets" : [ target ]
	}

def task_show_database_report():
	report_sql = "output/show-report-%s.sql" % (case_config.name,)

	def generate_show_report():
		with file(report_sql, "w") as f:
			abs_sql = ""
			eff_sql = ""
			eco_sql = ""

			for p in case_config.passwords:
				if p in case_config.skip_guess:
					continue

				abs_sql += "SELECT * FROM v_crack_report_abs WHERE passwords LIKE '%s' ORDER BY dict_size;\n" % p
				eff_sql += "SELECT * FROM v_crack_report WHERE passwords LIKE '%s' ORDER BY dict_size;\n" % p
				eco_sql += "SELECT * FROM v_eff_report WHERE passwords LIKE '%s' ORDER BY dict_size;\n" % p

			sql = """
.mode column
.width 25 25 15 12 12 12 12 12 12
.header off
SELECT '
Absolute-numbers report
';
.header on
%(abs_sql)s

.header off
SELECT '
Effectiveness of guessing
';
.header on
%(eff_sql)s

.header off
SELECT '
Economy of guessing
';
.header on
%(eco_sql)s

.header off
SELECT '
Psy. acceptance
';
.header on
--.width 25 0
SELECT * FROM v_psy_abs_pivot;
SELECT * FROM v_psy_pivot;
""" % { "abs_sql" : abs_sql, "eff_sql" : eff_sql, "eco_sql" : eco_sql }
			f.write(sql)

	yield {
		"name" : report_sql,
		"actions" : [ generate_show_report ],
		"targets" : [ report_sql ]
	}

	yield {
		"name" : "Show report",
		"actions" : [ "sqlite3 %s < %s" % (case_config.dbreport, report_sql) ],
		"file_dep" : [ case_config.dbreport, report_sql ],
		"verbosity" : 2,
		"uptodate" : [ False ]
	}
