import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import webbrowser
import os
import sys
import re
import locale
from tkcalendar import DateEntry
from datetime import date, datetime

def get_script_path():
    """获取脚本所在目录的绝对路径"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.realpath(sys.argv[0]))

def open_file_in_browser(file_path):
    """在浏览器中打开指定的文件"""
    if file_path and os.path.exists(file_path):
        webbrowser.open(f"file://{os.path.abspath(file_path)}")
        return True
    return False

def run_script(command, status_label):
    """通用函数，用于运行脚本并捕获输出。"""
    scripts_path = get_script_path()
    project_root = os.path.abspath(os.path.join(scripts_path, os.pardir))
    python_executable = sys.executable
    
    command = [python_executable] + command
    
    try:
        status_label.config(text="处理中，请稍候...", fg="blue")
        window.update_idletasks()

        result = subprocess.run(
            command, capture_output=True, text=True, encoding=locale.getpreferredencoding(False), check=False, cwd=project_root
        )
        
        if result.returncode != 0:
            error_message = f"脚本执行失败: {' '.join(command)}\n\n错误信息:\n{result.stderr or result.stdout}"
            raise subprocess.CalledProcessError(result.returncode, command, stderr=error_message)
            
        return result.stdout

    except subprocess.CalledProcessError as e:
        messagebox.showerror("执行错误", e.stderr)
        status_label.config(text="脚本执行失败，请查看错误弹窗。", fg="red")
        return None
    except Exception as e:
        messagebox.showerror("未知错误", f"发生未知错误: {e}")
        status_label.config(text="发生未知错误，请查看错误弹窗。", fg="red")
        return None

def generate_daily_report():
    """处理并生成每日报告，支持一次性处理多个日期。"""
    log_content = text_area.get("1.0", tk.END)
    if not log_content.strip():
        messagebox.showerror("错误", "日志内容不能为空！")
        status_label.config(text="请输入日志内容。", fg="red")
        return

    scripts_path = get_script_path()
    project_root = os.path.abspath(os.path.join(scripts_path, os.pardir))
    log_file_path = os.path.join(project_root, 'data', 'log.md')

    # 使用正则表达式按日期分割日志内容
    # (^\s*##\s*\d{1,2}\.\d{1,2}\s*$)
    # - ^: 匹配行首
    # - \s*: 零或多个空白字符
    # - ##: 字面量 "##"
    # - \s*: 零或多个空白字符
    # - \d{1,2}\.\d{1,2}: 月和日
    # - \s*: 零或多个空白字符
    # - $: 匹配行尾
    # 括号将分隔符本身也包含在结果中
    log_chunks_raw = re.split(r'(^\s*##\s*\d{1,2}\.\d{1,2}\s*$)', log_content, flags=re.MULTILINE)
    
    log_chunks = []
    # 从1开始循环，因为第一个元素通常是空的（如果文本以日期开头）
    for i in range(1, len(log_chunks_raw), 2):
        # 将日期和其后的内容合并成一个块
        date_header = log_chunks_raw[i]
        content = log_chunks_raw[i+1] if (i+1) < len(log_chunks_raw) else ""
        if date_header.strip() and content.strip():
            log_chunks.append(date_header + content)

    if not log_chunks:
        # 如果没有找到任何日期标记，则将整个内容视为一个单独的报告
        if log_content.strip():
            log_chunks.append(log_content)
        else:
            messagebox.showerror("错误", "未找到有效的日志内容或日期标记 (## 月.日)。")
            return

    generated_reports = []
    total_chunks = len(log_chunks)

    for i, chunk in enumerate(log_chunks):
        status_label.config(text=f"正在处理第 {i+1}/{total_chunks} 份报告...", fg="blue")
        window.update_idletasks() # 强制更新UI

        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(chunk)

        # Step 1: Process log file
        process_output = run_script([os.path.join(scripts_path, 'process_log.py')], status_label)
        if process_output is None:
            messagebox.showerror("处理失败", f"处理第 {i+1} 份报告时失败（process_log.py）。\n请检查控制台输出。")
            continue

        # Step 2: Build report
        build_output = run_script([os.path.join(scripts_path, 'build_report.py')], status_label)
        if build_output is None:
            messagebox.showerror("生成失败", f"生成第 {i+1} 份报告时失败（build_report.py）。\n请检查控制台输出。")
            continue

        match = re.search(r"-->\s*(.*\.html)", build_output)
        if match:
            report_path = match.group(1).strip()
            generated_reports.append(os.path.basename(report_path))
        else:
            messagebox.showwarning("警告", f"第 {i+1} 份报告已处理，但无法确定报告文件名。")
            
    if not generated_reports:
        messagebox.showerror("完成", "处理完成，但没有生成任何报告。")
        status_label.config(text="处理完成，但未生成报告。", fg="orange")
        return

    # --- 最终结果反馈 ---
    final_message = f"成功生成 {len(generated_reports)} 份报告:\n\n" + "\n".join(generated_reports)
    
    if len(generated_reports) == 1:
        # 如果只有一份报告，直接尝试打开它
        full_report_path = os.path.join(project_root, 'reports', generated_reports[0])
        if open_file_in_browser(full_report_path):
            status_label.config(text=f"报告 '{generated_reports[0]}' 已生成并打开！", fg="green")
            messagebox.showinfo("成功", f"报告 '{generated_reports[0]}' 已生成并成功在浏览器中打开！")
        else:
            messagebox.showerror("错误", f"已生成报告，但无法在浏览器中打开: {full_report_path}")
            status_label.config(text="错误：找不到报告文件。", fg="red")
    else:
        # 如果有多份报告，提示用户并询问是否打开文件夹
        status_label.config(text=f"成功生成 {len(generated_reports)} 份报告！", fg="green")
        if messagebox.askyesno("全部完成", final_message + "\n\n是否打开报告所在的文件夹？"):
            reports_dir = os.path.join(project_root, 'reports')
            try:
                os.startfile(reports_dir)
            except AttributeError: # For non-windows OS
                webbrowser.open(f"file:///{reports_dir}")

def generate_periodic_report():
    """生成周期报告"""
    period = period_var.get()
    
    if not period:
        messagebox.showerror("错误", "请选择一个报告周期！")
        return

    command_args = ['generate_periodic_report.py']
    
    if period == 'custom':
        start_date = start_date_entry.get_date()
        end_date = end_date_entry.get_date()
        if start_date > end_date:
            messagebox.showerror("错误", "开始日期不能晚于结束日期。")
            return
        command_args.extend(['--start', start_date.strftime('%Y-%m-%d'), '--end', end_date.strftime('%Y-%m-%d')])
    else:
        command_args.extend(['--period', period])

    scripts_path = get_script_path()
    project_root = os.path.abspath(os.path.join(scripts_path, os.pardir))

    # 构建完整的脚本路径
    command_with_full_path = [os.path.join(scripts_path, command_args[0])] + command_args[1:]

    # Run generation script
    output = run_script(command_with_full_path, status_label)

    if output:
        match = re.search(r"-->\s*(.*\.html)", output)
        if match:
            report_path = match.group(1).strip()
            full_report_path = os.path.join(project_root, report_path)
            if open_file_in_browser(full_report_path):
                status_label.config(text=f"报告 '{os.path.basename(report_path)}' 已生成并打开！", fg="green")
                messagebox.showinfo("成功", f"报告 '{os.path.basename(report_path)}' 已生成并成功在浏览器中打开！")
            else:
                messagebox.showerror("错误", f"找不到生成的报告文件: {full_report_path}")
                status_label.config(text="错误：找不到报告文件。", fg="red")
        else:
            messagebox.showerror("错误", "无法从脚本输出中找到报告文件名。")
            status_label.config(text="错误：无法确定报告文件名。", fg="red")

# --- GUI 界面设置 ---
window = tk.Tk()
window.title("柳比歇夫时间统计报告生成器 v2.0")
window.geometry("700x550")

# --- Main Tab Control ---
tab_control = ttk.Notebook(window)
tab_control.pack(expand=1, fill="both", padx=10, pady=10)

# --- Daily Report Tab ---
daily_tab = ttk.Frame(tab_control, padding=10)
tab_control.add(daily_tab, text='每日报告')

instruction_label = tk.Label(daily_tab, text="请在下方文本框中粘贴您的每日日志内容：", justify=tk.LEFT)
instruction_label.pack(side=tk.TOP, anchor="w", pady=(0, 5))

daily_button_frame = tk.Frame(daily_tab)
daily_button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
generate_daily_button = tk.Button(daily_button_frame, text="一键生成每日报告", command=generate_daily_report, font=("Microsoft YaHei", 12, "bold"))
generate_daily_button.pack(fill=tk.X)

text_area = scrolledtext.ScrolledText(daily_tab, wrap=tk.WORD, font=("Microsoft YaHei", 10))
text_area.pack(fill=tk.BOTH, expand=True)

# --- Periodic Report Tab ---
periodic_tab = ttk.Frame(tab_control, padding=10)
tab_control.add(periodic_tab, text='周期报告')

periodic_main_frame = tk.Frame(periodic_tab)
periodic_main_frame.pack(expand=True)

periodic_label = tk.Label(periodic_main_frame, text="请选择要生成的报告周期：", font=("Microsoft YaHei", 11))
periodic_label.pack(pady=10)

period_var = tk.StringVar(value="week")

def toggle_date_entries():
    """根据单选按钮的选择启用或禁用日期输入。"""
    if period_var.get() == 'custom':
        start_date_entry.config(state='normal')
        end_date_entry.config(state='normal')
    else:
        start_date_entry.config(state='disabled')
        end_date_entry.config(state='disabled')

periods = [("本周 (Week)", "week"), ("本月 (Month)", "month"), ("最近7天 (Last 7 Days)", "last7days")]
for text, mode in periods:
    rb = ttk.Radiobutton(periodic_main_frame, text=text, variable=period_var, value=mode, command=toggle_date_entries)
    rb.pack(anchor="w", padx=100, pady=5)

# --- Custom Date Frame ---
custom_date_frame = tk.Frame(periodic_main_frame)
custom_rb = ttk.Radiobutton(custom_date_frame, text="自定义范围 (Custom Range)", variable=period_var, value="custom", command=toggle_date_entries)
custom_rb.pack(side=tk.LEFT, anchor="w")
custom_date_frame.pack(anchor="w", padx=100, pady=(10, 5))

date_picker_frame = tk.Frame(periodic_main_frame)
date_picker_frame.pack(anchor="w", padx=110, pady=5)

tk.Label(date_picker_frame, text="从:").pack(side=tk.LEFT, padx=(5,2))
start_date_entry = DateEntry(date_picker_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-dd', max_date=date.today())
start_date_entry.pack(side=tk.LEFT)

tk.Label(date_picker_frame, text="到:").pack(side=tk.LEFT, padx=(10,2))
end_date_entry = DateEntry(date_picker_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-dd', max_date=date.today())
end_date_entry.pack(side=tk.LEFT)

generate_periodic_button = tk.Button(periodic_main_frame, text="生成周期报告", command=generate_periodic_report, font=("Microsoft YaHei", 12, "bold"))
generate_periodic_button.pack(pady=25, ipadx=20, ipady=5)

# --- Status Bar ---
status_label = tk.Label(window, text="欢迎使用！请选择报告类型并开始。", bd=1, relief=tk.SUNKEN, anchor=tk.W, padx=5)
status_label.pack(side=tk.BOTTOM, fill=tk.X)

# --- Initial Load of log.md ---
try:
    project_root_for_load = os.path.abspath(os.path.join(get_script_path(), os.pardir))
    log_file_path_for_load = os.path.join(project_root_for_load, 'data', 'log.md')
    if os.path.exists(log_file_path_for_load):
        with open(log_file_path_for_load, 'r', encoding='utf-8') as f:
            text_area.insert(tk.END, f.read())
except Exception as e:
    status_label.config(text=f"加载 log.md 失败: {e}", fg="orange")

# Initial state for date entries
toggle_date_entries()

window.mainloop() 