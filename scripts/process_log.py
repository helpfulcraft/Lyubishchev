import re
import json
from collections import defaultdict
from datetime import datetime
import os
import csv

def time_str_to_minutes(time_str):
    """将'XhYm'格式的字符串转换为分钟。"""
    hours = 0
    minutes = 0
    if 'h' in time_str:
        parts = time_str.split('h')
        hours = int(parts[0])
        if parts[1] and 'm' in parts[1]:
            minutes = int(parts[1].replace('m', ''))
    elif 'm' in time_str:
        minutes = int(time_str.replace('m', ''))
    return hours * 60 + minutes

def minutes_to_time_str(minutes):
    """将分钟数转换为'Xh Ym'格式的字符串。"""
    if minutes == 0:
        return "0m"
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}m"

def parse_log_file(file_path):
    """解析日志文件，计算时间总和，并提取详细的任务条目和日期。"""
    # 结构：{ category: { item: { 'total_minutes': total_minutes, 'tasks': [{'name': task_name, 'time_str': time_str}] } } }
    item_details = defaultdict(lambda: defaultdict(lambda: {'total_minutes': 0, 'tasks': []}))
    
    # 默认使用当前日期，但会尝试从日志中解析
    log_date = datetime.now()
    date_pattern = re.compile(r'^\s*##\s*(\d{1,2})\.(\d{1,2})\s*$')
    
    current_category = None
    category_pattern = re.compile(r'^\s*-\s*([一二三四五六七八九十]+、[\u4e00-\u9fa5]+)\s*$')
    item_pattern = re.compile(r'^\s+-\s*([\u4e00-\u9fa5]+)\s*[\(（](.*)[\)）]\s*$')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line_content = line.strip()
            if not line_content:
                continue

            # 尝试匹配日期
            date_match = date_pattern.match(line_content)
            if date_match:
                try:
                    month = int(date_match.group(1))
                    day = int(date_match.group(2))
                    current_year = datetime.now().year
                    log_date = datetime(current_year, month, day)
                except ValueError:
                    # 如果日期格式错误，则忽略并使用默认的当天日期
                    pass
                continue # 处理完日期行后跳过
            
            category_match = category_pattern.match(line)
            if category_match:
                full_title = category_match.group(1)
                current_category = full_title.split('、')[1]
                continue

            item_match = item_pattern.match(line)
            if item_match and current_category:
                item_name = item_match.group(1)
                content = item_match.group(2).strip()
                
                # 更精细地解析任务和时间
                # 正则表达式找到所有 "任务名+时间" 的组合
                # 任务名可以包含空格，但不包含'（'和'）'
                # 时间是 hh mm 或者 mm 格式
                pattern = re.compile(r'([\s\S]+?)(?:\s|-)*?(\d+h\d*m?|\d+m)')
                matches = pattern.findall(content)

                tasks = []
                # 合并由+连接的同名任务
                for i, (name, time) in enumerate(matches):
                    task_name = name.strip()
                    if task_name == '+' and tasks:
                        # 如果任务名是"+"，则将时间添加到上一个任务
                        tasks[-1]['time_str'] += f"+{time}"
                    else:
                        tasks.append({'name': task_name, 'time_str': time})

                # 处理 `+` 连接的时间字符串, 例如 "1h+12m"
                processed_tasks = []
                for task in tasks:
                    # 将 '17m+28m' 这样的字符串中的时间相加
                    individual_times = re.findall(r'\d+h\d*m?|\d+m', task['time_str'])
                    total_minutes = sum(time_str_to_minutes(ts) for ts in individual_times)
                    
                    if total_minutes > 0:
                        processed_tasks.append({'name': task['name'], 'minutes': total_minutes})

                for p_task in processed_tasks:
                    item_details[current_category][item_name]['tasks'].append(p_task)
                    item_details[current_category][item_name]['total_minutes'] += p_task['minutes']

    # --- 计算总计和格式化输出 ---
    final_data = defaultdict(dict)
    daily_details_structured = defaultdict(lambda: defaultdict(list))
    grand_total_minutes = 0

    for category, items in item_details.items():
        category_total_minutes = 0
        for item, details in items.items():
            total_minutes = details['total_minutes']
            final_data[category][item] = minutes_to_time_str(total_minutes)
            
            # 创建结构化的任务详情
            for task in details['tasks']:
                daily_details_structured[category][item].append({
                    "task": task['name'],
                    "time": minutes_to_time_str(task['minutes'])
                })
            
            category_total_minutes += total_minutes
        
        final_data[category]["总计"] = minutes_to_time_str(category_total_minutes)
        grand_total_minutes += category_total_minutes
    
    # 准备最终的JSON输出结构
    output_json = {
        "report_date": log_date.strftime('%Y-%m-%d'),
        "daily_summary": dict(final_data),
        "daily_details": {cat: dict(items) for cat, items in daily_details_structured.items()},
        "总计": minutes_to_time_str(grand_total_minutes)
    }

    # 为了保持和data.json一样的格式，将总计移动到 "daily_summary" 内部
    output_json["daily_summary"]["总计"] = output_json.pop("总计")

    return output_json, log_date

def append_to_csv(summary_data, log_date):
    """
    将每日总结追加到CSV文件中。
    此函数现在是幂等的：如果当天的数据已存在，它会先删除旧数据，再写入新数据。
    """
    csv_file = 'data/historical_data.csv'
    date_str = log_date.strftime('%Y-%m-%d')
    file_exists = os.path.isfile(csv_file)

    rows_to_keep = []
    header = ['Date', 'Category', 'Item', 'Task', 'Task Duration (minutes)']

    if file_exists:
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                # 保留表头和不属于当天的数据
                header = next(reader)
                rows_to_keep = [row for row in reader if row and row[0] != date_str]
            except StopIteration:
                # 文件为空或只有表头
                pass

    # 准备当天的新数据
    new_rows = []
    for category, items in summary_data.get('daily_details', {}).items():
        for item, tasks in items.items():
            if not tasks:
                total_time_str = summary_data.get('daily_summary', {}).get(category, {}).get(item, '0m')
                total_minutes = time_str_to_minutes(total_time_str)
                new_rows.append([date_str, category, item, "N/A", total_minutes])
            else:
                for task in tasks:
                    minutes = time_str_to_minutes(task['time'])
                    new_rows.append([date_str, category, item, task['task'], minutes])

    # 将保留的旧数据和当天的新数据全部写回文件
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows_to_keep)
        writer.writerows(new_rows)

    print(f"数据已成功更新到 '{csv_file}'。")

def main():
    """主函数"""
    # 假设日志文件名为 log.md
    log_file = 'data/log.md' 
    output_file = 'data/summary.json'

    # 检查日志文件是否存在
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            pass
        print(f"开始处理 '{log_file}'...")
    except FileNotFoundError:
        print(f"错误：日志文件 '{log_file}' 不存在。")
        print("请创建一个 'log.md' 文件并填入您的时间记录。")
        # 创建一个带有提示内容的log.md文件
        sample_log_content = """
在此处粘贴您的时间记录，例如：

一、杂项
日常（琐事1h 20m）
工程（写代码3h 45m）

二、第二类
锻炼（跑步30m）
"""
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(sample_log_content)
        print(f"已为您创建一个示例 '{log_file}'。请填充内容后重新运行。")
        return

    # 解析日志并生成JSON
    summary_data, log_date = parse_log_file(log_file)
    
    # 将结果写入JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
    print(f"成功生成 '{output_file}'！")

    # 追加数据到CSV
    append_to_csv(summary_data, log_date)

if __name__ == "__main__":
    main() 