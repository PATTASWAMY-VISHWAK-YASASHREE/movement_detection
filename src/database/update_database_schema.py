#!/usr/bin/env python3
"""
Database Update Script for Wireless Camera Support

Adds camera_source and motion_confidence columns to the motion_alerts table
for wireless camera integration.
"""

import psycopg2
from database_config import get_psycopg2_params, TABLES

def update_database_schema():
    """Update database schema to support wireless camera features"""
    
    # SQL statements to add new columns
    update_sql = f"""
    -- Add camera_source column if it doesn't exist
    DO $$ 
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = '{TABLES['alerts']}' 
            AND column_name = 'camera_source'
        ) THEN
            ALTER TABLE {TABLES['alerts']} 
            ADD COLUMN camera_source VARCHAR(100) DEFAULT 'webcam';
            
            COMMENT ON COLUMN {TABLES['alerts']}.camera_source IS 'Source camera identifier (webcam, mobile, wireless-device_id, etc.)';
        END IF;
    END $$;

    -- Add motion_confidence column if it doesn't exist  
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = '{TABLES['alerts']}' 
            AND column_name = 'motion_confidence'
        ) THEN
            ALTER TABLE {TABLES['alerts']} 
            ADD COLUMN motion_confidence DECIMAL(3,2) DEFAULT 0.80;
            
            COMMENT ON COLUMN {TABLES['alerts']}.motion_confidence IS 'Motion detection confidence score (0.00 to 1.00)';
        END IF;
    END $$;

    -- Create index on camera_source for better performance
    CREATE INDEX IF NOT EXISTS idx_alerts_camera_source ON {TABLES['alerts']}(camera_source);
    
    -- Update existing records to have default camera_source
    UPDATE {TABLES['alerts']} 
    SET camera_source = 'webcam' 
    WHERE camera_source IS NULL;
    """

    try:
        # Connect to PostgreSQL
        print("🔗 Connecting to PostgreSQL...")
        conn = psycopg2.connect(**get_psycopg2_params())
        cursor = conn.cursor()

        print("📝 Updating database schema for wireless camera support...")
        cursor.execute(update_sql)
        conn.commit()

        print("✅ Database schema updated successfully!")
        print("📋 Added columns:")
        print("   • camera_source (VARCHAR): Source camera identifier")
        print("   • motion_confidence (DECIMAL): Motion detection confidence")
        
        # Verify the changes
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = '{TABLES['alerts']}' 
            AND column_name IN ('camera_source', 'motion_confidence')
            ORDER BY column_name;
        """)
        
        columns = cursor.fetchall()
        if columns:
            print("\n📊 Column verification:")
            for col_name, data_type, nullable, default in columns:
                print(f"   • {col_name}: {data_type} (nullable: {nullable}, default: {default})")
        
        cursor.close()
        conn.close()
        
        return True

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main update function"""
    print("🔧 Database Schema Update for Wireless Camera Support")
    print("=" * 60)
    
    if update_database_schema():
        print("\n🎉 Database update completed successfully!")
        print("💡 The wireless camera server can now save alerts to the database")
    else:
        print("\n❌ Database update failed!")
        print("💡 Please check the error messages above")

if __name__ == "__main__":
    main()
