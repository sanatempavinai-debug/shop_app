# 🛒 ລະບົບຮ້ານຄ້າອອນລາຍ — Python + FastAPI + PostgreSQL

## ໂຄງສ້າງໂປແກມ

```
shop_app/
├── main.py              ← FastAPI server + ທຸກ API routes
├── database.py          ← ການເຊື່ອມຕໍ່ PostgreSQL
├── models.py            ← Pydantic models
├── schema.sql           ← ສ້າງຕາຕະລາງ Database
├── requirements.txt     ← Python packages
├── .env.example         ← ຕົວຢ່າງ config
├── uploads/             ← ໄຟລ໌ QR + ສະລິບ + ຮູບສິນຄ້າ
└── templates/
    ├── index.html       ← ໜ້າຮ້ານ (ລູກຄ້າ)
    └── admin.html       ← Admin Panel

```

## ວິທີຕິດຕັ້ງ

### 1. ສ້າງ Database PostgreSQL
```sql
CREATE DATABASE shopdb;
```

### 2. ຕັ້ງຄ່າ Environment
```bash
cp .env.example .env
# ແກ້ໄຂ DATABASE_URL ໃຫ້ຖືກຕ້ອງ
```

### 3. ຕິດຕັ້ງ Python packages
```bash
pip install -r requirements.txt
```

### 4. ລັນ Server
```bash
python main.py
# ຫຼື
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. ເປີດໃຊ້ງານ
- ໜ້າຮ້ານ: http://localhost:8000
- Admin:   http://localhost:8000/admin
- API Doc: http://localhost:8000/docs

---

## ຄຸນສົມບັດ

### ໜ້າຮ້ານ (Customer)
- ✅ ເບິ່ງ ແລະ ຄົ້ນຫາສິນຄ້າ
- ✅ ກະຕ່າສິນຄ້າ (ເພີ່ມ/ລຶບ/ປ່ຽນຈຳນວນ)
- ✅ ສ້າງຄຳສັ່ງຊື້
- ✅ ຈ່າຍຜ່ານ QR Code
- ✅ ອັບໂຫລດສະລິບໂອນ

### Admin Panel
- ✅ Dashboard ສະຖິຕິ
- ✅ ຈັດການຄຳສັ່ງ (ຢືນຢັນ/ຍົກເລີກ)
- ✅ ຈັດການສິນຄ້າ (ເພີ່ມ/ແກ້ໄຂ/ລຶບ)
- ✅ ຈັດການໝວດໝູ່
- ✅ ອັບໂຫລດ QR ຮ້ານ
- ✅ ຕັ້ງຄ່າຮ້ານ

### Database (PostgreSQL)
- `shop_settings` — ຂໍ້ມູນຮ້ານ + QR path
- `categories` — ໝວດໝູ່ສິນຄ້າ
- `products` — ສິນຄ້າ + ລາຄາ + ສາງ
- `orders` — ຄຳສັ່ງຊື້ + ສະຖານະ
- `order_items` — ລາຍການໃນຄຳສັ່ງ
- `stock_logs` — ປະຫວັດການປ່ຽນສາງ

---

## API Endpoints ຫຼັກ

| Method | Path | ລາຍລະອຽດ |
|--------|------|-----------|
| GET | /api/products | ລາຍການສິນຄ້າ |
| POST | /api/products | ເພີ່ມສິນຄ້າ |
| PUT | /api/products/{id} | ແກ້ໄຂສິນຄ້າ |
| POST | /api/orders | ສ້າງຄຳສັ່ງ |
| GET | /api/orders | ລາຍການຄຳສັ່ງ |
| PATCH | /api/orders/{id}/status | ອັບເດດສະຖານະ |
| POST | /api/settings/qr | ອັບໂຫລດ QR |
| GET | /api/stats | ສະຖິຕິ Dashboard |
