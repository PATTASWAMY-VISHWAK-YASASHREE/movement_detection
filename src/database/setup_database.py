#!/usr/bin/env python3
"""
Database Setup Script for Motion Detection Security System

Creates the necessary tables and indexes for storing alert images and metadata.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from database_config import get_psycopg2_params, TABLES

def create_database_schema():
    """Create database tables and indexes"""
    
    # SQL statements to create tables
    create_tables_sql = f"""
    -- Create motion_alerts table
    CREATE TABLE IF NOT EXISTS {TABLES['alerts']} (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        motion_areas_count INTEGER NOT NULL DEFAULT 0,
        sensitivity INTEGER NOT NULL DEFAULT 50,
        detection_type VARCHAR(50) DEFAULT 'motion',
        objects_detected JSONB DEFAULT '[]'::jsonb,
        confidence_scores JSONB DEFAULT '{{}}'::jsonb,
        frame_saved BOOLEAN DEFAULT FALSE,
        image_path TEXT,
        notes TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Create alert_images table  
    CREATE TABLE IF NOT EXISTS {TABLES['images']} (
        id SERIAL PRIMARY KEY,
        alert_id INTEGER REFERENCES {TABLES['alerts']}(id) ON DELETE CASCADE,
        image_name VARCHAR(255) NOT NULL,
        image_data TEXT NOT NULL,  -- Base64 encoded image
        image_type VARCHAR(10) DEFAULT 'jpg',
        file_size INTEGER,
        width INTEGER,
        height INTEGER,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Create system_settings table
    CREATE TABLE IF NOT EXISTS {TABLES['settings']} (
        id SERIAL PRIMARY KEY,
        setting_key VARCHAR(100) UNIQUE NOT NULL,
        setting_value TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON {TABLES['alerts']}(timestamp);
    CREATE INDEX IF NOT EXISTS idx_alerts_detection_type ON {TABLES['alerts']}(detection_type);
    CREATE INDEX IF NOT EXISTS idx_images_alert_id ON {TABLES['images']}(alert_id);
    CREATE INDEX IF NOT EXISTS idx_images_created_at ON {TABLES['images']}(created_at);
    CREATE INDEX IF NOT EXISTS idx_settings_key ON {TABLES['settings']}(setting_key);

    -- Create trigger to update updated_at timestamp
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    CREATE TRIGGER update_alerts_updated_at 
        BEFORE UPDATE ON {TABLES['alerts']}
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

    CREATE TRIGGER update_settings_updated_at 
        BEFORE UPDATE ON {TABLES['settings']}
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """

    try:
        # Connect to PostgreSQL
        print("🔗 Connecting to PostgreSQL...")
        conn = psycopg2.connect(**get_psycopg2_params())
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        print("📝 Creating database schema...")
        cursor.execute(create_tables_sql)

        # Insert default settings
        default_settings = [
            ('auto_cleanup_days', '30', 'Number of days to keep old alert data'),
            ('max_images_per_day', '1000', 'Maximum number of images to store per day'),
            ('image_quality', '85', 'JPEG compression quality (1-100)'),
            ('enable_web_viewer', 'true', 'Enable web viewer interface'),
            ('web_viewer_port', '5000', 'Port for web viewer application')
        ]

        for key, value, description in default_settings:
            cursor.execute(f"""
                INSERT INTO {TABLES['settings']} (setting_key, setting_value, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (setting_key) DO NOTHING
            """, (key, value, description))

        print("✅ Database schema created successfully!")
        print("\n📊 Created tables:")
        print(f"  • {TABLES['alerts']} - Motion alert metadata")
        print(f"  • {TABLES['images']} - Base64 encoded images")
        print(f"  • {TABLES['settings']} - System configuration")

        # Show table info
        cursor.execute("""
            SELECT table_name, 
                   (SELECT count(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t 
            WHERE table_schema = 'public' 
            AND table_name IN %s
        """, (tuple(TABLES.values()),))
        
        tables_info = cursor.fetchall()
        print("\n📋 Table details:")
        for table_name, column_count in tables_info:
            print(f"  • {table_name}: {column_count} columns")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_database_connection():
    """Test database connection and show system info"""
    try:
        print("🧪 Testing database connection...")
        conn = psycopg2.connect(**get_psycopg2_params())
        cursor = conn.cursor()

        # Get PostgreSQL version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to: {version}")

        # Check if tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN %s
        """, (tuple(TABLES.values()),))
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Existing tables: {len(existing_tables)}/{len(TABLES)}")
        
        for table in TABLES.values():
            status = "✅" if table in existing_tables else "❌"
            print(f"  {status} {table}")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Motion Detection Database...")
    print("=" * 50)
    
    # Test connection first
    if not test_database_connection():
        print("💡 Please check your database configuration in database_config.py")
        return
    
    print("\n" + "=" * 50)
    
    # Create schema
    if create_database_schema():
        print("\n🎉 Database setup completed successfully!")
        print("\n📝 Next steps:")
        print("  1. Run 'python image_processor.py' to process existing alert images")
        print("  2. Run 'python web_viewer.py' to start the web interface")
        print("  3. Visit http://localhost:5000 to view your alerts")
    else:
        print("\n❌ Database setup failed!")

if __name__ == "__main__":
    main()
