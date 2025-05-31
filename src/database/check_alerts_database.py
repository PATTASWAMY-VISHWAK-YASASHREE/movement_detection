#!/usr/bin/env python3
"""
Database Alert Checker

This script connects to the PostgreSQL database and shows all motion alerts
to verify that wireless camera alerts are being saved properly.
"""

import psycopg2
from datetime import datetime
from database_config import get_psycopg2_params, TABLES

def check_alerts_database():
    """Check and display all motion alerts from database"""
    
    try:
        # Connect to PostgreSQL
        print("🔗 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**get_psycopg2_params())
        cursor = conn.cursor()
        
        # Check if motion_alerts table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (TABLES['alerts'],))
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print(f"❌ Table '{TABLES['alerts']}' does not exist!")
            return False
        
        print(f"✅ Table '{TABLES['alerts']}' found!")
        
        # Get table structure
        print(f"\n📋 Table Structure:")
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = '{TABLES['alerts']}'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        for col_name, data_type, nullable, default in columns:
            print(f"   • {col_name}: {data_type} (nullable: {nullable})")
        
        # Count total alerts
        cursor.execute(f"SELECT COUNT(*) FROM {TABLES['alerts']};")
        total_count = cursor.fetchone()[0]
        print(f"\n📊 Total Motion Alerts: {total_count}")
        
        if total_count == 0:
            print("ℹ️  No alerts found in database")
            return True
          # Show recent alerts (last 20)
        print(f"\n🕐 Recent Motion Alerts (Last 20):")
        cursor.execute(f"""
            SELECT 
                id,
                timestamp,
                camera_source,
                motion_confidence,
                image_path,
                created_at
            FROM {TABLES['alerts']} 
            ORDER BY timestamp DESC 
            LIMIT 20;
        """)
        
        alerts = cursor.fetchall()
        
        if alerts:
            print("=" * 120)
            print(f"{'ID':<5} {'Timestamp':<20} {'Camera Source':<20} {'Confidence':<12} {'Image Path':<40} {'Created At':<20}")
            print("=" * 120)
            
            for alert in alerts:
                alert_id, timestamp, camera_source, confidence, image_path, created_at = alert
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A"
                created_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "N/A"
                camera_source = camera_source or "unknown"
                confidence = f"{confidence:.2f}" if confidence else "N/A"
                image_path = image_path or "N/A"
                
                print(f"{alert_id:<5} {timestamp_str:<20} {camera_source:<20} {confidence:<12} {image_path:<40} {created_str:<20}")
        
        # Show wireless camera specific alerts
        print(f"\n📱 Wireless Camera Alerts:")
        cursor.execute(f"""
            SELECT 
                COUNT(*) as count,
                camera_source,
                MIN(timestamp) as first_alert,
                MAX(timestamp) as last_alert,
                AVG(motion_confidence) as avg_confidence
            FROM {TABLES['alerts']} 
            WHERE camera_source LIKE 'wireless-%'
            GROUP BY camera_source
            ORDER BY last_alert DESC;
        """)
        
        wireless_alerts = cursor.fetchall()
        
        if wireless_alerts:
            print("=" * 100)
            print(f"{'Camera Source':<25} {'Count':<8} {'First Alert':<20} {'Last Alert':<20} {'Avg Confidence':<15}")
            print("=" * 100)
            
            for count, camera_source, first_alert, last_alert, avg_confidence in wireless_alerts:
                first_str = first_alert.strftime("%Y-%m-%d %H:%M:%S") if first_alert else "N/A"
                last_str = last_alert.strftime("%Y-%m-%d %H:%M:%S") if last_alert else "N/A"
                avg_conf = f"{avg_confidence:.3f}" if avg_confidence else "N/A"
                
                print(f"{camera_source:<25} {count:<8} {first_str:<20} {last_str:<20} {avg_conf:<15}")
        else:
            print("ℹ️  No wireless camera alerts found")
          # Show alerts from last hour
        print(f"\n⏰ Alerts from Last Hour:")
        cursor.execute(f"""
            SELECT 
                id,
                timestamp,
                camera_source,
                motion_confidence,
                image_path
            FROM {TABLES['alerts']} 
            WHERE timestamp >= NOW() - INTERVAL '1 hour'
            ORDER BY timestamp DESC;
        """)
        recent_alerts = cursor.fetchall()
        
        if recent_alerts:
            print(f"Found {len(recent_alerts)} alerts in the last hour:")
            for alert in recent_alerts:
                alert_id, timestamp, camera_source, confidence, image_path = alert
                timestamp_str = timestamp.strftime("%H:%M:%S") if timestamp else "N/A"
                confidence_str = f"{confidence:.2f}" if confidence else "N/A"
                print(f"   • #{alert_id} at {timestamp_str} from {camera_source} (confidence: {confidence_str})")
        else:
            print("ℹ️  No alerts in the last hour")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Database check completed successfully!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Motion Detection Alert Database Checker")
    print("=" * 60)
    check_alerts_database()

if __name__ == "__main__":
    main()
