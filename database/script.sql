CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

-- ============================================
-- 2. ПОЛЬЗОВАТЕЛИ
-- ============================================
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    login VARCHAR(50) NOT NULL UNIQUE,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    role_id INT NOT NULL,
    CONSTRAINT fk_users_role FOREIGN KEY (role_id) 
        REFERENCES roles(role_id) ON DELETE RESTRICT
);

-- ============================================
-- 3. КАТЕГОРИИ (Детская/Женская/Мужская обувь)
-- ============================================
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

-- ============================================
-- 4. ПОДКАТЕГОРИИ (Кроссовки/Сапоги/Босоножки/Туфли/Ботинки)
-- ============================================
CREATE TABLE subcategories (
    subcategory_id SERIAL PRIMARY KEY,
    subcategory_name VARCHAR(100) NOT NULL UNIQUE
);

-- ============================================
-- 5. ПРОИЗВОДИТЕЛИ (бренды)
-- ============================================
CREATE TABLE manufacturers (
    manufacturer_id SERIAL PRIMARY KEY,
    manufacturer_name VARCHAR(100) NOT NULL UNIQUE
);

-- ============================================
-- 6. СПРАВОЧНИК РАЗМЕРОВ (из Sizes_import)
-- ============================================
CREATE TABLE sizes (
    size_id SERIAL PRIMARY KEY,
    size_value DECIMAL(3, 1) NOT NULL UNIQUE
);

-- ============================================
-- 7. ТОВАРЫ
-- ============================================
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category_id INT NOT NULL,
    subcategory_id INT NOT NULL,
    manufacturer_id INT NOT NULL,
    composition VARCHAR(1000),
    description TEXT,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    image_path VARCHAR(255),
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) 
        REFERENCES categories(category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_products_subcategory FOREIGN KEY (subcategory_id) 
        REFERENCES subcategories(subcategory_id) ON DELETE RESTRICT,
    CONSTRAINT fk_products_manufacturer FOREIGN KEY (manufacturer_id) 
        REFERENCES manufacturers(manufacturer_id) ON DELETE RESTRICT
);

-- ============================================
-- 8. ОСТАТКИ НА СКЛАДЕ (сочетание товар+размер)
-- ============================================
CREATE TABLE product_sizes (
    product_size_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    size_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    CONSTRAINT fk_ps_product FOREIGN KEY (product_id) 
        REFERENCES products(product_id) ON DELETE CASCADE,
    CONSTRAINT fk_ps_size FOREIGN KEY (size_id) 
        REFERENCES sizes(size_id) ON DELETE RESTRICT,
    CONSTRAINT uq_product_size UNIQUE (product_id, size_id)
);

-- ============================================
-- 9. ЗАКАЗЫ
-- ============================================
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    client_last_name VARCHAR(50) NOT NULL,
    client_first_name VARCHAR(50) NOT NULL,
    client_middle_name VARCHAR(50),
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0
);

-- ============================================
-- 10. СОСТАВ ЗАКАЗА
-- ============================================
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    product_size_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    CONSTRAINT fk_oi_order FOREIGN KEY (order_id) 
        REFERENCES orders(order_id) ON DELETE CASCADE,
    CONSTRAINT fk_oi_product_size FOREIGN KEY (product_size_id) 
        REFERENCES product_sizes(product_size_id) ON DELETE RESTRICT
);