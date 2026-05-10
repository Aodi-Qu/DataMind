"""
web_app.py — Web 界面后端
职责：启动 Flask 服务，接收前端请求，返回查询结果
"""
from flask import Flask, request, jsonify, render_template_string
from database import init_db, execute_query
from sql_gen import generate_sql
from safety import get_safe_sql

app = Flask(__name__)

# HTML 模板（内嵌，不需要额外文件）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DataMind - 智能数据分析</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f6fa; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { text-align: center; color: #2d3436; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #636e72; margin-bottom: 20px; font-size: 14px; }
        .query-box { display: flex; gap: 10px; margin-bottom: 20px; }
        .query-box input { flex: 1; padding: 12px; border: 2px solid #dfe6e9; border-radius: 8px; font-size: 16px; }
        .query-box button { padding: 12px 30px; background: #0984e3; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }
        .query-box button:hover { background: #0767b3; }
        .query-box button:disabled { background: #b2bec3; cursor: not-allowed; }
        .loading { text-align: center; color: #636e72; margin: 10px 0; display: none; }
        .error { background: #ffeaa7; padding: 12px; border-radius: 8px; margin: 10px 0; display: none; }
        .result-area { display: none; }
        .sql-box { background: #2d3436; color: #dfe6e9; padding: 12px; border-radius: 8px; margin: 10px 0; font-family: monospace; font-size: 14px; }
        table { width: 100%%; border-collapse: collapse; margin: 10px 0; background: white; border-radius: 8px; overflow: hidden; }
        th { background: #0984e3; color: white; padding: 10px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #dfe6e9; }
        tr:hover { background: #f5f6fa; }
        .chart-container { width: 100%%; height: 400px; margin: 20px 0; background: white; border-radius: 8px; padding: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 DataMind</h1>
        <p class="subtitle">智能数据分析 Agent — 用大白话提问，自动生成 SQL 并可视化</p>
        
        <div class="query-box">
            <input id="question" type="text" placeholder="例如：上个月销售额最高的商品是什么？" />
            <button id="askBtn" onclick="ask()">查询</button>
        </div>
        
        <div id="loading" class="loading">🤔 正在分析你的问题...</div>
        <div id="error" class="error"></div>
        
        <div id="resultArea" class="result-area">
            <div id="sqlBox" class="sql-box"></div>
            <div id="tableBox"></div>
            <div id="chartBox" class="chart-container"></div>
        </div>
    </div>

    <script>
        let myChart = null;

        function ask() {
            const question = document.getElementById('question').value.trim();
            if (!question) return;

            // 显示加载状态
            document.getElementById('loading').style.display = 'block';
            document.getElementById('error').style.display = 'none';
            document.getElementById('resultArea').style.display = 'none';
            document.getElementById('askBtn').disabled = true;

            fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('askBtn').disabled = false;

                if (data.error) {
                    document.getElementById('error').textContent = '❌ ' + data.error;
                    document.getElementById('error').style.display = 'block';
                    return;
                }

                // 显示 SQL
                document.getElementById('sqlBox').textContent = '📝 ' + data.sql;

                // 显示表格
                let tableHtml = '<table><tr>';
                for (let col of data.columns) {
                    tableHtml += '<th>' + col + '</th>';
                }
                tableHtml += '</tr>';
                for (let row of data.rows) {
                    tableHtml += '<tr>';
                    for (let col of data.columns) {
                        tableHtml += '<td>' + (row[col] !== null ? row[col] : '') + '</td>';
                    }
                    tableHtml += '</tr>';
                }
                tableHtml += '</table>';
                document.getElementById('tableBox').innerHTML = tableHtml;

                // 显示图表
                setTimeout(() => {
                    if (myChart) myChart.dispose();
                    myChart = echarts.init(document.getElementById('chartBox'));
                    myChart.setOption(data.chart_option);
                }, 100);

                document.getElementById('resultArea').style.display = 'block';
            })
            .catch(err => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').textContent = '❌ 网络错误：' + err.message;
                document.getElementById('error').style.display = 'block';
                document.getElementById('askBtn').disabled = false;
            });
        }

        // 回车键触发查询
        document.getElementById('question').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') ask();
        });
    </script>
</body>
</html>
"""


def _build_chart_option(results, question):
    """根据查询结果构建 ECharts 配置"""
    if not results or len(results) == 0:
        return {}

    columns = list(results[0].keys())

    # 找标签列和数值列
    label_col = columns[0]
    value_col = columns[0]
    for col in columns:
        sample = results[0][col]
        if isinstance(sample, (int, float)):
            value_col = col
            break
    for col in columns:
        sample = results[0][col]
        if not isinstance(sample, (int, float)):
            label_col = col
            break

    labels = [str(row[label_col]) for row in results]
    values = [row[value_col] if isinstance(row[value_col], (int, float)) else 0 for row in results]

    return {
        "title": {"text": question or "查询结果", "left": "center"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"rotate": 30}
        },
        "yAxis": {"type": "value"},
        "series": [{
            "type": "bar",
            "data": values,
            "itemStyle": {"color": "#0984e3"}
        }]
    }


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/query", methods=["POST"])
def query():
    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "请输入问题"})

    # 生成 SQL
    sql = generate_sql(question)

    if sql == "无法理解":
        return jsonify({"error": "无法理解你的问题，请换一种问法"})

    # 安全校验
    try:
        safe_sql = get_safe_sql(sql)
    except ValueError as e:
        return jsonify({"error": f"SQL 安全检查未通过: {str(e)}"})

    # 执行查询
    try:
        results = execute_query(safe_sql)
    except Exception as e:
        return jsonify({"error": f"查询执行失败: {str(e)}"})

    # 构建返回数据
    columns = list(results[0].keys()) if results else []
    chart_option = _build_chart_option(results, question)

    return jsonify({
        "sql": sql,
        "columns": columns,
        "rows": results,
        "chart_option": chart_option,
    })


if __name__ == "__main__":
    init_db()
    print("=" * 50)
    print("  DataMind Web 服务已启动")
    print("  在浏览器打开: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host="127.0.0.1", port=5000)