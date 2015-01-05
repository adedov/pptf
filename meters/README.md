Place password policy wrappers here. Each wrapper must take password dump file as an input and produce output that differentiate good passwords from bad ones:

```
OK: Good Password\n
Bad: Bad Password\n
```

Specific requirements for wrapper:

- Must be exactly **one line** of shell code.
- Use %(source)s as a name of input file.
- Print results to stdout, one per password, either one:
  - OK: password
  - Bad: password

Framework provides one special password policy *NOMETER* that accepts any password as a good one:

```
awk '{print "OK: " $0 ;}' < %(source)s
```