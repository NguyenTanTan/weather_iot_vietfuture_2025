# 🚀 Hướng dẫn Deploy Dự án Weather Station

## 📋 Chuẩn bị trước khi deploy

### 1. **Cập nhật app.py cho production**
```python
# Thay đổi dòng cuối trong app.py
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

### 2. **Tạo file .env cho production**
```env
FLASK_ENV=production
DATABASE_URL=your_firebase_url
```

## 🌐 Các nền tảng deploy

### **Option 1: Render (Khuyến nghị - Miễn phí)**

1. **Đăng ký tài khoản:** https://render.com
2. **Tạo Web Service mới**
3. **Connect GitHub repository**
4. **Cấu hình:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment Variables:**
     - `FLASK_ENV=production`
     - `PORT=10000`

### **Option 2: Railway**

1. **Đăng ký:** https://railway.app
2. **Deploy từ GitHub**
3. **Tự động detect Python app**

### **Option 3: Heroku (Có phí)**

1. **Cài đặt Heroku CLI**
2. **Login và tạo app:**
```bash
heroku login
heroku create your-app-name
git push heroku main
```

### **Option 4: PythonAnywhere (Miễn phí)**

1. **Đăng ký:** https://www.pythonanywhere.com
2. **Upload files qua Files tab**
3. **Cấu hình WSGI file**

## 🔧 Cấu hình Firebase cho Production

### 1. **Tạo Service Account Key**
- Vào Firebase Console > Project Settings > Service Accounts
- Generate new private key
- Download file JSON

### 2. **Upload Service Account Key**
- **Render:** Upload qua Environment Variables
- **Railway:** Upload file trực tiếp
- **Heroku:** `heroku config:set FIREBASE_CREDENTIALS="$(cat firebase-service-account.json)"`

## 📁 Cấu trúc file cần thiết

```
vietfuture/
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── Procfile              # Heroku/Render config
├── runtime.txt           # Python version
├── firebase-service-account.json  # Firebase credentials
├── templates/
│   └── index.html
└── static/               # CSS, JS files (nếu có)
```

## 🚀 Bước deploy nhanh trên Render

1. **Push code lên GitHub**
2. **Vào Render.com > New Web Service**
3. **Connect GitHub repo**
4. **Cấu hình:**
   - Name: `vietfuture-weather`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. **Add Environment Variables:**
   - `FLASK_ENV=production`
6. **Deploy!**

## 🔍 Kiểm tra sau khi deploy

1. **Test API endpoints:**
   - `https://your-app.onrender.com/api/weather-data`
   - `https://your-app.onrender.com/api/weather-summary`

2. **Kiểm tra logs nếu có lỗi**

## 💡 Tips

- **Free tier limitations:** Có thể sleep sau 15 phút không hoạt động
- **Database:** Firebase Realtime Database hoạt động tốt cho production
- **SSL:** Tự động có HTTPS trên các nền tảng cloud
- **Custom domain:** Có thể thêm domain riêng

## 🆘 Troubleshooting

### Lỗi thường gặp:
1. **Module not found:** Kiểm tra requirements.txt
2. **Port error:** Đảm bảo sử dụng `os.environ.get('PORT', 5000)`
3. **Firebase auth:** Kiểm tra service account key
4. **Memory limit:** Tối ưu code nếu cần

### Debug commands:
```bash
# Xem logs
heroku logs --tail  # Heroku
railway logs        # Railway
# Render logs có trong dashboard
``` 