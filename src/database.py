"""
database.py — 数据库初始化与查询模块
职责：创建表结构、插入演示数据、执行查询
"""
import sqlite3
import os
from config import DATABASE_PATH


def get_connection():
    """获取数据库连接。如果 data/ 目录不存在就自动创建。"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果可以用字典方式访问
    return conn


def init_db():
    """初始化数据库：建表 + 插入演示数据（如果表已存在则跳过）"""
    conn = get_connection()
    cursor = conn.cursor()

    # ---- 建表 ----
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            total_amount REAL NOT NULL,
            sale_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # ---- 插入演示数据（只在表为空时才插入）----
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        _insert_demo_data(cursor)

    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")


def _insert_demo_data(cursor):
    """插入演示数据（私有函数，外部不调用）"""

    # 用户数据
    users = [
        ("张三", "13800001111"),
        ("李四", "13800002222"),
        ("王五", "13800003333"),
        ("赵六", "13800004444"),
        ("钱七", "13800005555"),
    ]
    cursor.executemany(
        "INSERT INTO users (name, phone) VALUES (?, ?)", users
    )

    # 商品数据
    products = [
        ("iPhone 15 Pro", "手机", 7999.00),
        ("华为 Mate 60", "手机", 6999.00),
        ("MacBook Air", "笔记本", 8999.00),
        ("ThinkPad X1", "笔记本", 9999.00),
        ("AirPods Pro", "耳机", 1899.00),
        ("索尼 WH-1000XM5", "耳机", 2499.00),
        ("iPad Air", "平板", 4799.00),
        ("小米平板 6", "平板", 1999.00),
    ]
    cursor.executemany(
        "INSERT INTO products (name, category, price) VALUES (?, ?, ?)", products
    )

    # 订单数据
    orders = [
        # 格式：(user_id, product_id, quantity, total_amount, sale_date)
        (1, 1, 1, 7999.00, "2026-04-05"),
        (1, 5, 2, 3798.00, "2026-04-10"),
        (2, 2, 1, 6999.00, "2026-04-08"),
        (2, 3, 1, 8999.00, "2026-04-15"),
        (3, 1, 1, 7999.00, "2026-04-12"),
        (3, 4, 1, 9999.00, "2026-04-18"),
        (3, 7, 1, 4799.00, "2026-04-20"),
        (4, 6, 1, 2499.00, "2026-04-02"),
        (4, 8, 3, 5997.00, "2026-04-22"),
        (5, 2, 2, 13998.00, "2026-04-25"),
        (1, 3, 1, 8999.00, "2026-05-01"),
        (2, 5, 1, 1899.00, "2026-05-03"),
        (3, 6, 2, 4998.00, "2026-05-05"),
        (4, 1, 1, 7999.00, "2026-05-06"),
        (5, 7, 1, 4799.00, "2026-05-08"),
    ]
    cursor.executemany(
        "INSERT INTO orders (user_id, product_id, quantity, total_amount, sale_date) "
        "VALUES (?, ?, ?, ?, ?)",
        orders,
    )


def execute_query(sql: str) -> list[dict]:
    """执行只读查询，返回结果列表。每行是一个字典。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    # 把 Row 对象转成字典
    return [dict(row) for row in rows]


def get_schema() -> str:
    """返回数据库表结构的文字描述，用于拼进 Prompt"""
    return """
数据库表结构如下（SQLite）：

1. users 表：用户信息
   - id: 用户ID (INTEGER, 主键)
   - name: 姓名 (TEXT)
   - phone: 手机号 (TEXT)

2. products 表：商品信息
   - id: 商品ID (INTEGER, 主键)
   - name: 商品名称 (TEXT)
   - category: 品类 (TEXT, 可选: 手机/笔记本/耳机/平板)
   - price: 单价 (REAL, 单位: 元)

3. orders 表：订单记录
   - id: 订单ID (INTEGER, 主键)
   - user_id: 用户ID (INTEGER, 外键关联 users.id)
   - product_id: 商品ID (INTEGER, 外键关联 products.id)
   - quantity: 购买数量 (INTEGER)
   - total_amount: 小计金额 (REAL, 单位: 元)
   - sale_date: 销售日期 (TEXT, 格式: YYYY-MM-DD)
"""