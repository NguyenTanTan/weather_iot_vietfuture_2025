# Weather Data Dashboard

Dự án web Python để hiển thị và theo dõi dữ liệu thời tiết từ cảm biến với giao diện dashboard đẹp mắt.

## Tính năng

- 🌤️ Dashboard thời tiết hiện đại với dữ liệu thời gian thực
- 📊 Biểu đồ tương tác cho nhiệt độ, độ ẩm, áp suất và gió
- 📈 Thống kê chi tiết (nhiệt độ cao/thấp, trung bình, tổng lượng mưa)
- 🔄 Tự động làm mới dữ liệu (có thể bật/tắt)
- 📱 Responsive design cho mobile và desktop
- ⚡ Hiển thị dữ liệu real-time từ CSV
- 🎨 Giao diện hiện đại với Bootstrap 5 và Chart.js

## Dữ liệu được hiển thị

- **Nhiệt độ** (°C) - hiện tại, cao nhất, thấp nhất, trung bình
- **Độ ẩm** (%) - hiện tại và trung bình
- **Áp suất khí quyển** (hPa)
- **Gió** - tốc độ (km/h) và hướng (độ)
- **Lượng mưa** (mm) - tổng lượng mưa trong ngày
- **Thời gian** - cập nhật cuối cùng

## Cài đặt

### 1. Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Chuẩn bị dữ liệu

Đặt file CSV chứa dữ liệu thời tiết vào thư mục gốc với tên:
```
Firebase Data - Historical Data Final.csv
```

Cấu trúc CSV cần có các cột:
- `Data timestamp` - timestamp (milliseconds)
- `temperature` - nhiệt độ (°C)
- `humidity` - độ ẩm (%)
- `pressure` - áp suất (hPa)
- `rain` - lượng mưa
- `sustain_windDir` - hướng gió ổn định
- `sustain_windSpd` - tốc độ gió ổn định
- `gust_windDir` - hướng gió giật
- `gust_windSpd` - tốc độ gió giật
- `Date` - ngày tháng

### 3. Chạy ứng dụng

```bash
python app.py
```

Ứng dụng sẽ chạy tại: http://localhost:5000

## API Endpoints

### GET `/api/weather-data`
Lấy dữ liệu thời tiết gần đây và thống kê

**Response:**
```json
{
  "success": true,
  "data": [...],
  "stats": {
    "total_records": 847,
    "latest_temperature": 26.5,
    "latest_humidity": 85.4,
    "avg_temperature": 24.2,
    "max_temperature": 33.5,
    "min_temperature": 16.6
  },
  "count": 50
}
```

### GET `/api/weather-summary`
Lấy tổng quan thời tiết hiện tại

**Response:**
```json
{
  "success": true,
  "summary": {
    "current_temp": 26.5,
    "current_humidity": 85.4,
    "current_pressure": 1012,
    "today_high": 30.2,
    "today_low": 22.1,
    "wind_speed": 5.2,
    "wind_direction": 180,
    "rain_today": 0
  }
}
```

### GET `/api/weather-chart-data`
Lấy dữ liệu cho biểu đồ

**Response:**
```json
{
  "success": true,
  "data": {
    "timestamps": ["2025-02-16 12:00", "2025-02-16 12:05"],
    "temperature": [26.5, 26.8],
    "humidity": [85.4, 85.1],
    "pressure": [1012, 1012],
    "wind_speed": [5.2, 4.8]
  }
}
```

## Cấu trúc dự án

```
vietfuture/
├── app.py                          # Flask application chính
├── config.py                       # Cấu hình ứng dụng
├── requirements.txt                # Python dependencies
├── sample_data.py                  # Script tạo dữ liệu mẫu (cho Firebase)
├── README.md                       # Hướng dẫn này
├── .gitignore                      # Loại trừ file không cần thiết
├── templates/
│   └── index.html                  # Giao diện dashboard
└── Firebase Data - Historical Data Final.csv  # Dữ liệu thời tiết
```

## Tính năng nâng cao

### Biểu đồ tương tác
- Biểu đồ nhiệt độ và độ ẩm theo thời gian
- Biểu đồ áp suất và tốc độ gió
- Hover để xem chi tiết
- Zoom và pan

### Thống kê thông minh
- Tính toán nhiệt độ cao/thấp trong ngày
- Trung bình nhiệt độ và độ ẩm
- Tổng lượng mưa trong ngày
- Hướng gió chủ đạo

### Auto-refresh
- Tự động làm mới dữ liệu mỗi 30 giây
- Có thể bật/tắt tính năng
- Hiển thị thời gian cập nhật cuối

## Tùy chỉnh

### Thay đổi tần suất cập nhật
Trong file `templates/index.html`, thay đổi:
```javascript
autoRefreshInterval = setInterval(refreshData, 30000); // 30 giây
```

### Thay đổi số lượng dữ liệu hiển thị
Trong file `app.py`, thay đổi:
```python
latest_data = df.tail(50).to_dict('records')  # 50 bản ghi gần nhất
```

### Thay đổi tên file CSV
Trong file `app.py`, thay đổi:
```python
df = pd.read_csv('your-weather-data.csv')
```

## Troubleshooting

### Lỗi "File CSV not found"
- Đảm bảo file CSV đã được đặt trong thư mục gốc
- Kiểm tra tên file chính xác

### Lỗi "Invalid data format"
- Kiểm tra cấu trúc CSV có đúng định dạng
- Đảm bảo các cột cần thiết đã có

### Lỗi "Chart not displaying"
- Kiểm tra kết nối internet để tải Chart.js
- Kiểm tra console browser để xem lỗi JavaScript

## License

MIT License - Tự do sử dụng và chỉnh sửa. 