"""
main.py — 主入口
职责：串联全流程，提供命令行交互界面
"""
from database import init_db, execute_query
from sql_gen import generate_sql
from safety import get_safe_sql
from visualizer import generate_chart, open_chart


def main():
    """主函数：初始化 → 接收问题 → 生成SQL → 校验 → 执行 → 输出结果"""

    # 1. 初始化数据库
    init_db()

    print("=" * 50)
    print("  DataMind — 智能数据分析 Agent")
    print("  输入你的问题，Agent 自动生成 SQL 并查询")
    print("  输入 'exit' 或 'quit' 退出")
    print("=" * 50)
    print()

    # 2. 主循环
    while True:
        try:
            question = input("请输入你的问题：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not question:
            continue

        if question.lower() in ("exit", "quit"):
            print("再见！")
            break

        # 3. 生成 SQL
        print("正在分析你的问题...")
        sql = generate_sql(question)
        print(f"生成 SQL:\n{sql}\n")

        if sql == "无法理解":
            print("抱歉，我无法理解你的问题，请换一种问法。")
            print()
            continue

        # 4. 安全校验
        try:
            safe_sql = get_safe_sql(sql)
        except ValueError as e:
            print(f"安全拦截: {e}")
            print()
            continue

        # 5. 执行查询
        try:
            results = execute_query(safe_sql)
        except Exception as e:
            print(f"查询执行失败：{e}")
            print()
            continue

        # 6. 输出结果
        if not results:
            print("查询结果为空。")
        else:
            print(f"查询结果（共 {len(results)} 条）：")
            for i, row in enumerate(results, 1):
                print(f"  {i}. {row}")

            # 7. 生成可视化图表
            try:
                filepath = generate_chart(results, question)
                if filepath:
                    open_chart(filepath)
                    print(f"图表已生成：{filepath}")
            except Exception as e:
                print(f"图表生成失败：{e}")

        print()


if __name__ == "__main__":
    main()