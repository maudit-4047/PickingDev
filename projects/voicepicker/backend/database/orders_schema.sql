
CREATE TABLE orders (
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	customer_name VARCHAR(100) NOT NULL,       -- or store name
	status VARCHAR(20) DEFAULT 'created',      -- created, picking, dispatched
	created_at TIMESTAMP DEFAULT NOW(),
	updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	order_id BIGINT REFERENCES orders(id) ON DELETE CASCADE,
	item_code VARCHAR(100) NOT NULL,
	requested_qty INT NOT NULL,
	picked_qty INT DEFAULT 0,
	status VARCHAR(20) DEFAULT 'pending'       -- pending, picked, short
);
