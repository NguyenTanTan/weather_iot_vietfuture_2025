from flask import Flask, render_template, jsonify, request
import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Firebase Push ID decoding constants
PUSH_CHARS = '-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz'

def decode_firebase_timestamp(push_id):
    """Decode Firebase Push ID to get actual timestamp"""
    try:
        timestamp_b64 = push_id[0:8]
        timestamp = 0
        for i in range(0, 8):
            timestamp += PUSH_CHARS.index(timestamp_b64[i]) * (64**(7-i))
        return timestamp
    except Exception as e:
        print(f"Error decoding timestamp from {push_id}: {e}")
        return None

# Initialize Firebase Admin SDK
def initialize_firebase():
    try:
        # Check if Firebase app is already initialized
        firebase_admin.get_app()
        print("✅ Firebase đã được khởi tạo trước đó")
    except ValueError:
        # Initialize Firebase with service account key
        try:
            # Try to get credentials from environment variable first (for production)
            firebase_creds = os.environ.get('FIREBASE_CREDENTIALS')
            if firebase_creds:
                import json
                try:
                    cred_dict = json.loads(firebase_creds)
                    cred = credentials.Certificate(cred_dict)
                    print("✅ Firebase initialized with environment credentials")
                except json.JSONDecodeError as e:
                    print(f"❌ Error parsing FIREBASE_CREDENTIALS: {e}")
                    return None
            else:
                # Fallback to local file (for development)
                try:
                    cred = credentials.Certificate("firebase-service-account.json")
                    print("✅ Firebase initialized with local file")
                except FileNotFoundError:
                    print("⚠️ Firebase service account file not found. Firebase features will be disabled.")
                    return None
            
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://esp-sensor-station-default-rtdb.asia-southeast1.firebasedatabase.app'
            })
            print("✅ Firebase initialized successfully")
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            return None
    
    try:
        # Get reference to Realtime Database
        ref = db.reference()
        print("✅ Firebase Realtime Database client created successfully")
        return ref
    except Exception as e:
        print(f"❌ Firebase Realtime Database client creation failed: {e}")
        return None

# Initialize Firebase
db_ref = initialize_firebase()

# Get weather data from Firebase Realtime Database
def get_firebase_weather_data():
    """Get weather data from Firebase Realtime Database"""
    if not db_ref:
        print("❌ Firebase not available")
        return []
    
    try:
        print("🔍 Đang lấy dữ liệu từ Firebase Realtime Database...")
        
        # Get data from path "0001/push" based on the export structure
        ref = db.reference('0001/push')
        data = ref.get()
        
        if not data:
            print("⚠️ Không có dữ liệu từ Firebase")
            return []
        
        # Convert Firebase data to list format
        weather_data = []
        for push_id, record in data.items():
            try:
                # Decode timestamp from push ID
                timestamp = decode_firebase_timestamp(push_id)
                if timestamp:
                    dt = datetime.fromtimestamp(timestamp / 1000)
                else:
                    dt = datetime.now()
                
                # Extract weather data
                weather_record = {
                    'datetime': dt,
                    'temperature': float(record.get('temperature', 0)),
                    'humidity': float(record.get('humidity', 0)),
                    'pressure': float(record.get('pressure', 0)),
                    'rain': float(record.get('rain', 0)),
                    'sustain_windSpd': float(record.get('sustain_windSpd', 0)),
                    'sustain_windDir': float(record.get('sustain_windDir', 0)),
                    'gust_windSpd': float(record.get('gust_windSpd', 0)),
                    'gust_windDir': float(record.get('gust_windDir', 0))
                }
                weather_data.append(weather_record)
            except Exception as e:
                print(f"Error processing record {push_id}: {e}")
                continue
        
        # Sort by datetime (newest first)
        weather_data.sort(key=lambda x: x['datetime'], reverse=True)
        
        print(f"✅ Firebase data loaded: {len(weather_data)} records")
        return weather_data
        
    except Exception as e:
        print(f"❌ Error getting Firebase data: {e}")
        return []

