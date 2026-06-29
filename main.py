import os
import uuid
import random
import string
import hashlib
import secrets
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from database import get_db, init_db, close_pool
from models import (
    CategoryCreate, ProductCreate, ProductUpdate,
    OrderCreate, OrderStatusUpdate, ShopSettingsUpdate, StockAdjust
)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def gen_token() -> str:
    return secrets.token_hex(32)

class UserRegister(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    password: str

class UserLogin(BaseModel):
    phone: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Lao Shop API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.on_event("startup")
async def startup():
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    await close_pool()


def gen_order_code():
    ts = datetime.now().strftime("%y%m%d")
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORD-{ts}-{rand}"


# =================== SERVE FRONTEND ===================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    html_path = BASE_DIR / "templates" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    html_path = BASE_DIR / "templates" / "admin.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# =================== SHOP SETTINGS ===================

@app.get("/api/settings")
async def get_settings():
    async with get_db() as db:
        row = await db.fetchrow("SELECT * FROM shop_settings LIMIT 1")
        if not row:
            raise HTTPException(404, "ບໍ່ພົບການຕັ້ງຄ່າ")
        return dict(row)

@app.put("/api/settings")
async def update_settings(data: ShopSettingsUpdate):
    async with get_db() as db:
        row = await db.fetchrow("""
            UPDATE shop_settings SET
                shop_name = COALESCE($1, shop_name),
                shop_description = COALESCE($2, shop_description),
                phone = COALESCE($3, phone),
                address = COALESCE($4, address),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT id FROM shop_settings LIMIT 1)
            RETURNING *
        """, data.shop_name, data.shop_description, data.phone, data.address)
        return dict(row)

@app.post("/api/settings/qr")
async def upload_qr(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        raise HTTPException(400, "ຮອງຮັບແຕ່ .jpg, .png, .gif, .webp")
    filename = f"qr_{uuid.uuid4().hex}{ext}"
    filepath = UPLOAD_DIR / filename
    content = await file.read()
    filepath.write_bytes(content)
    async with get_db() as db:
        await db.execute(
            "UPDATE shop_settings SET qr_image_path=$1, updated_at=CURRENT_TIMESTAMP WHERE id=(SELECT id FROM shop_settings LIMIT 1)",
            f"/uploads/{filename}"
        )
    return {"qr_image_path": f"/uploads/{filename}"}


# =================== CATEGORIES ===================

@app.get("/api/categories")
async def list_categories():
    async with get_db() as db:
        rows = await db.fetch("SELECT * FROM categories ORDER BY name")
        return [dict(r) for r in rows]

@app.post("/api/categories", status_code=201)
async def create_category(data: CategoryCreate):
    async with get_db() as db:
        row = await db.fetchrow(
            "INSERT INTO categories (name, description) VALUES ($1,$2) RETURNING *",
            data.name, data.description
        )
        return dict(row)

@app.delete("/api/categories/{cat_id}")
async def delete_category(cat_id: int):
    async with get_db() as db:
        await db.execute("DELETE FROM categories WHERE id=$1", cat_id)
        return {"ok": True}


# =================== PRODUCTS ===================

@app.get("/api/products")
async def list_products(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    active_only: bool = True
):
    async with get_db() as db:
        conditions = []
        params = []
        idx = 1
        if active_only:
            conditions.append(f"p.is_active = TRUE")
        if category_id:
            conditions.append(f"p.category_id = ${idx}")
            params.append(category_id); idx += 1
        if search:
            conditions.append(f"(p.name ILIKE ${idx} OR p.description ILIKE ${idx})")
            params.append(f"%{search}%"); idx += 1
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = await db.fetch(f"""
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            {where}
            ORDER BY p.created_at DESC
        """, *params)
        return [dict(r) for r in rows]

@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    async with get_db() as db:
        row = await db.fetchrow("""
            SELECT p.*, c.name as category_name
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = $1
        """, product_id)
        if not row:
            raise HTTPException(404, "ບໍ່ພົບສິນຄ້າ")
        return dict(row)

@app.post("/api/products", status_code=201)
async def create_product(data: ProductCreate):
    async with get_db() as db:
        row = await db.fetchrow("""
            INSERT INTO products (name, description, price, stock, category_id, emoji, is_active)
            VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING *
        """, data.name, data.description, data.price, data.stock,
            data.category_id, data.emoji, data.is_active)
        return dict(row)

@app.put("/api/products/{product_id}")
async def update_product(product_id: int, data: ProductUpdate):
    async with get_db() as db:
        row = await db.fetchrow("""
            UPDATE products SET
                name = COALESCE($1, name),
                description = COALESCE($2, description),
                price = COALESCE($3, price),
                stock = COALESCE($4, stock),
                category_id = COALESCE($5, category_id),
                emoji = COALESCE($6, emoji),
                is_active = COALESCE($7, is_active),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $8 RETURNING *
        """, data.name, data.description, data.price, data.stock,
            data.category_id, data.emoji, data.is_active, product_id)
        if not row:
            raise HTTPException(404, "ບໍ່ພົບສິນຄ້າ")
        return dict(row)

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int):
    async with get_db() as db:
        await db.execute("UPDATE products SET is_active=FALSE WHERE id=$1", product_id)
        return {"ok": True}

@app.post("/api/products/{product_id}/image")
async def upload_product_image(product_id: int, file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    # ຖ້ຳບໍ່ມີ extension ໃຫ້ກວດ content_type
    if not ext and file.content_type:
        ct_map = {"image/jpeg":".jpg","image/png":".png","image/webp":".webp",
                  "image/gif":".gif","image/heic":".jpg","image/bmp":".jpg"}
        ext = ct_map.get(file.content_type, ".jpg")
    if ext not in [".jpg",".jpeg",".png",".webp",".gif",".bmp",".heic",".heif"]:
        raise HTTPException(400, f"ຮອງຮັບ .jpg .png .webp .gif (ໄດ້ຮັບ: {ext or 'unknown'})")
    filename = f"product_{product_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = UPLOAD_DIR / filename
    content = await file.read()
    filepath.write_bytes(content)
    async with get_db() as db:
        await db.execute(
            "UPDATE products SET image_path=$1, updated_at=CURRENT_TIMESTAMP WHERE id=$2",
            f"/uploads/{filename}", product_id
        )
    return {"image_path": f"/uploads/{filename}"}

@app.post("/api/products/{product_id}/stock")
async def adjust_stock(product_id: int, data: StockAdjust):
    async with get_db() as db:
        row = await db.fetchrow("SELECT stock FROM products WHERE id=$1", product_id)
        if not row:
            raise HTTPException(404, "ບໍ່ພົບສິນຄ້າ")
        new_stock = row["stock"] + data.amount
        if new_stock < 0:
            raise HTTPException(400, "ສາງບໍ່ພໍ")
        await db.execute(
            "UPDATE products SET stock=$1, updated_at=CURRENT_TIMESTAMP WHERE id=$2",
            new_stock, product_id
        )
        await db.execute(
            "INSERT INTO stock_logs (product_id, change_amount, reason) VALUES ($1,$2,$3)",
            product_id, data.amount, data.reason
        )
        return {"product_id": product_id, "new_stock": new_stock}


# =================== ORDERS ===================

@app.get("/api/orders")
async def list_orders(
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0
):
    async with get_db() as db:
        where = "WHERE o.status = $1" if status else ""
        params = [status] if status else []
        rows = await db.fetch(f"""
            SELECT o.*, 
                json_agg(json_build_object(
                    'id', oi.id,
                    'product_id', oi.product_id,
                    'product_name', oi.product_name,
                    'quantity', oi.quantity,
                    'unit_price', oi.unit_price,
                    'subtotal', oi.subtotal
                )) as items
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            {where}
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT {limit} OFFSET {offset}
        """, *params)
        return [dict(r) for r in rows]

@app.get("/api/orders/{order_id}")
async def get_order(order_id: int):
    async with get_db() as db:
        row = await db.fetchrow("""
            SELECT o.*,
                json_agg(json_build_object(
                    'id', oi.id, 'product_id', oi.product_id,
                    'product_name', oi.product_name, 'quantity', oi.quantity,
                    'unit_price', oi.unit_price, 'subtotal', oi.subtotal
                )) as items
            FROM orders o LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.id = $1 GROUP BY o.id
        """, order_id)
        if not row:
            raise HTTPException(404, "ບໍ່ພົບຄຳສັ່ງ")
        return dict(row)

@app.post("/api/orders", status_code=201)
async def create_order(data: OrderCreate):
    async with get_db() as db:
        async with db.transaction():
            total = 0
            items_data = []
            for item in data.items:
                prod = await db.fetchrow(
                    "SELECT id, name, price, stock FROM products WHERE id=$1 AND is_active=TRUE",
                    item.product_id
                )
                if not prod:
                    raise HTTPException(404, f"ບໍ່ພົບສິນຄ້າ ID {item.product_id}")
                if prod["stock"] < item.quantity:
                    raise HTTPException(400, f"ສາງ '{prod['name']}' ບໍ່ພໍ (ເຫຼືອ {prod['stock']})")
                subtotal = float(prod["price"]) * item.quantity
                total += subtotal
                items_data.append({
                    "product_id": prod["id"],
                    "product_name": prod["name"],
                    "quantity": item.quantity,
                    "unit_price": float(prod["price"]),
                    "subtotal": subtotal,
                })
            order_code = gen_order_code()
            order = await db.fetchrow("""
                INSERT INTO orders (order_code, customer_name, customer_phone,
                    customer_address, total_amount, notes)
                VALUES ($1,$2,$3,$4,$5,$6) RETURNING *
            """, order_code, data.customer_name, data.customer_phone,
                data.customer_address, total, data.notes)
            for it in items_data:
                await db.execute("""
                    INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, subtotal)
                    VALUES ($1,$2,$3,$4,$5,$6)
                """, order["id"], it["product_id"], it["product_name"],
                    it["quantity"], it["unit_price"], it["subtotal"])
                await db.execute(
                    "UPDATE products SET stock = stock - $1 WHERE id=$2",
                    it["quantity"], it["product_id"]
                )
            return {"order_id": order["id"], "order_code": order_code, "total": total}

@app.patch("/api/orders/{order_id}/status")
async def update_order_status(order_id: int, data: OrderStatusUpdate):
    valid = ['pending','paid','processing','shipped','completed','cancelled']
    if data.status not in valid:
        raise HTTPException(400, f"Status ຕ້ອງເປັນ: {', '.join(valid)}")
    async with get_db() as db:
        row = await db.fetchrow(
            "UPDATE orders SET status=$1, updated_at=CURRENT_TIMESTAMP WHERE id=$2 RETURNING *",
            data.status, order_id
        )
        if not row:
            raise HTTPException(404, "ບໍ່ພົບຄຳສັ່ງ")
        return dict(row)

@app.post("/api/orders/{order_id}/slip")
async def upload_slip(order_id: int, file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(400, "ຮອງຮັບແຕ່ .jpg, .png, .webp")
    filename = f"slip_{order_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = UPLOAD_DIR / filename
    content = await file.read()
    filepath.write_bytes(content)
    async with get_db() as db:
        await db.execute(
            "UPDATE orders SET slip_image_path=$1, updated_at=CURRENT_TIMESTAMP WHERE id=$2",
            f"/uploads/{filename}", order_id
        )
    return {"slip_image_path": f"/uploads/{filename}"}



# =================== USERS / AUTH ===================

@app.post("/api/auth/register", status_code=201)
async def register(data: UserRegister):
    async with get_db() as db:
        exists = await db.fetchrow("SELECT id FROM users WHERE phone=$1", data.phone)
        if exists:
            raise HTTPException(400, "ເບີໂທນີ້ລົງທະບຽນແລ້ວ")
        hashed = hash_password(data.password)
        token = gen_token()
        user = await db.fetchrow("""
            INSERT INTO users (name, phone, email, password_hash, token)
            VALUES ($1,$2,$3,$4,$5) RETURNING id, name, phone, email, address, created_at
        """, data.name, data.phone, data.email, hashed, token)
        return {"token": token, "user": dict(user)}

@app.post("/api/auth/login")
async def login(data: UserLogin):
    async with get_db() as db:
        user = await db.fetchrow(
            "SELECT * FROM users WHERE phone=$1", data.phone)
        if not user:
            raise HTTPException(401, "ບໍ່ພົບບັນຊີ — ກາລຸນາລົງທະບຽນກ່ອນ")
        if user["password_hash"] != hash_password(data.password):
            raise HTTPException(401, "ລະຫັດຜ່ານບໍ່ຖືກຕ້ອງ")
        token = gen_token()
        await db.execute("UPDATE users SET token=$1 WHERE id=$2", token, user["id"])
        return {"token": token, "user": {
            "id": user["id"], "name": user["name"],
            "phone": user["phone"], "email": user["email"],
            "address": user["address"]
        }}

@app.get("/api/auth/me")
async def get_me(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "ກາລຸນາ Login ກ່ອນ")
    token = authorization.split(" ")[1]
    async with get_db() as db:
        user = await db.fetchrow(
            "SELECT id,name,phone,email,address,created_at FROM users WHERE token=$1", token)
        if not user:
            raise HTTPException(401, "Session ໝົດອາຍຸ — ກາລຸນາ Login ຄືນ")
        orders = await db.fetchval("SELECT COUNT(*) FROM orders WHERE customer_phone=$1", user["phone"])
        return {**dict(user), "total_orders": orders}

@app.put("/api/auth/me")
async def update_me(data: UserUpdate, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "ກາລຸນາ Login ກ່ອນ")
    token = authorization.split(" ")[1]
    async with get_db() as db:
        user = await db.fetchrow("SELECT id FROM users WHERE token=$1", token)
        if not user:
            raise HTTPException(401, "Session ໝົດອາຍຸ")
        await db.execute("""
            UPDATE users SET
                name=COALESCE($1,name),
                email=COALESCE($2,email),
                address=COALESCE($3,address)
            WHERE id=$4
        """, data.name, data.email, data.address, user["id"])
        updated = await db.fetchrow(
            "SELECT id,name,phone,email,address FROM users WHERE id=$1", user["id"])
        return dict(updated)

@app.post("/api/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        async with get_db() as db:
            await db.execute("UPDATE users SET token=NULL WHERE token=$1", token)
    return {"ok": True}


# =================== DASHBOARD STATS ===================

@app.get("/api/stats")
async def get_stats():
    async with get_db() as db:
        total_orders = await db.fetchval("SELECT COUNT(*) FROM orders")
        total_revenue = await db.fetchval(
            "SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE status IN ('paid','completed')"
        )
        pending_orders = await db.fetchval("SELECT COUNT(*) FROM orders WHERE status='pending'")
        total_products = await db.fetchval("SELECT COUNT(*) FROM products WHERE is_active=TRUE")
        low_stock = await db.fetch(
            "SELECT name, stock FROM products WHERE stock <= 5 AND is_active=TRUE ORDER BY stock"
        )
        recent = await db.fetch("""
            SELECT order_code, customer_name, total_amount, status, created_at
            FROM orders ORDER BY created_at DESC LIMIT 5
        """)
        return {
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "pending_orders": pending_orders,
            "total_products": total_products,
            "low_stock_products": [dict(r) for r in low_stock],
            "recent_orders": [dict(r) for r in recent],
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
