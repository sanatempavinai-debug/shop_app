from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    stock: int = 0
    category_id: Optional[int] = None
    emoji: str = "📦"
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    category_id: Optional[int] = None
    emoji: Optional[str] = None
    is_active: Optional[bool] = None

class Product(ProductBase):
    id: int
    image_path: Optional[str] = None
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)

class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemCreate]

class OrderStatusUpdate(BaseModel):
    status: str

class OrderItem(BaseModel):
    id: int
    product_id: Optional[int]
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

class Order(BaseModel):
    id: int
    order_code: str
    customer_name: str
    customer_phone: Optional[str]
    customer_address: Optional[str]
    total_amount: Decimal
    status: str
    slip_image_path: Optional[str]
    notes: Optional[str]
    items: List[OrderItem] = []
    created_at: datetime
    updated_at: datetime


class ShopSettingsUpdate(BaseModel):
    shop_name: Optional[str] = None
    shop_description: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class StockAdjust(BaseModel):
    amount: int
    reason: Optional[str] = None
