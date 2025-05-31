#!/usr/bin/env python3
"""
Database Utilities for Motion Detection Security System

Helper functions for database operations, maintenance, and data export.
"""

import base64
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import psycopg2
from PIL import Image
from io import BytesIO
from database_config import get_psycopg2_params, TABLES

class DatabaseUtils:
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**get_psycopg2_params())
            self.cursor = self.conn.cursor()
            return True
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def base64_to_image(self, base64_string: str, output_path: str) -> bool:
        """
        Convert Base64 string back to image file
        """
        try:
            # Decode Base64 string
            image_data = base64.b64decode(base64_string)
            
            # Save to file
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            return True
        except Exception as e:
            print(f"❌ Error converting Base64 to image: {e}")
            return False
    
    def export_images(self, output_dir: str = "exported_images", limit: int = None):
        """Export all images from database back to files"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # Get images with alert info
            query = f"""
                SELECT 
                    i.id,
                    i.image_name,
                    i.image_data,
                    i.image_type,
                    a.timestamp,
                    a.detection_type
                FROM {TABLES['images']} i
                JOIN {TABLES['alerts']} a ON i.alert_id = a.id
                ORDER BY a.timestamp DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            self.cursor.execute(query)
            images = self.cursor.fetchall()
            
            print(f"🔄 Exporting {len(images)} images to {output_dir}...")
            
            exported_count = 0
            for img in images:
                img_id, img_name, img_data, img_type, timestamp, detection_type = img
                
                # Create filename with timestamp and type
                timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S") if timestamp else "unknown"
                filename = f"{detection_type}_{timestamp_str}_{img_id}.{img_type}"
                file_path = output_path / filename
                
                if self.base64_to_image(img_data, str(file_path)):
                    exported_count += 1
                    if exported_count % 10 == 0:
                        print(f"  ✅ Exported {exported_count}/{len(images)} images")
            
            print(f"🎉 Successfully exported {exported_count} images to {output_dir}")
            return exported_count
            
        except psycopg2.Error as e:
            print(f"❌ Database error: {e}")
            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return 0
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove data older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Get count of records to be deleted
            self.cursor.execute(f"""
                SELECT COUNT(*) FROM {TABLES['alerts']} 
                WHERE timestamp < %s
            """, (cutoff_date,))
            alert_count = self.cursor.fetchone()[0]
            
            self.cursor.execute(f"""
                SELECT COUNT(*) FROM {TABLES['images']} i
                JOIN {TABLES['alerts']} a ON i.alert_id = a.id
                WHERE a.timestamp < %s
            """, (cutoff_date,))
            image_count = self.cursor.fetchone()[0]
            
            if alert_count == 0:
                print(f"✅ No data older than {days_to_keep} days found")
                return
            
            print(f"⚠️ Found {alert_count} alerts and {image_count} images older than {days_to_keep} days")
            confirm = input("❓ Do you want to delete this data? (y/N): ")
            
            if confirm.lower() != 'y':
                print("❌ Cleanup cancelled")
                return
            
            # Delete old records (images will be deleted automatically due to CASCADE)
            self.cursor.execute(f"""
                DELETE FROM {TABLES['alerts']} 
                WHERE timestamp < %s
            """, (cutoff_date,))
            
            deleted_count = self.cursor.rowcount
            self.conn.commit()
            
            print(f"✅ Deleted {deleted_count} old alert records and associated images")
            
        except psycopg2.Error as e:
            print(f"❌ Database error: {e}")
            self.conn.rollback()
    
    def get_detailed_statistics(self):
        """Get detailed database statistics"""
        try:
            stats = {}
            
            # Basic counts
            self.cursor.execute(f"SELECT COUNT(*) FROM {TABLES['alerts']}")
            stats['total_alerts'] = self.cursor.fetchone()[0]
            
            self.cursor.execute(f"SELECT COUNT(*) FROM {TABLES['images']}")
            stats['total_images'] = self.cursor.fetchone()[0]
            
            # Storage information
            self.cursor.execute(f"""
                SELECT 
                    SUM(file_size) as total_size,
                    AVG(file_size) as avg_size,
                    MIN(file_size) as min_size,
                    MAX(file_size) as max_size
                FROM {TABLES['images']}
            """)
            size_stats = self.cursor.fetchone()
            if size_stats[0]:
                stats['storage'] = {
                    'total_mb': round(size_stats[0] / (1024 * 1024), 2),
                    'avg_kb': round(size_stats[1] / 1024, 2),
                    'min_kb': round(size_stats[2] / 1024, 2),
                    'max_kb': round(size_stats[3] / 1024, 2)
                }
            
            # Image dimensions
            self.cursor.execute(f"""
                SELECT 
                    AVG(width) as avg_width,
                    AVG(height) as avg_height,
                    MAX(width) as max_width,
                    MAX(height) as max_height
                FROM {TABLES['images']}
                WHERE width IS NOT NULL AND height IS NOT NULL
            """)
            dim_stats = self.cursor.fetchone()
            if dim_stats[0]:
                stats['dimensions'] = {
                    'avg_width': int(dim_stats[0]),
                    'avg_height': int(dim_stats[1]),
                    'max_width': dim_stats[2],
                    'max_height': dim_stats[3]
                }
            
            # Detection types
            self.cursor.execute(f"""
                SELECT detection_type, COUNT(*) 
                FROM {TABLES['alerts']} 
                GROUP BY detection_type 
                ORDER BY COUNT(*) DESC
            """)
            stats['detection_types'] = dict(self.cursor.fetchall())
            
            # Activity by hour
            self.cursor.execute(f"""
                SELECT EXTRACT(HOUR FROM timestamp) as hour, COUNT(*) 
                FROM {TABLES['alerts']} 
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY EXTRACT(HOUR FROM timestamp) 
                ORDER BY hour
            """)
            stats['hourly_activity'] = dict(self.cursor.fetchall())
            
            # Recent activity
            self.cursor.execute(f"""
                SELECT 
                    DATE(timestamp) as date, 
                    COUNT(*) as count
                FROM {TABLES['alerts']} 
                WHERE timestamp >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(timestamp) 
                ORDER BY date DESC
                LIMIT 10
            """)
            stats['daily_activity'] = [(date.strftime('%Y-%m-%d'), count) 
                                     for date, count in self.cursor.fetchall()]
            
            # Date range
            self.cursor.execute(f"""
                SELECT MIN(timestamp), MAX(timestamp) 
                FROM {TABLES['alerts']}
            """)
            date_range = self.cursor.fetchone()
            if date_range[0]:
                stats['date_range'] = {
                    'first': date_range[0].strftime('%Y-%m-%d %H:%M:%S'),
                    'last': date_range[1].strftime('%Y-%m-%d %H:%M:%S'),
                    'days': (date_range[1] - date_range[0]).days + 1
                }
            
            return stats
            
        except psycopg2.Error as e:
            print(f"❌ Database error: {e}")
            return {}
    
    def backup_database_to_json(self, output_file: str = None):
        """Export all data to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"motion_detection_backup_{timestamp}.json"
        
        try:
            backup_data = {
                'export_timestamp': datetime.now().isoformat(),
                'alerts': [],
                'images': [],
                'settings': []
            }
            
            # Export alerts
            self.cursor.execute(f"""
                SELECT id, timestamp, detection_type, motion_areas_count, 
                       sensitivity, objects_detected, confidence_scores, 
                       frame_saved, image_path, notes, created_at, updated_at
                FROM {TABLES['alerts']} 
                ORDER BY timestamp
            """)
            
            for row in self.cursor.fetchall():
                backup_data['alerts'].append({
                    'id': row[0],
                    'timestamp': row[1].isoformat() if row[1] else None,
                    'detection_type': row[2],
                    'motion_areas_count': row[3],
                    'sensitivity': row[4],
                    'objects_detected': row[5],
                    'confidence_scores': row[6],
                    'frame_saved': row[7],
                    'image_path': row[8],
                    'notes': row[9],
                    'created_at': row[10].isoformat() if row[10] else None,
                    'updated_at': row[11].isoformat() if row[11] else None
                })
            
            # Export images (without base64 data to reduce file size)
            self.cursor.execute(f"""
                SELECT id, alert_id, image_name, image_type, 
                       file_size, width, height, created_at
                FROM {TABLES['images']} 
                ORDER BY created_at
            """)
            
            for row in self.cursor.fetchall():
                backup_data['images'].append({
                    'id': row[0],
                    'alert_id': row[1],
                    'image_name': row[2],
                    'image_type': row[3],
                    'file_size': row[4],
                    'width': row[5],
                    'height': row[6],
                    'created_at': row[7].isoformat() if row[7] else None
                })
            
            # Export settings
            self.cursor.execute(f"""
                SELECT setting_key, setting_value, description, 
                       created_at, updated_at
                FROM {TABLES['settings']} 
                ORDER BY setting_key
            """)
            
            for row in self.cursor.fetchall():
                backup_data['settings'].append({
                    'setting_key': row[0],
                    'setting_value': row[1],
                    'description': row[2],
                    'created_at': row[3].isoformat() if row[3] else None,
                    'updated_at': row[4].isoformat() if row[4] else None
                })
            
            # Write to file
            with open(output_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            file_size = os.path.getsize(output_file) / (1024 * 1024)
            print(f"✅ Database backup saved to {output_file} ({file_size:.2f} MB)")
            print(f"📊 Exported {len(backup_data['alerts'])} alerts, {len(backup_data['images'])} images")
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")

def main():
    """Main utility function"""
    print("🛠️ Motion Detection Database Utilities")
    print("=" * 50)
    
    utils = DatabaseUtils()
    
    if not utils.connect():
        return
    
    try:
        while True:
            print("\n📋 Available operations:")
            print("1. 📊 Show detailed statistics")
            print("2. 📤 Export images to files")
            print("3. 🧹 Cleanup old data")
            print("4. 💾 Backup database to JSON")
            print("5. 🔄 Convert Base64 string to image")
            print("6. ❌ Exit")
            
            choice = input("\n🤔 Choose an option (1-6): ").strip()
            
            if choice == '1':
                print("\n📊 Getting detailed statistics...")
                stats = utils.get_detailed_statistics()
                
                print("\n" + "=" * 50)
                print("📊 DATABASE STATISTICS")
                print("=" * 50)
                print(f"Total Alerts: {stats.get('total_alerts', 0)}")
                print(f"Total Images: {stats.get('total_images', 0)}")
                
                if 'storage' in stats:
                    storage = stats['storage']
                    print(f"\n💾 Storage Information:")
                    print(f"  Total Size: {storage['total_mb']} MB")
                    print(f"  Average Image: {storage['avg_kb']} KB")
                    print(f"  Size Range: {storage['min_kb']} - {storage['max_kb']} KB")
                
                if 'dimensions' in stats:
                    dim = stats['dimensions']
                    print(f"\n📐 Image Dimensions:")
                    print(f"  Average: {dim['avg_width']}x{dim['avg_height']}")
                    print(f"  Maximum: {dim['max_width']}x{dim['max_height']}")
                
                if stats.get('detection_types'):
                    print(f"\n🔍 Detection Types:")
                    for dtype, count in stats['detection_types'].items():
                        print(f"  • {dtype}: {count}")
                
                if stats.get('date_range'):
                    dr = stats['date_range']
                    print(f"\n📅 Date Range:")
                    print(f"  First Alert: {dr['first']}")
                    print(f"  Last Alert: {dr['last']}")
                    print(f"  Total Days: {dr['days']}")
            
            elif choice == '2':
                limit_input = input("📝 Limit number of images (press Enter for all): ").strip()
                limit = int(limit_input) if limit_input.isdigit() else None
                output_dir = input("📁 Output directory (default: exported_images): ").strip() or "exported_images"
                
                exported = utils.export_images(output_dir, limit)
                print(f"✅ Exported {exported} images")
            
            elif choice == '3':
                days_input = input("📅 Keep data for how many days? (default: 30): ").strip()
                days = int(days_input) if days_input.isdigit() else 30
                utils.cleanup_old_data(days)
            
            elif choice == '4':
                filename = input("📝 Backup filename (press Enter for auto): ").strip()
                utils.backup_database_to_json(filename or None)
            
            elif choice == '5':
                base64_input = input("📝 Enter Base64 string (or file path with @): ").strip()
                if base64_input.startswith('@'):
                    # Read from file
                    file_path = base64_input[1:]
                    try:
                        with open(file_path, 'r') as f:
                            base64_string = f.read().strip()
                    except Exception as e:
                        print(f"❌ Error reading file: {e}")
                        continue
                else:
                    base64_string = base64_input
                
                output_path = input("📁 Output image path (e.g., output.jpg): ").strip()
                if not output_path:
                    output_path = f"converted_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                
                if utils.base64_to_image(base64_string, output_path):
                    print(f"✅ Image saved to {output_path}")
                else:
                    print("❌ Failed to convert image")
            
            elif choice == '6':
                break
            
            else:
                print("❌ Invalid choice. Please try again.")
    
    finally:
        utils.close()

if __name__ == "__main__":
    main()
