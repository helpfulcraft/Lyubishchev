# 柳比歇夫时间统计法实践工具

这是一个基于Python的个人时间使用情况分析和报告生成工具，旨在实践亚历山大·柳比歇夫的时间统计法。通过记录每日的活动日志，本工具可以自动化地生成包含多种可视化图表的日度或周期性报告，帮助用户深入理解自己的时间分配模式。

## ✨ 功能特性

- **日志解析**: 自动解析特定格式的文本日志，提取任务、项目和耗时。
- **每日报告**: 生成详细的每日时间分配报告。
- **周期性报告**: 支持按周、月或自定义时间段生成汇总报告。
- **丰富的数据可视化**:
    - **总览卡片**: 直观展示各主类的总耗时。
    - **饼图**: 展示各主类时间分配的百分比。
    - **堆叠柱状图**: 清晰展示各主类下，不同子项的时间构成。
    - **旭日图**: 交互式地探索从主类到具体任务的时间分配层次。
    - **历史趋势图**: 以折线图展示各项活动随时间的变化趋势。
    - **图表库**: 提供额外的图表来探索数据，包括：
        - **Treemap**: 从另一维度展示时间块的层次结构。
        - **Streamgraph (流图)**: 优雅地展示各项活动耗时随时间的流动变化。
        - **Small Multiples**: 将不同类别的时间趋势拆分为多个迷你图表，便于分别观察和对比。
- **明暗主题切换**: 报告页面支持一键切换浅色和深色主题。
- **跨平台GUI**: 提供一个简单的图形用户界面 (`run_app.py`) 来粘贴日志、生成和查看报告。

## 🛠️ 技术栈

- **后端**: Python 3
- **数据处理**: Pandas
- **HTML模板**: Jinja2
- **可视化库**: Apache ECharts
- **GUI**: Tkinter (Python内置)

## 🚀 如何使用

### 1. 环境准备

确保您的环境中已安装 Python 3 和 Pip。

### 2. 安装依赖

本项目依赖 `pandas` 和 `jinja2`。通过以下命令安装：

```bash
pip install pandas jinja2
```

### 3. 记录日志

在 `data/log.md` 文件中，按照以下格式记录您的每日时间日志。新的一天从 `## YYYY-MM-DD` 开始。

```markdown
## 2025-06-13

### 第一类
- 子项A: 1h 30m
  - 具体任务1
  - 具体任务2
- 子项B: 45m
  - 具体任务3

### 第二类
- 子项C: 2h
  - 具体任务4
```

### 4. 生成报告

有多种方式可以生成报告：

- **使用GUI (推荐)**:
  直接运行 `run_app.py`，这会打开一个图形界面。您可以将日志内容粘贴进去，然后点击按钮生成和查看报告。
  ```bash
  python scripts/run_app.py
  ```

- **通过命令行生成每日报告**:
  运行 `process_log.py` 来处理 `data/log.md` 中的最新一天日志，并生成 `data/summary.json`。
  ```bash
  python scripts/process_log.py
  ```
  然后运行 `build_report.py` 来根据 `summary.json` 生成HTML报告。
  ```bash
  python scripts/build_report.py
  ```

- **通过命令行生成周期性报告**:
  运行 `generate_periodic_report.py` 并指定周期。
  ```bash
  # 生成本周报告
  python scripts/generate_periodic_report.py --period week

  # 生成最近7天报告
  python scripts/generate_periodic_report.py --period last7days

  # 生成自定义时间段报告
  python scripts/generate_periodic_report.py --start 2025-06-01 --end 2025-06-15
  ```

所有生成的报告将保存在 `reports` 文件夹下。

## 📁 项目结构

```
.
├── .gitignore          # Git忽略文件配置
├── data/
│   ├── historical_data.csv # 所有活动的历史记录
│   ├── log.md            # 每日活动日志源文件
│   └── summary.json      # 单日日志处理后的摘要
├── reports/
│   └── ...               # 生成的HTML报告存放处
├── scripts/
│   ├── build_report.py   # 从summary.json生成每日报告
│   ├── generate_periodic_report.py # 生成周期性报告
│   ├── process_log.py    # 解析log.md并生成summary.json
│   └── run_app.py        # GUI应用程序入口
└── templates/
    └── new_report_template.html # 报告的HTML模板
```

## 📝 日志格式

程序依赖 `