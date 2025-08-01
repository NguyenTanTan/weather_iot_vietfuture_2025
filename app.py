from flask import Flask, render_template, jsonify, request
import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv
import pandas as pd
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
                cred_dict = json.loads(firebase_creds)
                cred = credentials.Certificate(cred_dict)
                print("✅ Firebase initialized with environment credentials")
            else:
                # Fallback to local file (for development)
                cred = credentials.Certificate("firebase-service-account.json")
                print("✅ Firebase initialized with local file")
            
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://esp-sensor-station-default-rtdb.asia-southeast1.firebasedatabase.app'
            })
            print("✅ Firebase initialized successfully")
        except FileNotFoundError:
            print("⚠️ Firebase service account file not found. Firebase features will be disabled.")
            return None
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

# Load weather data from CSV
def load_weather_data():
    """Load weather data from CSV file"""
    try:
        df = pd.read_csv('Firebase Data - Historical Data Final.csv')
        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['Data timestamp'], unit='ms')
        # Convert string numbers to float (handle comma decimal separator)
        df['temperature'] = df['temperature'].astype(str).str.replace(',', '.').astype(float)
        df['humidity'] = df['humidity'].astype(str).str.replace(',', '.').astype(float)
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame()

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
        
        if data:
            print(f"✅ Tìm thấy dữ liệu tại path '0001/push'")
            weather_data = []
            
            # Convert data to list format
            if isinstance(data, dict):
                # Sort by key (timestamp) in descending order to get latest first
                sorted_keys = sorted(data.keys(), reverse=True)
                
                for key in sorted_keys[:50]:  # Get latest 50 records
                    value = data[key]
                    if isinstance(value, dict):
                        value['id'] = key
                        # Decode actual timestamp from Firebase Push ID
                        decoded_timestamp = decode_firebase_timestamp(key)
                        if decoded_timestamp:
                            # Convert milliseconds to datetime
                            value['timestamp'] = decoded_timestamp
                            value['datetime'] = datetime.fromtimestamp(decoded_timestamp / 1000.0)
                        else:
                            # Fallback to current time if decoding fails
                            value['timestamp'] = key
                            value['datetime'] = datetime.now()
                        weather_data.append(value)
            
            print(f"✅ Lấy được {len(weather_data)} records từ Firebase")
            if weather_data:
                print(f"   Sample data: {weather_data[0]}")
            
            return weather_data
        else:
            print("⚠️ Không tìm thấy dữ liệu tại path '0001/push'")
            return []
        
    except Exception as e:
        print(f"❌ Error getting Firebase data: {e}")
        return []
'''
    "gust_windDir": 0,
        "gust_windSpd": 0,
        "humidity": 95.2,
        "id": "0001",
        "pressure": 1014,
        "rain": 0,
        "sustain_windDir": 0,
        "sustain_windSpd": 0,
        "temperature": 25.6
'''
@app.route('/')
def index():
    """Trang chủ hiển thị dashboard"""
    return render_template('index.html')

