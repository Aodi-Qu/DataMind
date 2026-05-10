"""
safety.py — SQL 安全校验模块
职责：拦截危险操作、校验语法、确保只读
"""
import sqlite3
import re


# 危险关键词黑名单
DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
    "CREATE", "TRUNCATE", "REPLACE", "GRANT", "REVOKE",
]


def validate(sql: str) -> tuple[bool, str]:
    """
    校验 SQL 是否安全可执行。

    参数:
        sql: LLM 生成的 SQL 语句

    返回:
        (是否通过, 错误信息)
        - 通过: (True, SQL语句)
        - 失败: (False, 错误原因)
    """

    # 第一道防线：关键词黑名单
    upper_sql = sql.upper()
    for keyword in DANGEROUS_KEYWORDS:
        # 用正则匹配完整单词，避免误伤（比如 INSERT 不应该匹配到 INSERTED）
        pattern = r"\b" + keyword + r"\b"
        if re.search(pattern, upper_sql):
            return False, f"安全拦截：检测到危险关键词 '{keyword}'，只允许 SELECT 查询"

    # 第二道防线：必须包含 SELECT
    if not upper_sql.strip().startswith("SELECT"):
        return False, "安全拦截：只允许以 SELECT 开头的查询语句"

     # 第三道防线：SQLite 语法校验
    try:
        from config import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute(f"EXPLAIN {sql}")
        conn.close()
    except sqlite3.Error as e:
        return False, f"SQL 语法错误：{str(e)}"

    return True, sql


def get_safe_sql(sql: str) -> str:
    """
    包装函数：校验通过返回原 SQL，失败抛出异常。
    用在主流程中，调用这个函数就可以安全执行。
    """
    ok, msg = validate(sql)
    if not ok:
        raise ValueError(f"SQL 安全检查未通过: {msg}")
    return msg