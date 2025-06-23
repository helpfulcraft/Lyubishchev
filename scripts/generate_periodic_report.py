import pandas as pd
from jinja2 import Environment, FileSystemLoader
import datetime
import argparse
import os

# --- Predefined color list for categories ---
CATEGORY_COLORS = {
    '第一类': '#3498db',
    '第二类': '#2ecc71',
    '根源': '#9b59b6',
    '娱乐': '#f1c40f',
    '杂项': '#e74c3c',
    'default': '#7f8c8d'
}
COLOR_LIST = ['#5470C6', '#91CC75', '#FAC858', '#EE6666', '#73C0DE', '#3BA272', '#FC8452', '#9A60B4', '#EA7CCC']


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

def prepare_chart_and_pie_data(df):
    """从周期性DataFrame准备旭日图/卡片和饼图的数据。"""
    
    tasks_grouped = df.groupby(['Category', 'Item', 'Task'])['Task Duration (minutes)'].sum().reset_index()

    nested_data = {}
    for _, row in tasks_grouped.iterrows():
        cat, item, task, duration = row['Category'], row['Item'], row['Task'], row['Task Duration (minutes)']
        if cat not in nested_data:
            nested_data[cat] = {}
        if item not in nested_data[cat]:
            nested_data[cat][item] = {}
        nested_data[cat][item][task] = duration
    
    chart_data = []
    pie_data = []
    color_index = 0
    sorted_categories = sorted(nested_data.keys())

    for category in sorted_categories:
        items = nested_data[category]
        category_total_minutes = sum(sum(tasks.values()) for tasks in items.values())
        color = CATEGORY_COLORS.get(category, COLOR_LIST[color_index % len(COLOR_LIST)])
        color_index += 1

        children = []
        for item, tasks in items.items():
            item_minutes = sum(tasks.values())
            tasks_children = []
            for task, duration in tasks.items():
                tasks_children.append({
                    "name": task,
                    "value": duration,
                    "time_str": minutes_to_time_str(duration)
                })
            children.append({
                "name": item,
                "value": item_minutes,
                "value_str": minutes_to_time_str(item_minutes),
                "children": sorted(tasks_children, key=lambda x: x['value'], reverse=True)
            })
        
        chart_data.append({
            "name": category,
            "value": category_total_minutes,
            "value_str": minutes_to_time_str(category_total_minutes),
            "itemStyle": {"color": color},
            "children": sorted(children, key=lambda x: x['value'], reverse=True)
        })
        
        pie_data.append({
            "name": category,
            "value": category_total_minutes,
            "itemStyle": {"color": color}
        })
        
    return chart_data, pie_data

def prepare_stacked_bar_data(df):
    """为堆叠柱状图准备数据。"""
    y_axis_data = sorted(df['Category'].unique().tolist())
    legend_data = sorted(df['Item'].unique().tolist())
    
    series_data = []
    for subcategory in legend_data:
        series_item = {
            "name": subcategory,
            "type": 'bar',
            "stack": 'total',
            "emphasis": {"focus": "series"},
            "data": []
        }
        for category in y_axis_data:
            total_duration = df[(df['Category'] == category) & (df['Item'] == subcategory)]['Task Duration (minutes)'].sum()
            series_item['data'].append(int(total_duration))
        series_data.append(series_item)
        
    return {
        "yAxis": y_axis_data,
        "legend": legend_data,
        "series": series_data
    }


def main():
    """主函数：解析参数，处理数据，生成周期性报告。"""
    parser = argparse.ArgumentParser(description="生成周期性时间使用报告。")
    parser.add_argument('--period', type=str, choices=['week', 'month', 'last7days'],
                        help="预设的报告周期: 'week' (本周), 'month' (本月), 'last7days' (最近7天)。")
    parser.add_argument('--start', type=str, help="报告周期的开始日期 (YYYY-MM-DD)。")
    parser.add_argument('--end', type=str, help="报告周期的结束日期 (YYYY-MM-DD)。")
    parser.add_argument('--output', type=str, help="（可选）指定输出的HTML文件名。")
    args = parser.parse_args()

    today = datetime.date.today()
    start_date, end_date = None, None

    if args.start and args.end:
        try:
            start_date = datetime.datetime.strptime(args.start, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(args.end, '%Y-%m-%d').date()
        except ValueError:
            print("错误: --start 和 --end 日期格式必须为 YYYY-MM-DD。")
            return
    elif args.period:
        if args.period == 'last7days':
            start_date = today - datetime.timedelta(days=6)
            end_date = today
        elif args.period == 'week':
            start_date = today - datetime.timedelta(days=today.weekday())
            end_date = today
        elif args.period == 'month':
            start_date = today.replace(day=1)
            end_date = today
    
    if not start_date or not end_date:
        print("错误: 请提供一个有效的报告周期。")
        return
        
    csv_file = 'data/historical_data.csv'
    if not os.path.exists(csv_file):
        print(f"错误: 未找到历史数据文件 '{csv_file}'。")
        return
    
    try:
        df = pd.read_csv(csv_file)
        # 显式指定日期格式，以确保解析正确
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce').dt.date
    except Exception as e:
        print(f"读取或解析 '{csv_file}' 时出错: {e}")
        return

    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
    period_df = df.loc[mask]

    if period_df.empty:
        print("指定周期内没有找到任何数据。")
        return

    # --- 3. 准备所有图表和模板所需的数据 ---
    chart_data, pie_data = prepare_chart_and_pie_data(period_df)
    stacked_bar_data = prepare_stacked_bar_data(period_df)
    grand_total_minutes = period_df['Task Duration (minutes)'].sum()
    generation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    daily_summary_like = {}
    for cat_data in chart_data:
        daily_summary_like[cat_data['name']] = {"总计": cat_data['value_str']}
        for item_data in cat_data['children']:
            daily_summary_like[cat_data['name']][item_data['name']] = item_data['value_str']
    daily_summary_like["总计"] = minutes_to_time_str(grand_total_minutes)
    template_data_for_card = {"daily_summary": daily_summary_like}

    # --- 4. 渲染HTML模板 ---
    template_file = 'new_report_template.html'
    try:
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template(template_file)
    except Exception as e:
        print(f"错误: 找不到或无法加载模板文件 '{template_file}'。 {e}")
        return

    html_content = template.render(
        chart_data=chart_data,
        pie_data=pie_data,
        stacked_bar_data=stacked_bar_data,
        data=template_data_for_card,
        report_period=f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        historical_data=None,
        generation_time=generation_time
    )
    
    if args.output:
        # If an output path is specified, ensure it's in the reports directory
        if not args.output.startswith('reports/'):
             output_file = os.path.join('reports', os.path.basename(args.output))
        else:
            output_file = args.output
    else:
        period_str = args.period or 'custom'
        date_str = start_date.strftime("%Y%m%d")
        output_file = f"reports/report-periodic-{period_str}-{date_str}.html"

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        # Standardize the output for easy parsing by the GUI
        print(f"--> {output_file}")
    except Exception as e:
        print(f"错误: 无法写入报告文件 '{output_file}'。 {e}")

if __name__ == "__main__":
    main() 