# Default weather data when Firebase is not available
def get_default_weather_data():
    """Return default weather data when Firebase is not available"""
    now = datetime.now()
    data = []
    
    # Generate sample data for the last 30 days to test week/month views
    for i in range(30):
        dt = now - timedelta(days=i)
        data.append({
            'datetime': dt,
            'temperature': 25.0 + (i % 10) - 5,  # Vary temperature
            'humidity': 60.0 + (i % 20),  # Vary humidity
            'pressure': 1013.25 + (i % 10) - 5,  # Vary pressure
            'rain': (i % 3) * 2.5,  # Some rain days
            'sustain_windSpd': 5.0 + (i % 8),  # Vary wind speed
            'sustain_windDir': 180.0 + (i % 180),  # Vary wind direction
            'gust_windSpd': 8.0 + (i % 12),  # Vary gust wind speed
            'gust_windDir': 180.0 + (i % 180)  # Vary gust wind direction
        })
    
    return data

@app.route('/')
def index():
    """Trang chủ hiển thị dashboard"""
    return render_template('index.html')

@app.route('/api/weather-data')
def get_weather_data():
    """API endpoint để lấy dữ liệu thời tiết từ CSV hoặc Firebase"""
    try:
        # Always use Firebase data
        print("🔥 Sử dụng Firebase data")
        firebase_data = get_firebase_weather_data()
        
        if not firebase_data:
            # Fallback to default data if Firebase is empty
            print("⚠️ Firebase data empty, falling back to default")
            firebase_data = get_default_weather_data()
        
        # Sort data by datetime (newest first) for proper display
        firebase_data.sort(key=lambda x: x.get('datetime', datetime.now()), reverse=True)
        
        # Calculate statistics from Firebase data
        temps = [item.get('temperature', 0) for item in firebase_data]
        humidities = [item.get('humidity', 0) for item in firebase_data]
        pressures = [item.get('pressure', 0) for item in firebase_data]
        
        stats = {
            'total_records': len(firebase_data),
            'latest_temperature': float(temps[0]) if temps else 0,
            'latest_humidity': float(humidities[0]) if humidities else 0,
            'latest_pressure': float(pressures[0]) if pressures else 0,
            'avg_temperature': float(sum(temps) / len(temps)) if temps else 0,
            'avg_humidity': float(sum(humidities) / len(humidities)) if humidities else 0,
            'max_temperature': float(max(temps)) if temps else 0,
            'min_temperature': float(min(temps)) if temps else 0,
            'last_update': firebase_data[0].get('datetime', datetime.now()).strftime('%Y-%m-%d %I:%M:%S %p')
        }
        
        print(f"✅ Firebase data processed: {len(firebase_data)} records")
        return jsonify({
            'success': True,
            'data': firebase_data,
            'stats': stats,
            'count': len(firebase_data),
            'source': 'firebase'
        })
    except Exception as e:
        print(f"❌ Error in get_weather_data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather-chart-data')
def get_weather_chart_data():
    """API endpoint để lấy dữ liệu cho biểu đồ"""
    try:
        # Always use Firebase data
        print("🔥 Sử dụng Firebase data cho chart")
        firebase_data = get_firebase_weather_data()
        
        if not firebase_data:
            # Fallback to default data if Firebase is empty
            print("⚠️ Firebase data empty for chart, falling back to default")
            firebase_data = get_default_weather_data()
        
        # Get last 10 records for chart
        chart_data = firebase_data[:10] if len(firebase_data) > 10 else firebase_data
        
        # Prepare data for charts with better formatting
        chart_data_dict = {
            'timestamps': [item.get('datetime', '').strftime('%H:%M') for item in chart_data],
            'dates': [item.get('datetime', '').strftime('%d/%m') for item in chart_data],
            'temperature': [item.get('temperature', 0) for item in chart_data],
            'humidity': [item.get('humidity', 0) for item in chart_data],
            'pressure': [item.get('pressure', 0) for item in chart_data],
            'rain': [item.get('rain', 0) for item in chart_data],
            'gust_windSpd': [item.get('gust_windSpd', 0) for item in chart_data],
            'gust_windDir': [item.get('gust_windDir', 0) for item in chart_data],
            'sustain_windSpd': [item.get('sustain_windSpd', 0) for item in chart_data],
            'sustain_windDir': [item.get('sustain_windDir', 0) for item in chart_data]
        }
        
        print(f"✅ Firebase chart data prepared: {len(chart_data_dict['timestamps'])} points")
        return jsonify({
            'success': True,
            'data': chart_data_dict,
            'source': 'firebase'
        })
    except Exception as e:
        print(f"❌ Error in get_weather_chart_data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather-summary')
def get_weather_summary():
    """API endpoint để lấy tổng quan thời tiết"""
    try:
        # Always use Firebase data
        print("🔥 Sử dụng Firebase data cho summary")
        firebase_data = get_firebase_weather_data()
        
        if not firebase_data:
            # Fallback to default data if Firebase is empty
            print("⚠️ Firebase data empty for summary, falling back to default")
            firebase_data = get_default_weather_data()
        
        latest = firebase_data[0]
        summary = {
            'current_temp': float(latest.get('temperature', 0)),
            'current_humidity': float(latest.get('humidity', 0)),
            'current_pressure': float(latest.get('pressure', 0)),
            'today_high': float(max([item.get('temperature', 0) for item in firebase_data])),
            'today_low': float(min([item.get('temperature', 0) for item in firebase_data])),
            'today_avg_temp': float(sum([item.get('temperature', 0) for item in firebase_data]) / len(firebase_data)),
            'today_avg_humidity': float(sum([item.get('humidity', 0) for item in firebase_data]) / len(firebase_data)),
            'wind_speed': float(latest.get('sustain_windSpd', 0)),
            'wind_direction': float(latest.get('sustain_windDir', 0)),
            'rain_today': float(sum([item.get('rain', 0) for item in firebase_data])),
            'gust_wind_speed': float(latest.get('gust_windSpd', 0)),
            'gust_wind_direction': float(latest.get('gust_windDir', 0)),
            'sustain_wind_direction': float(latest.get('sustain_windDir', 0)),
            'last_update': latest.get('datetime', datetime.now()).strftime('%I:%M:%S %p')
        }
        
        print(f"✅ Firebase summary prepared: temp={summary['current_temp']}°C")
        return jsonify({
            'success': True,
            'summary': summary,
            'source': 'firebase'
        })
    except Exception as e:
        print(f"❌ Error in get_weather_summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/data-sources')
def get_data_sources():
    """API endpoint để kiểm tra nguồn dữ liệu có sẵn"""
    sources = {
        'firebase': db_ref is not None,
        'default': True  # Always available as fallback
    }
    
    print(f"🌐 API call: data-sources, available={sources}")
    return jsonify({
        'success': True,
        'sources': sources
    })

@app.route('/api/weather-chart-data/<period>')
def get_weather_chart_data_by_period(period):
    """API endpoint để lấy dữ liệu biểu đồ theo thời gian (day/week/month)"""
    try:
        print(f"🔥 Sử dụng Firebase data cho chart với period: {period}")
        firebase_data = get_firebase_weather_data()
        
        if not firebase_data:
            print("⚠️ Firebase data empty for chart, falling back to default")
            firebase_data = get_default_weather_data()
        
        if period == 'day':
            # Last 24 hours - show 10 points
            now = datetime.now()
            start_time = now - timedelta(days=1)
            filtered_data = [item for item in firebase_data if item.get('datetime', now) >= start_time]
            chart_data = filtered_data[:10] if len(filtered_data) > 10 else filtered_data
            
            # Sort by datetime (oldest to newest) to match week/month format
            chart_data.sort(key=lambda x: x.get('datetime', now))
            
            chart_data_dict = {
                'timestamps': [item.get('datetime', '').strftime('%H:%M') for item in chart_data],
                'dates': [item.get('datetime', '').strftime('%d/%m') for item in chart_data],
                'temperature': [item.get('temperature', 0) for item in chart_data],
                'humidity': [item.get('humidity', 0) for item in chart_data],
                'pressure': [item.get('pressure', 0) for item in chart_data],
                'rain': [item.get('rain', 0) for item in chart_data],
                'gust_windSpd': [item.get('gust_windSpd', 0) for item in chart_data],
                'gust_windDir': [item.get('gust_windDir', 0) for item in chart_data],
                'sustain_windSpd': [item.get('sustain_windSpd', 0) for item in chart_data],
                'sustain_windDir': [item.get('sustain_windDir', 0) for item in chart_data]
            }
            
        elif period == 'week':
            # Last 7 days - calculate daily averages
            now = datetime.now()
            daily_data = {}
            
            for item in firebase_data:
                item_date = item.get('datetime', now).date()
                if item_date not in daily_data:
                    daily_data[item_date] = {
                        'temperatures': [], 'humidities': [], 'pressures': [], 'rains': [],
                        'gust_windSpds': [], 'gust_windDirs': [], 'sustain_windSpds': [], 'sustain_windDirs': []
                    }
                
                daily_data[item_date]['temperatures'].append(item.get('temperature', 0))
                daily_data[item_date]['humidities'].append(item.get('humidity', 0))
                daily_data[item_date]['pressures'].append(item.get('pressure', 0))
                daily_data[item_date]['rains'].append(item.get('rain', 0))
                daily_data[item_date]['gust_windSpds'].append(item.get('gust_windSpd', 0))
                daily_data[item_date]['gust_windDirs'].append(item.get('gust_windDir', 0))
                daily_data[item_date]['sustain_windSpds'].append(item.get('sustain_windSpd', 0))
                daily_data[item_date]['sustain_windDirs'].append(item.get('sustain_windDir', 0))
            
            # Get last 7 days and calculate averages
            dates = sorted(daily_data.keys(), reverse=True)[:7]
            dates.reverse()  # Show oldest to newest
            
            chart_data_dict = {
                'timestamps': [date.strftime('%H:%M') for date in dates],  # Use time format for consistency
                'dates': [date.strftime('%d/%m') for date in dates],
                'temperature': [sum(daily_data[date]['temperatures']) / len(daily_data[date]['temperatures']) if daily_data[date]['temperatures'] else 0 for date in dates],
                'humidity': [sum(daily_data[date]['humidities']) / len(daily_data[date]['humidities']) if daily_data[date]['humidities'] else 0 for date in dates],
                'pressure': [sum(daily_data[date]['pressures']) / len(daily_data[date]['pressures']) if daily_data[date]['pressures'] else 0 for date in dates],
                'rain': [sum(daily_data[date]['rains']) for date in dates],  # Total rain per day
                'gust_windSpd': [sum(daily_data[date]['gust_windSpds']) / len(daily_data[date]['gust_windSpds']) if daily_data[date]['gust_windSpds'] else 0 for date in dates],
                'gust_windDir': [sum(daily_data[date]['gust_windDirs']) / len(daily_data[date]['gust_windDirs']) if daily_data[date]['gust_windDirs'] else 0 for date in dates],
                'sustain_windSpd': [sum(daily_data[date]['sustain_windSpds']) / len(daily_data[date]['sustain_windSpds']) if daily_data[date]['sustain_windSpds'] else 0 for date in dates],
                'sustain_windDir': [sum(daily_data[date]['sustain_windDirs']) / len(daily_data[date]['sustain_windDirs']) if daily_data[date]['sustain_windDirs'] else 0 for date in dates]
            }
            
        elif period == 'month':
            # Last 7 months - calculate monthly averages
            now = datetime.now()
            monthly_data = {}
            
            for item in firebase_data:
                item_month = item.get('datetime', now).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if item_month not in monthly_data:
                    monthly_data[item_month] = {
                        'temperatures': [], 'humidities': [], 'pressures': [], 'rains': [],
                        'gust_windSpds': [], 'gust_windDirs': [], 'sustain_windSpds': [], 'sustain_windDirs': []
                    }
                
                monthly_data[item_month]['temperatures'].append(item.get('temperature', 0))
                monthly_data[item_month]['humidities'].append(item.get('humidity', 0))
                monthly_data[item_month]['pressures'].append(item.get('pressure', 0))
                monthly_data[item_month]['rains'].append(item.get('rain', 0))
                monthly_data[item_month]['gust_windSpds'].append(item.get('gust_windSpd', 0))
                monthly_data[item_month]['gust_windDirs'].append(item.get('gust_windDir', 0))
                monthly_data[item_month]['sustain_windSpds'].append(item.get('sustain_windSpd', 0))
                monthly_data[item_month]['sustain_windDirs'].append(item.get('sustain_windDir', 0))
            
            # Get last 7 months and calculate averages
            months = sorted(monthly_data.keys(), reverse=True)[:7]
            months.reverse()  # Show oldest to newest
            
            chart_data_dict = {
                'timestamps': [month.strftime('%H:%M') for month in months],  # Use time format for consistency
                'dates': [month.strftime('%m/%Y') for month in months],
                'temperature': [sum(monthly_data[month]['temperatures']) / len(monthly_data[month]['temperatures']) if monthly_data[month]['temperatures'] else 0 for month in months],
                'humidity': [sum(monthly_data[month]['humidities']) / len(monthly_data[month]['humidities']) if monthly_data[month]['humidities'] else 0 for month in months],
                'pressure': [sum(monthly_data[month]['pressures']) / len(monthly_data[month]['pressures']) if monthly_data[month]['pressures'] else 0 for month in months],
                'rain': [sum(monthly_data[month]['rains']) for month in months],  # Total rain per month
                'gust_windSpd': [sum(monthly_data[month]['gust_windSpds']) / len(monthly_data[month]['gust_windSpds']) if monthly_data[month]['gust_windSpds'] else 0 for month in months],
                'gust_windDir': [sum(monthly_data[month]['gust_windDirs']) / len(monthly_data[month]['gust_windDirs']) if monthly_data[month]['gust_windDirs'] else 0 for month in months],
                'sustain_windSpd': [sum(monthly_data[month]['sustain_windSpds']) / len(monthly_data[month]['sustain_windSpds']) if monthly_data[month]['sustain_windSpds'] else 0 for month in months],
                'sustain_windDir': [sum(monthly_data[month]['sustain_windDirs']) / len(monthly_data[month]['sustain_windDirs']) if monthly_data[month]['sustain_windDirs'] else 0 for month in months]
            }
            
        else:
            # Default to last 10 records
            chart_data = firebase_data[:10] if len(firebase_data) > 10 else firebase_data
            
            chart_data_dict = {
                'timestamps': [item.get('datetime', '').strftime('%H:%M') for item in chart_data],
                'dates': [item.get('datetime', '').strftime('%d/%m') for item in chart_data],
                'temperature': [item.get('temperature', 0) for item in chart_data],
                'humidity': [item.get('humidity', 0) for item in chart_data],
                'pressure': [item.get('pressure', 0) for item in chart_data],
                'rain': [item.get('rain', 0) for item in chart_data],
                'gust_windSpd': [item.get('gust_windSpd', 0) for item in chart_data],
                'gust_windDir': [item.get('gust_windDir', 0) for item in chart_data],
                'sustain_windSpd': [item.get('sustain_windSpd', 0) for item in chart_data],
                'sustain_windDir': [item.get('sustain_windDir', 0) for item in chart_data]
            }
        
        print(f"✅ Firebase chart data prepared: {len(chart_data_dict['timestamps'])} points for {period}")
        return jsonify({
            'success': True,
            'data': chart_data_dict,
            'source': 'firebase',
            'period': period
        })
    except Exception as e:
        print(f"❌ Error in get_weather_chart_data_by_period: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/data')
def get_data():
    """API endpoint để lấy dữ liệu từ Firebase (giữ lại cho tương thích)"""
    try:
        if not db_ref:
            return jsonify({
                'success': False,
                'error': 'Firebase not configured'
            }), 500
            
        # Lấy dữ liệu từ Realtime Database
        ref = db.reference()
        data = ref.get()
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data) if isinstance(data, list) else 1
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/real-time')
def real_time_data():
    """API endpoint cho dữ liệu real-time"""
    try:
        if not db_ref:
            return jsonify({
                'success': False,
                'error': 'Firebase not configured'
            }), 500
            
        # Lấy dữ liệu mới nhất từ Realtime Database
        ref = db.reference()
        data = ref.get()
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port) 