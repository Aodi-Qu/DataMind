"""
visualizer.py — 数据可视化模块
职责：将查询结果生成 HTML 图表，并自动打开浏览器
"""
import webbrowser
import os
import json


def _guess_chart_type(results: list[dict]) -> str:
    """
    根据查询结果的列名和数据，猜测最适合的图表类型。

    规则：
    - 如果有日期列 → 折线图（看趋势）
    - 如果只有 1 个数值列 + 1 个分类列 → 柱状图
    - 如果数值列有占比含义（比如 COUNT, 占比小）→ 饼图
    - 默认 → 柱状图
    """
    if not results:
        return "bar"

    columns = list(results[0].keys())

    # 有日期列 → 折线图
    date_keywords = ["date", "日期", "时间", "month", "year", "sale_date"]
    for col in columns:
        if any(kw in col.lower() for kw in date_keywords):
            return "line"

    # 只有两列：一列文本 + 一列数字 → 默认柱状图
    # 如果数字列名包含"占比""比例""百分比"→ 饼图
    if len(columns) == 2:
        # 判断哪一列是数字
        for row in results:
            for col in columns:
                if isinstance(row[col], (int, float)):
                    if any(kw in col.lower() for kw in ["占比", "比例", "百分比", "percent"]):
                        return "pie"
            break
        return "bar"

    return "bar"


def generate_chart(results: list[dict], question: str = "") -> str:
    """
    生成 HTML 图表文件，返回文件路径。

    参数:
        results: 查询结果列表，每行是一个字典
        question: 用户的问题，用作标题

    返回:
        HTML 文件的路径
    """
    if not results:
        return ""

    chart_type = _guess_chart_type(results)
    columns = list(results[0].keys())

    # 假设第一列是标签（x 轴 / 图例），第二列是数值
    # 如果超过两列，选前两列
        # 智能选择标签列和数值列
    # 标签列：选第一个文本类型的列（通常是 name 或 category）
    # 数值列：选第一个数字类型的列（通常是 price、total 等）
    label_col = columns[0]
    value_col = columns[0]
    
    # 先找数值列
    for col in columns:
        sample = results[0][col]
        if isinstance(sample, (int, float)):
            value_col = col
            break
    
    # 再找非数值列作为标签
    for col in columns:
        sample = results[0][col]
        if not isinstance(sample, (int, float)):
            label_col = col
            break
    # 提取标签和数值
    labels = [row[label_col] for row in results]
    values = [row[value_col] if isinstance(row[value_col], (int, float)) else 0 for row in results]

    # ECharts 配置
    chart_config = {
        "title": question or "查询结果",
        "type": chart_type,
        "labels": labels,
        "values": values,
    }

    # 根据图表类型生成不同的 ECharts 配置
    if chart_type == "pie":
        option = _build_pie_option(chart_config)
    elif chart_type == "line":
        option = _build_line_option(chart_config)
    else:
        option = _build_bar_option(chart_config)

    # 生成 HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{chart_config['title']}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
</head>
<body>
    <h2>{chart_config['title']}</h2>
    <div id="chart" style="width: 800px; height: 500px;"></div>
    <script>
        var myChart = echarts.init(document.getElementById('chart'));
        var option = {json.dumps(option, ensure_ascii=False)};
        myChart.setOption(option);
    </script>
</body>
</html>"""

    # 保存文件
    filepath = os.path.abspath("chart.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath


def _build_bar_option(config: dict) -> dict:
    """生成柱状图的 ECharts 配置"""
    return {
        "xAxis": {
            "type": "category",
            "data": config["labels"],
            "axisLabel": {"rotate": 30}
        },
        "yAxis": {"type": "value"},
        "series": [{
            "type": "bar",
            "data": config["values"],
            "itemStyle": {"color": "#5470c6"}
        }],
        "title": {"text": config["title"], "left": "center"},
        "tooltip": {"trigger": "axis"}
    }


def _build_line_option(config: dict) -> dict:
    """生成折线图的 ECharts 配置"""
    return {
        "xAxis": {
            "type": "category",
            "data": config["labels"],
            "axisLabel": {"rotate": 30}
        },
        "yAxis": {"type": "value"},
        "series": [{
            "type": "line",
            "data": config["values"],
            "smooth": True,
            "itemStyle": {"color": "#91cc75"}
        }],
        "title": {"text": config["title"], "left": "center"},
        "tooltip": {"trigger": "axis"}
    }


def _build_pie_option(config: dict) -> dict:
    """生成饼图的 ECharts 配置"""
    data = []
    for label, value in zip(config["labels"], config["values"]):
        data.append({"name": str(label), "value": value})

    return {
        "series": [{
            "type": "pie",
            "data": data,
            "radius": "60%",
            "label": {"show": True, "formatter": "{b}: {c}"}
        }],
        "title": {"text": config["title"], "left": "center"},
        "tooltip": {"trigger": "item"}
    }


def open_chart(filepath: str):
    """在浏览器中打开图表"""
    if filepath and os.path.exists(filepath):
        webbrowser.open("file://" + filepath)