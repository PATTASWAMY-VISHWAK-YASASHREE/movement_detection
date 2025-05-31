#!/usr/bin/env python3
"""
Database Configuration for Motion Detection Security System

Contains database connection settings and utility functions.
"""

import os
from typing import Optional

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',  # Default database
    'user': 'postgres',
    'password': 'vishwak'
}

# Table names
TABLES = {
    'alerts': 'motion_alerts',
    'images': 'alert_images',
    'settings': 'system_settings'
}

def get_connection_string():
    """Get PostgreSQL connection string"""
    return f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

def get_psycopg2_params():
    """Get connection parameters for psycopg2"""
    return {
        'host': DB_CONFIG['host'],
        'port': DB_CONFIG['port'],
        'database': DB_CONFIG['database'],
        'user': DB_CONFIG['user'],
        'password': DB_CONFIG['password']
    }
