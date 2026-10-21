#!/bin/bash
# Database setup script

echo "Creating PostgreSQL user and database..."
sudo -u postgres psql << EOF
CREATE USER universe WITH PASSWORD 'universe_secure_pass_2026';
CREATE DATABASE universe_of_ilm OWNER universe;
GRANT ALL PRIVILEGES ON DATABASE universe_of_ilm TO universe;
EOF

echo "Database setup complete!"
