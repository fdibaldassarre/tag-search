CREATE TABLE Categories (
  Code INTEGER PRIMARY KEY,
	Name TEXT UNIQUE,
	HasMagnitude INTEGER
);

INSERT INTO Categories(Name, HasMagnitude) VALUES ('Content', 0);

CREATE TABLE Tags (
	Code INTEGER PRIMARY KEY,
	Name TEXT UNIQUE,
	Category INTEGER
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
