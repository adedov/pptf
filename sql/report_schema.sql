CREATE TABLE passwords(name VARCHAR, size INT);
CREATE TABLE meter_sessions(passwords VARCHAR, meter VARCHAR, passok INT);
CREATE TABLE dicts(name VARCHAR, size INT);
CREATE TABLE crack_sessions(passwords VARCHAR, meter VARCHAR, dict VARCHAR, success INT);

-- views
create view v_psychology as
	select p.name as passwords, s.meter as meter, round((s.passok*1.0)/p.size,6) as pass_part
	from meter_sessions s join passwords p on (p.name = s.passwords);

create view v_psychology_abs as
	select p.name as passwords, s.meter as meter, s.passok as pass_part
	from meter_sessions s join passwords p on (p.name = s.passwords);

create view v_effectiveness as 
	select c.passwords as passwords, c.meter as meter, c.dict as dict, c.success as success, 
		round((1.0*c.success)/p.size,6) as success_part, 
		round((1.0*c.success)/d.size,6) as dict_to_success, d.size as dict_size 
	from crack_sessions c join dicts d on (c.dict = d.name) 
	join meter_sessions m on (m.meter = c.meter and m.passwords = c.passwords)
	join passwords p on (p.name = c.passwords);
