"""
sql_gen.py — SQL 生成模块
职责：拼接 Prompt（含 Few-shot 示例），调用 LLM 生成 SQL 语句
"""
from llm import chat
from database import get_schema


# Few-shot 示例：高质量的问题 → SQL 配对
FEWSHOT_EXAMPLES = """
示例1：
问题：所有商品按价格从高到低排序
SQL：SELECT * FROM products ORDER BY price DESC;

示例2：
问题：手机品类的平均价格是多少
SQL：SELECT AVG(price) FROM products WHERE category = '手机';

示例3：
问题：上个月销售额最高的商品是什么
SQL：SELECT p.name, SUM(o.total_amount) AS total_sales
FROM orders o
JOIN products p ON o.product_id = p.id
WHERE o.sale_date >= '2026-04-01' AND o.sale_date < '2026-05-01'
GROUP BY p.id
ORDER BY total_sales DESC
LIMIT 1;

示例4：
问题：每个用户的消费总额
SQL：SELECT u.name, COALESCE(SUM(o.total_amount), 0) AS total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name
ORDER BY total_spent DESC;

示例5：
问题：耳机品类的平均价格
SQL：SELECT category, AVG(price) AS avg_price FROM products WHERE category = '耳机';
"""


def generate_sql(user_question: str) -> str:
    """
    根据用户自然语言问题，生成 SQL 查询语句（含 Few-shot 示例）。
    """

    schema = get_schema()

    prompt = f"""
你是一个精通 SQLite 的数据分析师。

下面是一个电商数据库的表结构：

{schema}

以下是一些问题和对应正确 SQL 的示例，请仔细学习它们的写法：

{FEWSHOT_EXAMPLES}

现在用户提出了一个新问题，请根据表结构，参考示例的写法，写出对应的 SQLite 查询语句。

用户问题："{user_question}"

要求：
1. 只返回 SQL 语句，不要任何解释，不要 markdown 代码块标记
2. 只生成 SELECT 语句
3. 如果问题无法用 SQL 回答，返回：无法理解
4. 涉及时间的问题，日期格式用 YYYY-MM-DD。当前日期是 2026-05-10
"""

    sql = chat(prompt, system_prompt="你是一个专业的 SQL 分析师，只输出 SQL 语句。")
    return sql.strip()