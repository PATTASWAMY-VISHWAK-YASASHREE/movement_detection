#!/usr/bin/env python3
"""
Web Viewer for Motion Detection Security System

Flask web application to view stored alert images from PostgreSQL database.
Images are decoded from Base64 strings and displayed in a web interface.
"""

import base64
import json
import os
from datetime import datetime, timedelta
from io import BytesIO
import psycopg2
from flask import Flask, render_template, request, jsonify, send_file, url_for
from database_config import get_psycopg2_params, TABLES

app = Flask(__name__)
app.secret_key = 'motion_detection_security_system_2025'

class WebViewer:
    def __init__(self):
        self.conn = None
        self.cursor = None
    
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
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def get_alerts(self, limit=50, offset=0, detection_type=None, date_from=None, date_to=None, search_query=None):
        """Get alerts with pagination and filtering - NO IMAGE DATA for performance"""
        try:
            # Build WHERE clause
            where_conditions = []
            params = []
            
            if detection_type and detection_type != 'all':
                where_conditions.append("a.detection_type = %s")
                params.append(detection_type)
            
            if date_from:
                where_conditions.append("a.timestamp >= %s")
                params.append(date_from)
            
            if date_to:
                where_conditions.append("a.timestamp <= %s")
                params.append(date_to + timedelta(days=1))  # Include full day
            
            if search_query:
                where_conditions.append("(i.image_name ILIKE %s OR a.objects_detected::text ILIKE %s)")
                search_pattern = f"%{search_query}%"
                params.extend([search_pattern, search_pattern])
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Main query - EXCLUDE image_data for performance
            query = f"""
                SELECT 
                    a.id,
                    a.timestamp,
                    a.detection_type,
                    a.motion_areas_count,
                    a.sensitivity,
                    a.objects_detected,
                    a.confidence_scores,
                    i.id as image_id,
                    i.image_name,
                    i.image_type,
                    i.file_size,
                    i.width,
                    i.height
                FROM {TABLES['alerts']} a
                LEFT JOIN {TABLES['images']} i ON a.id = i.alert_id
                {where_clause}
                ORDER BY a.timestamp DESC
                LIMIT %s OFFSET %s
            """
            
            params.extend([limit, offset])
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            # Count total records for pagination
            count_query = f"""
                SELECT COUNT(DISTINCT a.id)
                FROM {TABLES['alerts']} a
                LEFT JOIN {TABLES['images']} i ON a.id = i.alert_id
                {where_clause}
            """
            
            self.cursor.execute(count_query, params[:-2])  # Exclude limit and offset
            total_count = self.cursor.fetchone()[0]
            
            return results, total_count
            
        except psycopg2.Error as e:
            print(f"❌ Database error: {e}")
            return [], 0
    
    def get_image_data(self, image_id):
        """Get Base64 image data for display"""
        try:
            self.cursor.execute(f"""
                SELECT image_data, image_type, image_name
                FROM {TABLES['images']}
                WHERE id = %s
            """, (image_id,))
            
            result = self.cursor.fetchone()
            if result:
                return {
                    'image_data': result[0],
                    'image_type': result[1],
                    'image_name': result[2]
                }
            return None
            
        except psycopg2.Error as e:
            print(f"❌ Database error: {e}")
            return None
    
    def get_statistics(self):
        """Get dashboard statistics"""
        try:
            stats = {}
            
            # Total counts
            self.cursor.execute(f"SELECT COUNT(*) FROM {TABLES['alerts']}")
            stats['total_alerts'] = self.cursor.fetchone()[0]
            
            self.cursor.execute(f"SELECT COUNT(*) FROM {TABLES['images']}")
            stats['total_images'] = self.cursor.fetchone()[0]
            
            # Total size
            self.cursor.execute(f"SELECT SUM(file_size) FROM {TABLES['images']}")
            total_size = self.cursor.fetchone()[0] or 0
            stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            # Recent activity (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            self.cursor.execute(f"""
                SELECT COUNT(*) FROM {TABLES['alerts']} 
                WHERE timestamp >= %s
            """, (yesterday,))
            stats['alerts_24h'] = self.cursor.fetchone()[0]
            
            # Detection types
            self.cursor.execute(f"""
                SELECT detection_type, COUNT(*) 
                FROM {TABLES['alerts']} 
                GROUP BY detection_type 
                ORDER BY COUNT(*) DESC
            """)
            stats['detection_types'] = self.cursor.fetchall()
            
            # Recent dates with activity
            self.cursor.execute(f"""
                SELECT DATE(timestamp) as alert_date, COUNT(*) 
                FROM {TABLES['alerts']} 
                WHERE timestamp >= %s
                GROUP BY DATE(timestamp) 
                ORDER BY alert_date DESC
                LIMIT 7
            """, (datetime.now() - timedelta(days=7),))
            stats['recent_activity'] = self.cursor.fetchall()
            
            return stats
            
        except psycopg2.Error as e:
            print(f"❌ Database error: {e}")
            return {}

# Global viewer instance
viewer = WebViewer()

def initialize():
    """Initialize database connection"""
    if not viewer.connect_db():
        print("❌ Failed to connect to database")

# Initialize on startup
with app.app_context():
    initialize()

@app.teardown_appcontext
def close_db_connection(exception):
    """Close database connection"""
    pass  # Keep connection open for reuse

@app.route('/')
def index():
    """Main dashboard page with lazy loading"""
    # Get filter parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    detection_type = request.args.get('type', 'all')
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    search_query = request.args.get('search', '').strip()
    
    # Parse dates
    date_from = None
    date_to = None
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Get alerts (without image data for performance)
    offset = (page - 1) * per_page
    alerts, total_count = viewer.get_alerts(
        limit=per_page, 
        offset=offset,
        detection_type=detection_type,
        date_from=date_from,
        date_to=date_to,
        search_query=search_query if search_query else None
    )
    
    # Calculate pagination
    total_pages = (total_count + per_page - 1) // per_page
    
    # Get statistics
    stats = viewer.get_statistics()
    
    return render_template('index.html', 
                         alerts=alerts,
                         stats=stats,
                         pagination={
                             'page': page,
                             'per_page': per_page,
                             'total_pages': total_pages,
                             'total_count': total_count
                         },
                         filters={
                             'type': detection_type,
                             'date_from': date_from_str,
                             'date_to': date_to_str,
                             'search': search_query
                         })

@app.route('/image/<int:image_id>')
def view_image(image_id):
    """Display individual image"""
    image_data = viewer.get_image_data(image_id)
    if not image_data:
        return "Image not found", 404
    
    # Decode Base64 image
    try:
        image_bytes = base64.b64decode(image_data['image_data'])
        return send_file(
            BytesIO(image_bytes),
            mimetype=f"image/{image_data['image_type']}",
            as_attachment=False,
            download_name=image_data['image_name']
        )
    except Exception as e:
        return f"Error displaying image: {e}", 500

@app.route('/thumbnail/<int:image_id>')
def get_thumbnail(image_id):
    """Generate and return thumbnail for lazy loading"""
    image_data = viewer.get_image_data(image_id)
    if not image_data:
        return "Image not found", 404
    
    try:
        from PIL import Image
        
        # Decode Base64 image
        image_bytes = base64.b64decode(image_data['image_data'])
        
        # Open image and create thumbnail
        with Image.open(BytesIO(image_bytes)) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Create thumbnail (max 300x200 for performance)
            img.thumbnail((300, 200), Image.Resampling.LANCZOS)
            
            # Save as JPEG with compression
            thumbnail_bytes = BytesIO()
            img.save(thumbnail_bytes, format='JPEG', quality=75, optimize=True)
            thumbnail_bytes.seek(0)
            
            return send_file(
                thumbnail_bytes,
                mimetype="image/jpeg",
                as_attachment=False
            )
    except Exception as e:
        # Return a placeholder if thumbnail generation fails
        return f"Error generating thumbnail: {e}", 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    stats = viewer.get_statistics()
    return jsonify(stats)

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for alerts"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    detection_type = request.args.get('type', 'all')
    
    offset = (page - 1) * per_page
    alerts, total_count = viewer.get_alerts(
        limit=per_page, 
        offset=offset,
        detection_type=detection_type
    )
    
    # Format alerts for JSON
    formatted_alerts = []
    for alert in alerts:
        formatted_alerts.append({
            'id': alert[0],
            'timestamp': alert[1].isoformat() if alert[1] else None,
            'detection_type': alert[2],
            'motion_areas_count': alert[3],
            'sensitivity': alert[4],
            'objects_detected': alert[5],
            'confidence_scores': alert[6],
            'image_id': alert[7],
            'image_name': alert[8],
            'image_type': alert[9],
            'file_size': alert[10],
            'width': alert[11],
            'height': alert[12]
        })
    
    return jsonify({
        'alerts': formatted_alerts,
        'total_count': total_count,
        'page': page,
        'per_page': per_page
    })

def create_template_files():
    """Create HTML template files"""
    template_dir = "templates"
    os.makedirs(template_dir, exist_ok=True)
    
    # Create base template
    base_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Motion Detection Security System{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .alert-card { transition: transform 0.2s; }
        .alert-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .image-thumbnail { max-height: 200px; object-fit: cover; }
        .stats-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .navbar-brand { font-weight: bold; }
        
        /* Lazy loading styles */
        .lazy-image-container { position: relative; }
        .image-placeholder { 
            cursor: pointer; 
            transition: background-color 0.3s;
            border: 2px dashed #dee2e6;
            border-radius: 8px;
        }
        .image-placeholder:hover { 
            background-color: #f8f9fa !important; 
            border-color: #6c757d;
        }
        .image-thumbnail { 
            border-radius: 8px;
            transition: opacity 0.3s;
        }
        .load-image-btn:hover { 
            transform: scale(1.05);
        }
        
        /* Search highlight */
        .search-highlight {
            background-color: #fff3cd;
            padding: 2px 4px;
            border-radius: 3px;
        }
        
        /* Loading states */
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-shield-alt"></i> Motion Detection System
            </a>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>"""
    
    # Write template files
    with open(f"{template_dir}/base.html", "w") as f:
        f.write(base_template)
    
    print("✅ Created HTML template files")

