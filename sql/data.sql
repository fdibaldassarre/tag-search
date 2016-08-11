CREATE TABLE MetaTags (
  Code INTEGER PRIMARY KEY,
	Name TEXT UNIQUE,
	HasMagnitude INTEGER
);

INSERT INTO MetaTags(Name, HasMagnitude) VALUES ('Content', 1);

CREATE TABLE Tags (
	Code INTEGER PRIMARY KEY,
	Name TEXT UNIQUE,
	Meta INTEGER
);

/*CREATE INDEX 'TagsName' ON Tags(Name);*/

CREATE TABLE Files (
	Code INTEGER PRIMARY KEY,
	Location TEXT,
	Name TEXT,
	Mime TEXT,
	UNIQUE (`Location`,`Name`)
);

CREATE TABLE TagsFiles (
	Tag INTEGER,
	File INTEGER,
	Magnitude INTEGER,
	PRIMARY KEY  (`Tag`,`File`)
);
