#!/usr/bin/env python3
"""
Image Processor for Motion Detection Security System

Processes existing alert images, converts them to Base64 strings,
and stores them in the PostgreSQL database.
"""

import os
import base64
import json
from datetime import datetime
from pathlib import Path
from PIL import Image
import psycopg2
from database_config import get_psycopg2_params, TABLES

class ImageProcessor:
    def __init__(self):
        self.alerts_dir = Path("recordings/alerts")
        self.processed_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**get_psycopg2_params())
            self.cursor = self.conn.cursor()
            return True
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def close_db(self):
        """Close database connection"""
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def image_to_base64(self, image_path: Path) -> tuple:
        """
        Convert image to Base64 string
        Returns: (base64_string, file_size, width, height)
        """
        try:
            # Read image file
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                base64_string = base64.b64encode(img_data).decode('utf-8')
            
            # Get image dimensions
            with Image.open(image_path) as img:
                width, height = img.size
            
            file_size = len(img_data)
            return base64_string, file_size, width, height
            
        except Exception as e:
            print(f"❌ Error processing image {image_path}: {e}")
            return None, None, None, None
    
    def parse_filename(self, filename: str) -> dict:
        """
        Parse filename to extract metadata
        Format: motion_alert_YYYYMMDD_HHMMSS.jpg or manual_save_YYYYMMDD_HHMMSS.jpg
        """
        try:
            name_part = filename.replace('.jpg', '').replace('.jpeg', '').replace('.png', '')
            parts = name_part.split('_')
            
            if len(parts) >= 3:
                detection_type = parts[0] + '_' + parts[1]  # motion_alert or manual_save
                date_str = parts[2]
                time_str = parts[3] if len(parts) > 3 else "000000"
                
                # Parse datetime
                datetime_str = f"{date_str}_{time_str}"
                timestamp = datetime.strptime(datetime_str, "%Y%m%d_%H%M%S")
                
                return {
                    'detection_type': detection_type,
                    'timestamp': timestamp,
                    'original_filename': filename
                }
        except Exception as e:
            print(f"⚠️ Could not parse filename {filename}: {e}")
        
        # Fallback to file modification time
        return {
            'detection_type': 'unknown',
            'timestamp': datetime.now(),
            'original_filename': filename
        }
    
    def insert_alert_record(self, metadata: dict) -> int:
        """Insert alert record and return alert_id"""
        try:
            # Check if alert already exists
            self.cursor.execute(f"""
                SELECT id FROM {TABLES['alerts']} 
                WHERE timestamp = %s AND detection_type = %s
            """, (metadata['timestamp'], metadata['detection_type']))
            
            existing = self.cursor.fetchone()
            if existing:
                return existing[0]
            
            # Insert new alert record
            self.cursor.execute(f"""
                INSERT INTO {TABLES['alerts']} 
                (timestamp, detection_type, frame_saved, motion_areas_count, sensitivity)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                metadata['timestamp'],
                metadata['detection_type'],
                True,
                1,  # Default motion areas count
                50  # Default sensitivity
            ))
            
            alert_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return alert_id
            
        except psycopg2.Error as e:
            print(f"❌ Database error inserting alert: {e}")
            self.conn.rollback()
            return None
    
    def insert_image_record(self, alert_id: int, image_data: dict, metadata: dict):
        """Insert image record"""
        try:
            # Check if image already exists
            self.cursor.execute(f"""
                SELECT id FROM {TABLES['images']} 
                WHERE alert_id = %s AND image_name = %s
            """, (alert_id, metadata['original_filename']))
            
            if self.cursor.fetchone():
                self.skipped_count += 1
                print(f"⏭️ Skipped (already exists): {metadata['original_filename']}")
                return True
            
            # Insert image record
            self.cursor.execute(f"""
                INSERT INTO {TABLES['images']} 
                (alert_id, image_name, image_data, image_type, file_size, width, height)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                alert_id,
                metadata['original_filename'],
                image_data['base64_string'],
                image_data['image_type'],
                image_data['file_size'],
                image_data['width'],
                image_data['height']
            ))
            
            self.conn.commit()
            self.processed_count += 1
            print(f"✅ Processed: {metadata['original_filename']}")
            return True
            
        except psycopg2.Error as e:
            print(f"❌ Database error inserting image: {e}")
            self.conn.rollback()
            self.error_count += 1
            return False
    
    def process_image(self, image_path: Path):
        """Process a single image file"""
        try:
            # Parse filename for metadata
            metadata = self.parse_filename(image_path.name)
            
            # Convert image to Base64
            base64_string, file_size, width, height = self.image_to_base64(image_path)
            if base64_string is None:
                self.error_count += 1
                return
            
            # Determine image type
            image_type = image_path.suffix.lower().replace('.', '')
            if image_type not in ['jpg', 'jpeg', 'png']:
                image_type = 'jpg'
            
            image_data = {
                'base64_string': base64_string,
                'file_size': file_size,
                'width': width,
                'height': height,
                'image_type': image_type
            }
            
            # Insert alert record
            alert_id = self.insert_alert_record(metadata)
            if alert_id is None:
                self.error_count += 1
                return
            
            # Insert image record
            self.insert_image_record(alert_id, image_data, metadata)
            
        except Exception as e:
            print(f"❌ Error processing {image_path}: {e}")
            self.error_count += 1
    
    def process_all_images(self):
        """Process all images in the alerts directory"""
        if not self.alerts_dir.exists():
            print(f"❌ Alerts directory not found: {self.alerts_dir}")
            return
        
        # Get all image files
        image_extensions = ['.jpg', '.jpeg', '.png']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(self.alerts_dir.glob(f'*{ext}'))
            image_files.extend(self.alerts_dir.glob(f'*{ext.upper()}'))
        
        if not image_files:
            print(f"📁 No image files found in {self.alerts_dir}")
            return
        
        print(f"📁 Found {len(image_files)} image files to process")
        print("🔄 Processing images...")
        
        for image_path in sorted(image_files):
            self.process_image(image_path)
        
        # Show summary
        total = len(image_files)
        print("\n" + "=" * 50)
        print("📊 PROCESSING SUMMARY")
        print("=" * 50)
        print(f"Total files found: {total}")
        print(f"✅ Successfully processed: {self.processed_count}")
        print(f"⏭️ Skipped (already in DB): {self.skipped_count}")
        print(f"❌ Errors: {self.error_count}")
        print(f"📈 Success rate: {(self.processed_count / total * 100):.1f}%" if total > 0 else "0%")
    
    def show_database_stats(self):
        """Show database statistics"""
        try:
            # Count records in each table
            self.cursor.execute(f"SELECT COUNT(*) FROM {TABLES['alerts']}")
            alert_count = self.cursor.fetchone()[0]
            
            self.cursor.execute(f"SELECT COUNT(*) FROM {TABLES['images']}")
            image_count = self.cursor.fetchone()[0]
            
            # Get total size of images
            self.cursor.execute(f"SELECT SUM(file_size) FROM {TABLES['images']}")
            total_size = self.cursor.fetchone()[0] or 0
            
            # Get date range
            self.cursor.execute(f"""
                SELECT MIN(timestamp), MAX(timestamp) 
                FROM {TABLES['alerts']} 
                WHERE timestamp IS NOT NULL
            """)
            date_range = self.cursor.fetchone()
            
            print("\n" + "=" * 50)
            print("📊 DATABASE STATISTICS")
            print("=" * 50)
            print(f"Alert records: {alert_count}")
            print(f"Image records: {image_count}")
            print(f"Total image size: {total_size / (1024*1024):.2f} MB")
            
            if date_range[0] and date_range[1]:
                print(f"Date range: {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}")
            
            # Show recent alerts
            self.cursor.execute(f"""
                SELECT detection_type, COUNT(*) 
                FROM {TABLES['alerts']} 
                GROUP BY detection_type 
                ORDER BY COUNT(*) DESC
            """)
            alert_types = self.cursor.fetchall()
            
            if alert_types:
                print("\nAlert types:")
                for alert_type, count in alert_types:
                    print(f"  • {alert_type}: {count}")
            
        except psycopg2.Error as e:
            print(f"❌ Error getting database stats: {e}")

    def save_alert_with_image(self, timestamp, image_base64, camera_source, motion_confidence=0.8, motion_areas_count=1):
        """
        Save motion alert with image to database (for real-time wireless camera feeds)
        
        Args:
            timestamp: DateTime when alert occurred
            image_base64: Base64 encoded image data
            camera_source: Source camera identifier
            motion_confidence: Motion detection confidence (0.0 to 1.0)
            motion_areas_count: Number of motion areas detected
            
        Returns:
            alert_id if successful, None if failed
        """
        try:
            # Connect to database if not already connected
            if not hasattr(self, 'conn') or self.conn.closed:
                if not self.connect_db():
                    return None
            
            # Insert alert record first
            self.cursor.execute(f"""
                INSERT INTO {TABLES['alerts']} 
                (timestamp, detection_type, frame_saved, motion_areas_count, sensitivity, camera_source, motion_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                timestamp,
                'motion_alert',
                True,
                motion_areas_count,
                50,  # Default sensitivity
                camera_source,
                motion_confidence
            ))
            
            alert_id = self.cursor.fetchone()[0]
            
            # Generate filename based on timestamp
            filename = f"wireless_motion_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
            
            # Get image dimensions from base64 data (rough estimate)
            import base64
            image_data = base64.b64decode(image_base64)
            file_size = len(image_data)
            
            # Try to get actual dimensions using PIL
            width, height = 640, 480  # Default dimensions
            try:
                from io import BytesIO
                from PIL import Image
                img = Image.open(BytesIO(image_data))
                width, height = img.size
            except:
                pass  # Use defaults if PIL fails
            
            # Insert image record
            self.cursor.execute(f"""
                INSERT INTO {TABLES['images']} 
                (alert_id, image_name, image_data, image_type, file_size, width, height)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                alert_id,
                filename,
                image_base64,
                'jpg',
                file_size,
                width,
                height
            ))
            
            self.conn.commit()
            print(f"💾 Wireless alert saved to database: Alert ID {alert_id}, Size: {file_size//1000}KB")
            return alert_id
            
        except psycopg2.Error as e:
            print(f"❌ Database error saving wireless alert: {e}")
            if hasattr(self, 'conn'):
                self.conn.rollback()
            return None
        except Exception as e:
            print(f"❌ Error saving wireless alert: {e}")
            return None

def main():
    """Main processing function"""
    print("🖼️ Motion Detection Image Processor")
    print("=" * 50)
    
    processor = ImageProcessor()
    
    # Connect to database
    if not processor.connect_db():
        return
    
    try:
        # Show current database stats
        processor.show_database_stats()
        
        # Process all images
        processor.process_all_images()
        
        # Show updated stats
        processor.show_database_stats()
        
        if processor.processed_count > 0:
            print(f"\n🎉 Successfully processed {processor.processed_count} new images!")
            print("💡 You can now run 'python web_viewer.py' to view them in the web interface")
        else:
            print("\n📝 No new images to process")
        
    finally:
        processor.close_db()

if __name__ == "__main__":
    main()
