# Work Diary Management System

Ứng dụng **Quản lý Nhật ký Công việc Cá nhân** giúp lưu trữ, tìm kiếm và xuất báo cáo công việc hàng ngày.  
Giao diện thân thiện (Tkinter), hỗ trợ theme, lưu dữ liệu bằng SQLite, và có tính năng kiểm tra cập nhật từ GitHub.

---

## 📌 Tính năng chính
- Quản lý nhiều loại công việc:
  - Quản trị hệ thống mạng, camera, tổng đài điện thoại
  - Hỗ trợ và tư vấn người dùng về thiết bị, phần mềm
  - Phối hợp thực hiện các nhiệm vụ khác của phòng
- Lưu trữ và tìm kiếm nhanh
- Giới hạn số bản ghi gần đây (configurable)
- Tự động kiểm tra cập nhật qua API GitHub Releases
- Giao diện Tkinter đẹp, hỗ trợ nhiều theme

---

## 📂 Cấu trúc thư mục
work-diary/
│
├── data/ # Cơ sở dữ liệu SQLite
│ └── work_diary.db
├── src/ # Mã nguồn chính
├── config.json # Cấu hình ứng dụng
├── requirements.txt # Thư viện Python cần cài
├── main.py # Điểm khởi chạy ứng dụng
├── build.py # Script build exe
├── README.md # Tài liệu giới thiệu
└── BUILD.md # Hướng dẫn build
## 🚀 Cài đặt & chạy ứng dụng
### 1. Cài Python
- Tải và cài đặt Python 3.8+ từ [python.org](https://www.python.org/downloads/)
- Tick **Add Python to PATH** khi cài đặt

### 2. Cài thư viện
```bash
pip install -r requirements.txt
### Chạy file main
python main.py
### Build bằng file script(khuyến nghị)
python build.py

---

📌 Sau khi bạn lưu file `README.md` này vào thư mục `work-diary`, chỉ cần:
```bash
git add README.md
git commit -m "Add full README"
git push


