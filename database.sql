-- SQLite Database Schema
-- This file is for reference only - the database is automatically created by the Flask app

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    item_name TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    date_reported DATETIME NOT NULL,
    type TEXT CHECK(type IN ('lost', 'found')) NOT NULL,
    status TEXT CHECK(status IN ('active', 'resolved')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);