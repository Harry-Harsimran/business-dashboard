
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS marketing_spend;
DROP TABLE IF EXISTS kpi_targets;

CREATE TABLE customers (
    customer_id  INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    region       TEXT NOT NULL,          
    signup_month TEXT NOT NULL           
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date  TEXT NOT NULL,           
    category    TEXT NOT NULL,           
    quantity    INTEGER NOT NULL
    unit_price  REAL NOT NULL,           
    unit_cost   REAL NOT NULL,           
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE marketing_spend (
    month TEXT PRIMARY KEY,              
    spend REAL NOT NULL                  
);

CREATE TABLE kpi_targets (
    name             TEXT PRIMARY KEY,
    target           REAL NOT NULL,
    unit             TEXT NOT NULL,      -- '%', 'x', '₹'
    lower_is_better  INTEGER NOT NULL DEFAULT 0
);

INSERT INTO kpi_targets (name, target, unit, lower_is_better) VALUES
('Revenue growth (Q1 → Q4)', 15, '%', 0),
('Net margin', 25, '%', 0),
('Gross margin', 60, '%', 0),
('Monthly churn', 5, '%', 1),
('LTV : CAC ratio', 3, 'x', 0),
('Customer Acquisition Cost', 3500, '₹', 1),
('Customer LTV', 20000, '₹', 0),
('Average Order Value', 8000, '₹', 0);
