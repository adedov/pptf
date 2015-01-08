## Intro

This project aims to help developers to measure important properties of password policy they use in applications. The measurement is offline meaning that there is no experiments on people are involved.

The main idea is to apply password policy of interest to password dumps. And then to model guessing attacks on passwords from specific dump that have passed the policy. Additionally, the policy is applied to a number of knowingly good passwords to see if policy allows users to choose strong passwords from the key space of their choice. The different parameters of the process are being measured during attack model:

- Number of passwords passed the policy
- Number of guessed passwords
- Size of attackers dictionary
- etc.

See my [slides](http://www.slideshare.net/antondedov5/zn2013-testing-of-password-policy-abridged) from [ZeroNights 2013](http://2013.zeronights.org/fasttrack) conference.

## Requirements

1. [John The Ripper](http://openwall.com/john/)
1. Python [doit](http://pydoit.org/)
1. Sqlite3
1. Node.js recommended

## Preparations
1. Compile John The Ripper; link *run* folder into local directory.
1. Place big enough password dumps into "passwords" folder (see [passwords/README.md](passwords/README.md)).
1. Make command wrapper and, probably, implementation of password policy of interest in "meters" folder (see [meters/README.md](meters/README.md)).
1. Configure test case configuration in JSON. Use [default.json](default.json) as example.

## Run

If you have configuration for test case in "test1.json", use following command to run experiment:

```
% CASE=test1 doit
```

## Artefacts

The framework creates folder *output* to put all intermediate and final artefacts. The following files are useful for analysis:

<table>
<tr>
<td>output/&lt;dump&gt;-&lt;policy&gt;.meter</td>
<td>All passwords from particular *dump* that have been accepted by *policy*.</td>
</tr>
<tr>
<td>output/&lt;dump&gt;-&lt;policy&gt;.john</td>
<td>John the Ripper input file for pair {*dump*, *policy*}.</td>
</tr>
<tr>
<td>output/&lt;dump&gt;-&lt;policy&gt;-&lt;dictionary&gt;.pot</td>
<td>JtR pot files for cracking sessions against passwords from *dump* accepted by the *policy* using specific *dictionary*.</td>
</tr>
<tr>
<td>output/report-&lt;case&gt;.db</td>
<td>SQLite3 database that contain statistics data about all password evaluation and guessing sessions for test the test *case*. Take a look at [report_schema.sql](sql/report_schema.sql) for schema.</td>
</tr>
</table>
