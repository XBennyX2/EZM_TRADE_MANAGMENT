-- Sample data for EZM Trade Management System

-- Insert sample stores
INSERT OR IGNORE INTO store_store (name, address, phone_number) VALUES
('Main Branch', 'Bole, Addis Ababa', '+251911111111'),
('Piazza Branch', 'Piazza, Addis Ababa', '+251911111112'),
('Merkato Branch', 'Merkato, Addis Ababa', '+251911111113'),
('CMC Branch', 'CMC, Addis Ababa', '+251911111114'),
('Kazanchis Branch', 'Kazanchis, Addis Ababa', '+251911111115');

-- Insert sample supplier
INSERT OR IGNORE INTO Inventory_supplier (name, contact_person, email, phone, address) VALUES
('Default Supplier', 'Supply Manager', 'supplier@example.com', '+251911000000', 'Addis Ababa, Ethiopia');

-- Insert sample products
INSERT OR IGNORE INTO Inventory_product (name, category, description, price, material, size, variation, product_type, supplier_company, batch_number, room, shelf, floor, storing_condition) VALUES
-- Electronics
('Samsung Galaxy A54', 'electronics', 'Latest Android smartphone with 128GB storage', 25000.00, 'Aluminum and Glass', 'medium', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH1001', 'Room 1', 'Shelf 1', 1, 'normal'),
('iPhone 14', 'electronics', 'Apple iPhone with advanced camera system', 65000.00, 'Aluminum and Ceramic Shield', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH1002', 'Room 1', 'Shelf 2', 1, 'normal'),
('Dell Laptop Inspiron 15', 'electronics', 'Business laptop with Intel i5 processor', 45000.00, 'Plastic and Metal', 'large', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH1003', 'Room 1', 'Shelf 3', 1, 'normal'),
('HP Printer LaserJet', 'electronics', 'Wireless laser printer for office use', 8500.00, 'Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH1004', 'Room 1', 'Shelf 4', 1, 'normal'),
('Sony Headphones WH-1000XM4', 'electronics', 'Noise-canceling wireless headphones', 15000.00, 'Plastic and Metal', 'small', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH1005', 'Room 1', 'Shelf 5', 1, 'normal'),
('Samsung 55" Smart TV', 'electronics', '4K UHD Smart TV with HDR support', 35000.00, 'Plastic and Metal', 'extra_large', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH1006', 'Room 1', 'Shelf 6', 1, 'normal'),
('iPad Air', 'electronics', 'Apple tablet with 64GB storage', 28000.00, 'Aluminum', 'medium', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH1007', 'Room 1', 'Shelf 7', 1, 'normal'),
('Canon DSLR Camera', 'electronics', 'Professional camera with 24MP sensor', 42000.00, 'Metal and Plastic', 'medium', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH1008', 'Room 1', 'Shelf 8', 1, 'normal'),
('Bluetooth Speaker JBL', 'electronics', 'Portable wireless speaker', 3500.00, 'Plastic and Fabric', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH1009', 'Room 1', 'Shelf 9', 1, 'normal'),
('Gaming Mouse Logitech', 'electronics', 'High-precision gaming mouse', 2200.00, 'Plastic', 'small', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH1010', 'Room 1', 'Shelf 10', 1, 'normal'),

-- Clothing
('Men''s Cotton T-Shirt', 'clothing', 'Comfortable cotton t-shirt in various colors', 450.00, '100% Cotton', 'medium', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH2001', 'Room 2', 'Shelf 1', 2, 'normal'),
('Women''s Jeans', 'clothing', 'Slim fit denim jeans', 1200.00, 'Denim Cotton', 'medium', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH2002', 'Room 2', 'Shelf 2', 2, 'normal'),
('Leather Jacket', 'clothing', 'Genuine leather jacket for men', 3500.00, 'Genuine Leather', 'large', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH2003', 'Room 2', 'Shelf 3', 2, 'normal'),
('Running Shoes Nike', 'clothing', 'Athletic shoes for running and sports', 2800.00, 'Synthetic and Mesh', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH2004', 'Room 2', 'Shelf 4', 2, 'normal'),
('Winter Coat', 'clothing', 'Warm winter coat with hood', 4200.00, 'Polyester and Down', 'large', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH2005', 'Room 2', 'Shelf 5', 2, 'normal'),
('Formal Shirt', 'clothing', 'Business formal shirt for men', 850.00, 'Cotton Blend', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH2006', 'Room 2', 'Shelf 6', 2, 'normal'),
('Summer Dress', 'clothing', 'Light summer dress for women', 1800.00, 'Cotton and Polyester', 'medium', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH2007', 'Room 2', 'Shelf 7', 2, 'normal'),
('Sports Bra', 'clothing', 'High-support sports bra', 650.00, 'Polyester and Spandex', 'small', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH2008', 'Room 2', 'Shelf 8', 2, 'normal'),
('Casual Sneakers', 'clothing', 'Comfortable casual sneakers', 1500.00, 'Canvas and Rubber', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH2009', 'Room 2', 'Shelf 9', 2, 'normal'),
('Wool Sweater', 'clothing', 'Warm wool sweater for winter', 2200.00, 'Wool Blend', 'medium', 'Color: Green', 'finished_product', 'Default Supplier', 'BATCH2010', 'Room 2', 'Shelf 10', 2, 'normal'),

-- Home & Garden
('Coffee Table', 'home_garden', 'Modern wooden coffee table', 5500.00, 'Solid Wood', 'large', 'Color: Brown', 'finished_product', 'Default Supplier', 'BATCH3001', 'Room 3', 'Shelf 1', 1, 'normal'),
('Garden Hose 50ft', 'home_garden', 'Flexible garden hose with spray nozzle', 1200.00, 'Rubber and Plastic', 'medium', 'Color: Green', 'finished_product', 'Default Supplier', 'BATCH3002', 'Room 3', 'Shelf 2', 1, 'normal'),
('LED Desk Lamp', 'home_garden', 'Adjustable LED desk lamp with USB charging', 2200.00, 'Metal and Plastic', 'small', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH3003', 'Room 3', 'Shelf 3', 1, 'normal'),
('Flower Pots Set', 'home_garden', 'Set of 5 ceramic flower pots', 800.00, 'Ceramic', 'small', 'Color: Brown', 'finished_product', 'Default Supplier', 'BATCH3004', 'Room 3', 'Shelf 4', 1, 'normal'),
('Kitchen Knife Set', 'home_garden', 'Professional kitchen knife set with block', 3200.00, 'Stainless Steel', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3005', 'Room 3', 'Shelf 5', 1, 'normal'),
('Bed Sheets Queen', 'home_garden', 'Egyptian cotton bed sheet set', 2800.00, 'Egyptian Cotton', 'large', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH3006', 'Room 3', 'Shelf 6', 1, 'normal'),
('Wall Mirror', 'home_garden', 'Decorative wall mirror 24x36 inches', 1800.00, 'Glass and Wood Frame', 'large', '', 'finished_product', 'Default Supplier', 'BATCH3007', 'Room 3', 'Shelf 7', 1, 'normal'),
('Garden Tools Set', 'home_garden', 'Complete gardening tools set', 2500.00, 'Steel and Wood', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3008', 'Room 3', 'Shelf 8', 1, 'normal'),
('Dining Chair Set', 'home_garden', 'Set of 4 dining chairs', 4800.00, 'Wood and Fabric', 'large', 'Color: Brown', 'finished_product', 'Default Supplier', 'BATCH3009', 'Room 3', 'Shelf 9', 1, 'normal'),
('Kitchen Blender', 'home_garden', 'High-speed kitchen blender', 3200.00, 'Plastic and Steel', 'medium', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH3010', 'Room 3', 'Shelf 10', 1, 'normal'),

-- Books
('Python Programming Guide', 'books', 'Complete guide to Python programming', 850.00, 'Paper', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH4001', 'Room 4', 'Shelf 1', 1, 'normal'),
('Ethiopian History Book', 'books', 'Comprehensive Ethiopian history', 650.00, 'Paper', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH4002', 'Room 4', 'Shelf 2', 1, 'normal'),
('Business Management', 'books', 'Modern business management principles', 1200.00, 'Paper', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH4003', 'Room 4', 'Shelf 3', 1, 'normal'),
('Cookbook Ethiopian Cuisine', 'books', 'Traditional Ethiopian recipes', 750.00, 'Paper', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH4004', 'Room 4', 'Shelf 4', 1, 'normal'),
('Children''s Story Book', 'books', 'Illustrated children''s stories', 350.00, 'Paper', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4005', 'Room 4', 'Shelf 5', 1, 'normal'),
('English Dictionary', 'books', 'Comprehensive English dictionary', 950.00, 'Paper', 'large', '', 'finished_product', 'Default Supplier', 'BATCH4006', 'Room 4', 'Shelf 6', 1, 'normal'),
('Mathematics Textbook', 'books', 'Advanced mathematics textbook', 1100.00, 'Paper', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH4007', 'Room 4', 'Shelf 7', 1, 'normal'),
('Art and Design Book', 'books', 'Modern art and design concepts', 1400.00, 'Paper', 'large', '', 'finished_product', 'Default Supplier', 'BATCH4008', 'Room 4', 'Shelf 8', 1, 'normal'),
('Science Encyclopedia', 'books', 'Complete science encyclopedia', 1800.00, 'Paper', 'large', '', 'finished_product', 'Default Supplier', 'BATCH4009', 'Room 4', 'Shelf 9', 1, 'normal'),
('Fiction Novel', 'books', 'Bestselling fiction novel', 550.00, 'Paper', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4010', 'Room 4', 'Shelf 10', 1, 'normal'),

-- Sports
('Football Soccer Ball', 'sports', 'Official size soccer ball', 850.00, 'Synthetic Leather', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH5001', 'Room 5', 'Shelf 1', 1, 'normal'),
('Basketball', 'sports', 'Professional basketball', 1200.00, 'Rubber', 'medium', 'Color: Orange', 'finished_product', 'Default Supplier', 'BATCH5002', 'Room 5', 'Shelf 2', 1, 'normal'),
('Tennis Racket', 'sports', 'Professional tennis racket', 3500.00, 'Carbon Fiber', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH5003', 'Room 5', 'Shelf 3', 1, 'normal'),
('Yoga Mat', 'sports', 'Non-slip yoga exercise mat', 1800.00, 'PVC', 'large', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH5004', 'Room 5', 'Shelf 4', 1, 'normal'),
('Dumbbells Set', 'sports', 'Adjustable dumbbells 5-50 lbs', 8500.00, 'Cast Iron', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH5005', 'Room 5', 'Shelf 5', 1, 'normal'),
('Swimming Goggles', 'sports', 'Anti-fog swimming goggles', 450.00, 'Silicone and Plastic', 'small', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH5006', 'Room 5', 'Shelf 6', 1, 'normal'),
('Bicycle Helmet', 'sports', 'Safety bicycle helmet', 2200.00, 'Polycarbonate', 'medium', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH5007', 'Room 5', 'Shelf 7', 1, 'normal'),
('Running Shorts', 'sports', 'Moisture-wicking running shorts', 650.00, 'Polyester', 'medium', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH5008', 'Room 5', 'Shelf 8', 1, 'normal'),
('Golf Club Set', 'sports', 'Complete golf club set', 12000.00, 'Steel and Graphite', 'large', '', 'finished_product', 'Default Supplier', 'BATCH5009', 'Room 5', 'Shelf 9', 1, 'normal'),
('Table Tennis Paddle', 'sports', 'Professional table tennis paddle', 1500.00, 'Wood and Rubber', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH5010', 'Room 5', 'Shelf 10', 1, 'normal'),

-- Beauty
('Face Moisturizer', 'beauty', 'Daily face moisturizer with SPF', 1200.00, 'Cosmetic Formula', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6001', 'Room 2', 'Shelf 11', 2, 'normal'),
('Shampoo 500ml', 'beauty', 'Nourishing shampoo for all hair types', 450.00, 'Cosmetic Formula', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH6002', 'Room 2', 'Shelf 12', 2, 'normal'),
('Lipstick Set', 'beauty', 'Set of 6 matte lipsticks', 1800.00, 'Cosmetic Formula', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH6003', 'Room 2', 'Shelf 13', 2, 'normal'),
('Perfume 100ml', 'beauty', 'Long-lasting eau de parfum', 3500.00, 'Fragrance', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6004', 'Room 2', 'Shelf 14', 2, 'normal'),
('Face Mask Pack', 'beauty', 'Hydrating face mask pack of 10', 850.00, 'Cosmetic Formula', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6005', 'Room 2', 'Shelf 15', 2, 'normal'),
('Hair Conditioner', 'beauty', 'Deep conditioning hair treatment', 650.00, 'Cosmetic Formula', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH6006', 'Room 2', 'Shelf 16', 2, 'normal'),
('Nail Polish Set', 'beauty', 'Set of 12 nail polish colors', 1400.00, 'Cosmetic Formula', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6007', 'Room 2', 'Shelf 17', 2, 'normal'),
('Body Lotion', 'beauty', 'Moisturizing body lotion 400ml', 750.00, 'Cosmetic Formula', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH6008', 'Room 2', 'Shelf 18', 2, 'normal'),
('Sunscreen SPF 50', 'beauty', 'Broad spectrum sunscreen', 950.00, 'Cosmetic Formula', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6009', 'Room 2', 'Shelf 19', 2, 'normal'),
('Hair Styling Gel', 'beauty', 'Strong hold hair styling gel', 550.00, 'Cosmetic Formula', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6010', 'Room 2', 'Shelf 20', 2, 'normal');
