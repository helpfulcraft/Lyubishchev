import json
from jinja2 import Environment, FileSystemLoader
import datetime
import pandas as pd
import os

def time_str_to_minutes(time_str):
    """将'Xh Ym'或'Xh'或'Ym'格式的字符串转换为分钟。"""
    hours = 0
    minutes = 0
    if not isinstance(time_str, str):
        return 0
    time_str = time_str.strip()
    
    if 'h' in time_str:
        parts = time_str.split('h')
        try:
            hours = int(parts[0])
        except ValueError:
            hours = 0
        if parts[1] and 'm' in parts[1]:
            try:
                minutes = int(parts[1].replace('m', ''))
            except (ValueError, IndexError):
                minutes = 0
    elif 'm' in time_str:
        try:
            minutes = int(time_str.replace('m', ''))
        except ValueError:
            minutes = 0
            
    return hours * 60 + minutes

def minutes_to_time_str(minutes):
    """将分钟数转换为'Xh Ym'格式的字符串。"""
    if minutes is None or minutes < 0:
        return "0m"
    if minutes == 0:
        return "0m"
    hours = minutes // 60
    mins = minutes % 60
    result = ''
    if hours > 0:
        result += f"{hours}h"
    if mins > 0:
        result += ('' if result == '' else ' ') + f"{mins}m"
    return result

def prepare_data_for_template(data):
    """将摘要数据转换为新模板所需的丰富格式。"""
    
    # 为类别定义颜色
    colors = {
        '第一类': '#3498db',  # 蓝色
        '第二类': '#2ecc71',  # 绿色
        '根源': '#9b59b6',   # 紫色
        '娱乐': '#f1c40f',   # 黄色
        '杂项': '#e74c3c',    # 红色
        'default': '#7f8c8d'  # 灰色
    }

    chart_data = []
    pie_data = []
    summary = data.get("daily_summary", {})
    details = data.get("daily_details", {})
    
    # 按照在颜色字典中定义的顺序排序，以确保颜色稳定
    sorted_categories = sorted(summary.keys(), key=lambda x: list(colors.keys()).index(x) if x in colors else 99)

    for category in sorted_categories:
        items = summary[category]
        if category == "总计":
            continue
            
        category_total_minutes = time_str_to_minutes(items.get("总计", "0m"))
        color = colors.get(category, colors['default'])

        # 准备子类别数据 (旭日图的第二层)
        children = []
        category_details = details.get(category, {})
        for item, time_str in items.items():
            if item != "总计":
                item_minutes = time_str_to_minutes(time_str)
                
                # 准备任务数据 (旭日图的第三层)
                tasks_children = []
                if item in category_details:
                    for task in category_details[item]:
                        task_minutes = time_str_to_minutes(task['time'])
                        tasks_children.append({
                            "name": task['task'],
                            "value": task_minutes,
                            "time_str": minutes_to_time_str(task_minutes)
                        })

                children.append({
                    "name": item,
                    "value": item_minutes,
                    "value_str": minutes_to_time_str(item_minutes),
                    "children": tasks_children
                })
        
        # 准备旭日图和卡片的数据
        chart_data.append({
            "name": category,
            "value": category_total_minutes,
            "value_str": minutes_to_time_str(category_total_minutes),
            "itemStyle": {"color": color},
            "children": children
        })
        
        # 准备饼图数据
        pie_data.append({
            "name": category,
            "value": category_total_minutes,
            "itemStyle": {"color": color}
        })
        
    return chart_data, pie_data

def prepare_stacked_bar_data(data):
    """为堆叠柱状图准备数据。"""
    summary = data.get("daily_summary", {})
    
    # 获取所有主类别作为Y轴
    y_axis_data = [cat for cat in summary if cat != "总计"]
    
    # 获取所有子类别，并创建图例
    all_subcategories = set()
    for category, items in summary.items():
        if category == "总计":
            continue
        for item in items:
            if item != "总计":
                all_subcategories.add(item)
    
    legend_data = sorted(list(all_subcategories))
    
    series_data = []
    for subcategory in legend_data:
        series_item = {
            "name": subcategory,
            "type": 'bar',
            "stack": 'total', # 所有系列都在同一个堆叠'total'中
            "emphasis": {"focus": "series"},
            "data": []
        }
        for category in y_axis_data:
            time_str = summary.get(category, {}).get(subcategory, "0m")
            minutes = time_str_to_minutes(time_str)
            series_item['data'].append(minutes)
        series_data.append(series_item)
        
    return {
        "yAxis": y_axis_data,
        "legend": legend_data,
        "series": series_data
    }

def prepare_historical_data(csv_file):
    """读取并处理历史数据CSV，为折线图准备数据。"""
    if not os.path.exists(csv_file):
        return None

    try:
        # 指定列名，以防旧文件格式不一致
        col_names = ['Date', 'Category', 'Item', 'Task', 'Task Duration (minutes)']
        df = pd.read_csv(csv_file)
        df.columns = col_names[:len(df.columns)]


        # 将日期字符串转换为datetime对象，并按日期排序
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')

        # 按日期和类别对时长进行分组求和
        # 我们只关心Category的总和，所以Item和Task级别的数据直接聚合掉
        pivot_df = df.pivot_table(index='Date', columns='Category', values='Task Duration (minutes)', aggfunc='sum').fillna(0)
        
        # 准备ECharts需要的数据格式
        dates = pivot_df.index.strftime('%Y-%m-%d').tolist()
        categories = pivot_df.columns.tolist()
        
        series = []
        for category in categories:
            series.append({
                "name": category,
                "type": 'line',
                "data": pivot_df[category].tolist()
            })
            
        return {"dates": dates, "categories": categories, "series": series}
    except Exception as e:
        print(f"处理历史数据时出错: {e}")
        return None

def main():
    """主函数：读取JSON，渲染并保存HTML报告。"""
    json_file = 'data/summary.json'
    template_file = 'new_report_template.html'
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 未找到 '{json_file}'。请先运行 'process_log.py'。")
        return
    except json.JSONDecodeError:
        print(f"错误: '{json_file}' 文件格式不正确。")
        return

    # 统一并动态生成输出文件名
    report_date = summary_data.get("report_date")
    date_str = report_date or datetime.datetime.now().strftime("%Y-%m-%d")
    output_file = f'reports/report-daily-{date_str}.html'

    chart_data, pie_data = prepare_data_for_template(summary_data)
    stacked_bar_data = prepare_stacked_bar_data(summary_data)
    historical_data = prepare_historical_data('data/historical_data.csv')
    generation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 为新图表准备数据
    # Treemap 数据可以复用旭日图的数据结构
    treemap_data = chart_data
    # Streamgraph 和 Small Multiples 可以复用历史数据
    streamgraph_data = historical_data
    small_multiples_data = historical_data

    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(template_file)
    
    html_content = template.render(
        report_date=report_date,
        data=summary_data,
        chart_data=chart_data,
        pie_data=pie_data,
        stacked_bar_data=stacked_bar_data,
        historical_data=historical_data,
        generation_time=generation_time,
        # 新增图表数据
        treemap_data=treemap_data,
        streamgraph_data=streamgraph_data,
        small_multiples_data=small_multiples_data
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    # Standardize the output for easy parsing by the GUI
    print(f"--> {output_file}")

if __name__ == "__main__":
    main() 