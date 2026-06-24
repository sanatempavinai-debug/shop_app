-- ຕາຕະລາງຮ້ານຄ້າ
CREATE TABLE IF NOT EXISTS shop_settings (
    id SERIAL PRIMARY KEY,
    shop_name VARCHAR(200) NOT NULL DEFAULT 'ຮ້ານຂອງຂ້ອຍ',
    shop_description TEXT,
    phone VARCHAR(50),
    address TEXT,
    qr_image_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ໝວດໝູ່ສິນຄ້າ
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ສິນຄ້າ
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(15,2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    emoji VARCHAR(10) DEFAULT '📦',
    image_path VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ຄຳສັ່ງຊື້
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_code VARCHAR(20) UNIQUE NOT NULL,
    customer_name VARCHAR(200) NOT NULL,
    customer_phone VARCHAR(50),
    customer_address TEXT,
    total_amount DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    slip_image_path VARCHAR(500),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT status_check CHECK (status IN ('pending','paid','processing','shipped','completed','cancelled'))
);

-- ລາຍການໃນຄຳສັ່ງ
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_name VARCHAR(200) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    subtotal DECIMAL(15,2) NOT NULL
);

-- ປະຫວັດການເຄື່ອນໄຫວສາງ
CREATE TABLE IF NOT EXISTS stock_logs (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    change_amount INTEGER NOT NULL,
    reason VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ຂໍ້ມູນຕົວຢ່າງ (ໃສ່ສະເພາະຖ້ຳຕາຕະລາງຫວ່າງ)
INSERT INTO shop_settings (shop_name, shop_description, phone)
SELECT 'ຮ້ານລາວສົ່ງຂອງ', 'ສິນຄ້າທົ່ວໄປ ອອນລາຍ', '020-00000000'
WHERE NOT EXISTS (SELECT 1 FROM shop_settings);

INSERT INTO categories (name)
SELECT name FROM (VALUES ('ເຄື່ອງດື່ມ'),('ຂອງຝາກ'),('ເຄື່ອງນຸ່ງ'),('ສິນຄ້າທົ່ວໄປ')) AS t(name)
WHERE NOT EXISTS (SELECT 1 FROM categories);

INSERT INTO products (name, price, stock, category_id, emoji)
SELECT p.name, p.price, p.stock, c.id, p.emoji
FROM (VALUES
  ('ກາເຟ Lao Arabica', 45000, 50, 'ເຄື່ອງດື່ມ', '☕'),
  ('ນ້ຳດື່ມ 1.5L',      8000, 100, 'ເຄື່ອງດື່ມ', '💧'),
  ('ຂອງຝາກລາວ Set',   120000,  20, 'ຂອງຝາກ',    '🎁'),
  ('ເສີ້ຍ Batik ລາວ',  95000,  15, 'ເຄື່ອງນຸ່ງ', '👕'),
  ('ຜ້າຊິ້ນລາວ',       180000,   8, 'ເຄື່ອງນຸ່ງ', '🧣'),
  ('ສາບູ Lao Herb',    35000,  60, 'ສິນຄ້າທົ່ວໄປ','🌿')
) AS p(name, price, stock, cat_name, emoji)
JOIN categories c ON c.name = p.cat_name
WHERE NOT EXISTS (SELECT 1 FROM products);
