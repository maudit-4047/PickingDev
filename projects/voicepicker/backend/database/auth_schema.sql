
-- PostgreSQL Schema for Supabase
-- This file uses PostgreSQL-specific syntax

CREATE TABLE workers (
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	name VARCHAR(100) NOT NULL,
	team_id INT,
	pin VARCHAR(10) NOT NULL,
	voice_ref TEXT,                           -- for voice authentication
	status VARCHAR(20) DEFAULT 'active',      -- active/inactive
	role VARCHAR(50) DEFAULT 'picker',        -- picker, forklift, loader etc.
	created_at TIMESTAMP DEFAULT NOW(),
	updated_at TIMESTAMP DEFAULT NOW()
);

-- optional future table for teams
CREATE TABLE teams (
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	name VARCHAR(50) NOT NULL,
	created_at TIMESTAMP DEFAULT NOW()
);