@app.route('/api/weather-data')
def get_weather_data():
    """API endpoint để lấy dữ liệu thời tiết từ CSV hoặc Firebase"""
    try:
        # Check if user wants Firebase data
        use_firebase = request.args.get('source', 'csv').lower() == 'firebase'
        print(f"🌐 API call: weather-data, source={request.args.get('source', 'csv')}")
        
        if use_firebase and db_ref:
            print("🔥 Sử dụng Firebase data")
            # Get data from Firebase
            firebase_data = get_firebase_weather_data()
            if firebase_data:
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
            else:
                print("⚠️ Firebase data empty, falling back to CSV")
        
        # Fallback to CSV data
        print("📄 Sử dụng CSV data")
        df = load_weather_data()
        if df.empty:
            return jsonify({
                'success': False,
                'error': 'Không thể tải dữ liệu CSV'
            }), 500
        
        # Get latest data
        latest_data = df.tail(50).to_dict('records')
        
        # Calculate statistics
        stats = {
            'total_records': len(df),
            'latest_temperature': float(df['temperature'].iloc[-1]),
            'latest_humidity': float(df['humidity'].iloc[-1]),
            'latest_pressure': float(df['pressure'].iloc[-1]),
            'avg_temperature': float(df['temperature'].mean()),
            'avg_humidity': float(df['humidity'].mean()),
            'max_temperature': float(df['temperature'].max()),
            'min_temperature': float(df['temperature'].min()),
            'last_update': df['datetime'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ CSV data processed: {len(latest_data)} records")
        return jsonify({
            'success': True,
            'data': latest_data,
            'stats': stats,
            'count': len(latest_data),
            'source': 'csv'
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
        # Check if user wants Firebase data
        use_firebase = request.args.get('source', 'csv').lower() == 'firebase'
        print(f"🌐 API call: weather-chart-data, source={request.args.get('source', 'csv')}")
        
        if use_firebase and db_ref:
            print("🔥 Sử dụng Firebase data cho chart")
            # Get data from Firebase
            firebase_data = get_firebase_weather_data()
            if firebase_data:
                                # Prepare data for charts
                chart_data_dict = {
                    'timestamps': [item.get('datetime', '').strftime('%Y-%m-%d %I:%M %p') for item in firebase_data],
                    'temperature': [item.get('temperature', 0) for item in firebase_data],
                    'humidity': [item.get('humidity', 0) for item in firebase_data],
                    'pressure': [item.get('pressure', 0) for item in firebase_data],
                    'rain': [item.get('rain', 0) for item in firebase_data],
                    'gust_windSpd': [item.get('gust_windSpd', 0) for item in firebase_data],
                    'gust_windDir': [item.get('gust_windDir', 0) for item in firebase_data],
                    'sustain_windSpd': [item.get('sustain_windSpd', 0) for item in firebase_data],
                    'sustain_windDir': [item.get('sustain_windDir', 0) for item in firebase_data]
                }
                
                print(f"✅ Firebase chart data prepared: {len(chart_data_dict['timestamps'])} points")
                return jsonify({
                    'success': True,
                    'data': chart_data_dict,
                    'source': 'firebase'
                })
            else:
                print("⚠️ Firebase data empty for chart, falling back to CSV")
        
        # Fallback to CSV data
        print("📄 Sử dụng CSV data cho chart")
        df = load_weather_data()
        if df.empty:
            return jsonify({
                'success': False,
                'error': 'Không thể tải dữ liệu CSV'
            }), 500
        
        # Get last 100 records for chart
        chart_data = df.tail(100)
        
        # Prepare data for charts
        chart_data_dict = {
            'timestamps': chart_data['datetime'].dt.strftime('%Y-%m-%d %I:%M %p').tolist(),
            'temperature': chart_data['temperature'].tolist(),
            'humidity': chart_data['humidity'].tolist(),
            'pressure': chart_data['pressure'].tolist(),
            'rain': chart_data['rain'].tolist(),
            'gust_windSpd': chart_data['gust_windSpd'].tolist(),
            'gust_windDir': chart_data['gust_windDir'].tolist(),
            'sustain_windSpd': chart_data['sustain_windSpd'].tolist(),
            'sustain_windDir': chart_data['sustain_windDir'].tolist()
        }
        
        print(f"✅ CSV chart data prepared: {len(chart_data_dict['timestamps'])} points")
        return jsonify({
            'success': True,
            'data': chart_data_dict,
            'source': 'csv'
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
        # Check if user wants Firebase data
        use_firebase = request.args.get('source', 'csv').lower() == 'firebase'
        print(f"🌐 API call: weather-summary, source={request.args.get('source', 'csv')}")
        
        if use_firebase and db_ref:
            print("🔥 Sử dụng Firebase data cho summary")
            # Get latest data from Firebase
            firebase_data = get_firebase_weather_data()
            if firebase_data:
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
            else:
                print("⚠️ Firebase data empty for summary, falling back to CSV")
        
        # Fallback to CSV data
        print("📄 Sử dụng CSV data cho summary")
        df = load_weather_data()
        if df.empty:
            return jsonify({
                'success': False,
                'error': 'Không thể tải dữ liệu CSV'
            }), 500
        
        # Get today's data
        today = datetime.now().date()
        today_data = df[df['datetime'].dt.date == today]
        
        if len(today_data) == 0:
            # If no data for today, get last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            today_data = df[df['datetime'] >= yesterday]
        
        summary = {
            'current_temp': float(df['temperature'].iloc[-1]),
            'current_humidity': float(df['humidity'].iloc[-1]),
            'current_pressure': float(df['pressure'].iloc[-1]),
            'today_high': float(today_data['temperature'].max()) if len(today_data) > 0 else 0,
            'today_low': float(today_data['temperature'].min()) if len(today_data) > 0 else 0,
            'today_avg_temp': float(today_data['temperature'].mean()) if len(today_data) > 0 else 0,
            'today_avg_humidity': float(today_data['humidity'].mean()) if len(today_data) > 0 else 0,
            'wind_speed': float(df['sustain_windSpd'].iloc[-1]),
            'wind_direction': float(df['sustain_windDir'].iloc[-1]),
            'rain_today': float(today_data['rain'].sum()) if len(today_data) > 0 else 0,
            'gust_wind_speed': float(df['gust_windSpd'].iloc[-1]),
            'gust_wind_direction': float(df['gust_windDir'].iloc[-1]),
            'sustain_wind_direction': float(df['sustain_windDir'].iloc[-1]),
            'last_update': df['datetime'].iloc[-1].strftime('%I:%M:%S %p')
        }
        
        print(f"✅ CSV summary prepared: temp={summary['current_temp']}°C")
        return jsonify({
            'success': True,
            'summary': summary,
            'source': 'csv'
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
        'csv': True,
        'firebase': db_ref is not None
    }
    
    print(f"🌐 API call: data-sources, available={sources}")
    return jsonify({
        'success': True,
        'sources': sources
    })

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