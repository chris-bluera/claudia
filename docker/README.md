# Docker Directory

This directory contains Docker-related runtime data.

## Structure

```
docker/
├── data/           # Runtime data volumes (gitignored)
│   └── postgres/   # PostgreSQL database files
└── README.md       # This file
```

## Purpose

- **data/** - Contains persistent data for Docker containers. This is gitignored as it contains runtime database files, not source code.

## Note

The actual database schema/initialization SQL is in `/database/init.sql`.
This `/docker/data/` directory only contains the runtime PostgreSQL data files created when the database runs.