def main():
    """Main function to start the web viewer"""
    print("🌐 Motion Detection Web Viewer with Lazy Loading")
    print("=" * 50)
    
    # Create template files
    create_template_files()
    
    # Test database connection
    if not viewer.connect_db():
        print("❌ Cannot start web viewer without database connection")
        print("💡 Please run 'python setup_database.py' first")
        return
    
    print("✅ Database connection successful")
    
    # Get stats
    stats = viewer.get_statistics()
    print(f"📊 Found {stats.get('total_alerts', 0)} alerts and {stats.get('total_images', 0)} images")
    
    if stats.get('total_images', 0) == 0:
        print("💡 No images found. Run 'python image_processor.py' to process existing images")
      # Get local IP address
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "localhost"
    
    server_ip = get_local_ip()
    
    # Start Flask app
    print("\n🚀 Starting optimized web server with lazy loading...")
    print(f"🌐 Open your browser and go to: http://{server_ip}:5000")
    print("📱 Access from other devices on your network using the IP above")
    print("⚡ Images load only when requested - no more lag!")
    print("🔍 Use search to automatically load relevant images")
    print("⏹️  Press Ctrl+C to stop the server")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Web server stopped")
    finally:
        viewer.close_db()

if __name__ == "__main__":
    # Run the app on all interfaces by default
    app.run(host='0.0.0.0', port=5000, debug=False)
