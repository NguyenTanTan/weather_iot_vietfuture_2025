#!/usr/bin/env python3
"""
Script test để kiểm tra kết nối Firebase Realtime Database và dữ liệu
Chạy script này để debug vấn đề Firebase
"""

import firebase_admin
from firebase_admin import credentials, db
import json
from datetime import datetime
import os

def test_firebase_connection():
    """Test kết nối Firebase Realtime Database"""
    print("🔍 Bắt đầu test kết nối Firebase Realtime Database...")
    
    # 1. Kiểm tra file service account
    service_account_file = "firebase-service-account.json"
    if not os.path.exists(service_account_file):
        print(f"❌ File {service_account_file} không tồn tại!")
        print("💡 Hãy tải file service account từ Firebase Console và đặt trong thư mục gốc")
        return False
    
    print(f"✅ File {service_account_file} đã tồn tại")
    
    # 2. Test đọc file service account
    try:
        with open(service_account_file, 'r') as f:
            service_account_data = json.load(f)
        print("✅ File service account có thể đọc được")
        print(f"   Project ID: {service_account_data.get('project_id', 'N/A')}")
    except Exception as e:
        print(f"❌ Lỗi đọc file service account: {e}")
        return False
    
    # 3. Test khởi tạo Firebase
    try:
        # Kiểm tra xem Firebase đã được khởi tạo chưa
        try:
            firebase_admin.get_app()
            print("✅ Firebase đã được khởi tạo")
        except ValueError:
            # Khởi tạo Firebase mới với Realtime Database URL
            cred = credentials.Certificate(service_account_file)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://esp-sensor-station-default-rtdb.asia-southeast1.firebasedatabase.app'
            })
            print("✅ Firebase Realtime Database khởi tạo thành công")
        
        ref = db.reference()
        print("✅ Firebase Realtime Database client tạo thành công")
        
    except Exception as e:
        print(f"❌ Lỗi khởi tạo Firebase: {e}")
        return False
    
    return ref

def test_firebase_data(ref):
    """Test dữ liệu trong Firebase Realtime Database"""
    print("\n📚 Kiểm tra dữ liệu trong Realtime Database...")
    
    try:
        # Lấy toàn bộ dữ liệu từ root
        root_data = ref.get()
        print(f"📋 Root data type: {type(root_data)}")
        
        if root_data:
            print("✅ Có dữ liệu trong database")
            print(f"📄 Root keys: {list(root_data.keys()) if isinstance(root_data, dict) else 'Not a dict'}")
            
            # Test path "0001/push" based on the export structure
            test_path_data(ref, "0001")
            
        else:
            print("⚠️ Database trống")
            
    except Exception as e:
        print(f"❌ Lỗi kiểm tra database: {e}")

def test_path_data(ref, path):
    """Test dữ liệu tại một path cụ thể"""
    print(f"\n   🔍 Kiểm tra path '{path}'...")
    
    try:
        path_ref = db.reference(path)
        data = path_ref.get()
        
        if data:
            print(f"   ✅ Tìm thấy dữ liệu tại path '{path}'")
            print(f"   📊 Data type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"   📋 Keys: {list(data.keys())}")
                
                # Check for "push" subdirectory
                if 'push' in data:
                    print(f"   ✅ Tìm thấy subdirectory 'push'")
                    test_push_data(ref, f"{path}/push")
                else:
                    print(f"   ⚠️ Không tìm thấy subdirectory 'push'")
                    
        else:
            print(f"   ⚠️ Không có dữ liệu tại path '{path}'")
            
    except Exception as e:
        print(f"   ❌ Lỗi đọc path '{path}': {e}")

def test_push_data(ref, path):
    """Test dữ liệu trong push directory"""
    print(f"\n      🔍 Kiểm tra path '{path}'...")
    
    try:
        push_ref = db.reference(path)
        data = push_ref.get()
        
        if data:
            print(f"      ✅ Tìm thấy dữ liệu tại path '{path}'")
            print(f"      📊 Data type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"      📋 Số lượng records: {len(data)}")
                
                # Show sample data
                sample_keys = list(data.keys())[:3]
                for key in sample_keys:
                    print(f"         {key}: {data[key]}")
                    
        else:
            print(f"      ⚠️ Không có dữ liệu tại path '{path}'")
            
    except Exception as e:
        print(f"      ❌ Lỗi đọc path '{path}': {e}")

def create_sample_weather_data(ref):
    """Tạo dữ liệu mẫu cho weather path"""
    print("\n➕ Tạo dữ liệu mẫu cho path 'weather'...")
    
    try:
        weather_ref = db.reference('weather')
        
        # Tạo dữ liệu mẫu với timestamp
        sample_data = {
            'temperature': 25.5,
            'humidity': 80.2,
            'pressure': 1013.25,
            'wind_speed': 12.5,
            'wind_direction': 180,
            'rain': 0,
            'timestamp': datetime.now().timestamp()
        }
        
        # Thêm vào database với key là timestamp
        key = str(int(datetime.now().timestamp()))
        weather_ref.child(key).set(sample_data)
        
        print(f"✅ Đã tạo dữ liệu với key: {key}")
        print(f"   Dữ liệu: {sample_data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi tạo dữ liệu mẫu: {e}")
        return False

def test_api_endpoints():
    """Test các API endpoints"""
    print("\n🌐 Test API endpoints...")
    
    import requests
    
    base_url = "http://localhost:5000"
    endpoints = [
        "/api/data-sources",
        "/api/weather-data?source=csv",
        "/api/weather-data?source=firebase",
        "/api/weather-summary?source=csv",
        "/api/weather-summary?source=firebase"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
                data = response.json()
                if 'source' in data:
                    print(f"   Source: {data['source']}")
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - Không thể kết nối (Flask app chưa chạy?)")
        except Exception as e:
            print(f"❌ {endpoint} - Lỗi: {e}")

def main():
    """Hàm chính"""
    print("🚀 Firebase Realtime Database Connection Test")
    print("=" * 60)
    
    # Test kết nối Firebase
    ref = test_firebase_connection()
    if not ref:
        print("\n❌ Không thể kết nối Firebase. Kiểm tra lại cấu hình.")
        return
    
    # Test dữ liệu
    test_firebase_data(ref)
    
    # Hỏi người dùng có muốn tạo dữ liệu mẫu không
    print("\n" + "=" * 60)
    choice = input("Bạn có muốn tạo dữ liệu mẫu cho path 'weather'? (y/n): ")
    if choice.lower() == 'y':
        create_sample_weather_data(ref)
    
    # Test API endpoints
    print("\n" + "=" * 60)
    choice = input("Bạn có muốn test API endpoints? (y/n): ")
    if choice.lower() == 'y':
        test_api_endpoints()
    
    print("\n✅ Test hoàn thành!")

if __name__ == "__main__":
    main() 