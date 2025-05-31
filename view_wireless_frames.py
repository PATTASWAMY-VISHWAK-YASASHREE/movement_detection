#!/usr/bin/env python3
"""
Wireless Camera Frame Viewer

This tool extracts wireless camera frames from the database and saves them
to the recordings/alerts directory for viewing.
"""

import os
import base64
import psycopg2
from datetime import datetime, timedelta
from pathlib import Path
from database_config import get_psycopg2_params, TABLES

def extract_wireless_frames(limit=50, hours=1):
    """Extract wireless camera frames from database and save as image files"""
    
    # Create output directory
    output_dir = Path("recordings/alerts/wireless")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    try:
        # Connect to PostgreSQL
        print("🔗 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**get_psycopg2_params())
        cursor = conn.cursor()
        
        # Find wireless alerts with images
        print(f"🔍 Searching for wireless camera alerts in the last {hours} hours...")
        cursor.execute(f"""
            SELECT a.id, a.timestamp, a.camera_source, a.motion_confidence, 
                   i.image_data, i.image_name, i.file_size
            FROM {TABLES['alerts']} a
            JOIN {TABLES['images']} i ON a.id = i.alert_id
            WHERE a.camera_source LIKE 'wireless-%'
              AND a.timestamp >= NOW() - INTERVAL '{hours} hours'
            ORDER BY a.timestamp DESC
            LIMIT {limit}
        """)
        
        results = cursor.fetchall()
        
        if not results:
            # Try without the time filter if no recent results
            print("📅 No recent wireless frames found, searching for any wireless frames...")
            cursor.execute(f"""
                SELECT a.id, a.timestamp, a.camera_source, a.motion_confidence, 
                       i.image_data, i.image_name, i.file_size
                FROM {TABLES['alerts']} a
                JOIN {TABLES['images']} i ON a.id = i.alert_id
                WHERE a.camera_source LIKE 'wireless-%'
                ORDER BY a.timestamp DESC
                LIMIT {limit}
            """)
            results = cursor.fetchall()
        
        if not results:
            print("❌ No wireless camera frames found in database")
            
            # Try finding all alerts without the images joined
            print("🔍 Checking for wireless alerts without images...")
            cursor.execute(f"""
                SELECT id, timestamp, camera_source, motion_confidence
                FROM {TABLES['alerts']}
                WHERE camera_source LIKE 'wireless-%'
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            alerts_only = cursor.fetchall()
            
            if alerts_only:
                print(f"📊 Found {len(alerts_only)} wireless alerts in database, but no images attached")
                for alert_id, timestamp, camera_source, confidence in alerts_only:
                    print(f"  • Alert #{alert_id} at {timestamp}, Source: {camera_source}, Confidence: {confidence:.2f}")
                print("\n⚠️ The 'save_alert_with_image' function is saving alerts but not properly linking images.")
                
            return False
        
        print(f"📸 Found {len(results)} wireless camera frames in database")
        
        # Save each image
        saved_count = 0
        for alert_id, timestamp, camera_source, confidence, image_data, image_name, file_size in results:
            try:
                # Clean up device_id for filename
                device_id = camera_source.replace('wireless-', '').replace(':', '_')
                
                # Create filename
                timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
                outfile = output_dir / f"{device_id}_{timestamp_str}_{alert_id}.jpg"
                
                # Save image
                image_bytes = base64.b64decode(image_data)
                with open(outfile, 'wb') as f:
                    f.write(image_bytes)
                
                saved_count += 1
                print(f"✅ Saved: {outfile.name} ({file_size/1024:.1f} KB)")
                
            except Exception as e:
                print(f"❌ Error saving image {alert_id}: {e}")
        
        cursor.close()
        conn.close()
        
        if saved_count > 0:
            print(f"\n🎉 Successfully saved {saved_count} wireless camera frames to {output_dir}")
            print(f"📷 You can now view the frames in: {output_dir.absolute()}")
            return True
        else:
            print("❌ No frames could be saved")
            return False
            
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("📱 Wireless Camera Frame Extractor")
    print("=" * 60)
    
    # Get user input for time range
    hours = input("Enter number of hours to search (default: 1): ")
    hours = int(hours) if hours and hours.isdigit() else 1
    
    limit = input("Maximum number of frames to extract (default: 20): ")
    limit = int(limit) if limit and limit.isdigit() else 20
    
    success = extract_wireless_frames(limit=limit, hours=hours)
    
    if success:
        print("\n🖼️ Opening frames directory...")
        os.system(f'start {os.path.normpath(os.path.join(os.getcwd(), "recordings", "alerts", "wireless"))}')

if __name__ == "__main__":
    main()
