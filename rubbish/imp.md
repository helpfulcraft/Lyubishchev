# IMP: 周期性时间报告系统实现方案

## 1. 总览 (Overview)

本文档基于 `rfc.md` 的需求，为周期性报告系统提供具体的实现步骤和技术选型。核心是创建一个 `generate_periodic_report.py` 脚本，并为其设计一个可交互的前端模板 `periodic_report_template.html`。

## 2. 后端实现 (`generate_periodic_report.py`)

### 2.1. 依赖库
-   `pandas`: 用于高效地读取、筛选和聚合 `historical_data.csv` 数据。
-   `jinja2`: 用于渲染HTML报告模板。
-   `argparse`: 用于从命令行解析用户输入的参数（如日期范围）。

### 2.2. 命令行参数解析
脚本需支持灵活的日期参数：
-   `--period <name>`: 支持预设值，如 `week`, `month`, `last7days`。
-   `--start <YYYY-MM-DD>` 和 `--end <YYYY-MM-DD>`: 支持自定义日期范围。
-   `--output <filename>`: (可选) 允许用户指定输出文件名。

### 2.3. 数据处理流程

**Step 1: 读取和筛选**
-   使用 `pandas` 读取 `historical_data.csv`。
-   将 'Date' 列转换为 `datetime` 对象，以便进行日期比较。
-   根据命令行传入的参数，计算出起始和结束日期。
-   使用日期范围筛选 DataFrame，得到周期内的所有数据记录。

**Step 2: 数据聚合与结构化**
这是最核心的步骤，需要为前端准备一个嵌套的、信息丰富的字典/JSON结构。
-   **顶层聚合 (for FR2)**:
    -   按 'Category' 分组，计算每个主类的总时长。
    -   按 'Category' 和 'Item' 分组，计算每个子项的总时长。
-   **钻取详情聚合 (for FR3)**:
    -   按 'Category', 'Item', 和 'Task' 三个层级分组，计算每个具体任务在周期内的总时长。
-   **数据结构设计**:
    最终传递给模板的数据结构，应该类似于：
    ```json
    {
      "report_period": "2025-06-10 to 2025-06-16",
      "total_duration_str": "70h 30m",
      "categories": [
        {
          "name": "娱乐",
          "total_duration": 1500, // minutes
          "total_duration_str": "25h",
          "items": [
            {
              "name": "游戏",
              "total_duration": 1080,
              "total_duration_str": "18h",
              "tasks": [
                { "name": "er", "duration_str": "10h" },
                { "name": "卢岛食堂", "duration_str": "8h" }
              ]
            },
            // ... more items
          ]
        },
        // ... more categories
      ]
      // ... 可能还有用于特定图表的数据
    }
    ```

### 2.4. 模板渲染
-   加载 `periodic_report_template.html` 模板。
-   使用 `jinja2` 将处理好的数据结构渲染进模板。
-   根据周期计算输出文件名（例如 `report-weekly-2025-W24.html`），并将渲染好的HTML内容写入文件。

## 3. 前端实现 (`periodic_report_template.html`)

### 3.1. 依赖库
-   `ECharts`: 用于数据可视化，生成图表。

### 3.2. 页面布局
-   页面主体将分为几个"卡片"区域：
    -   **总览卡片**: 显示周期、总时长等关键指标。
    -   **图表分析卡片**: 放置用于宏观分析的图表。
    -   **明细卡片**: 这是实现钻取功能的核心区域。

### 3.3. 交互式钻取 (Drill-Down) 实现
-   **HTML结构**:
    -   使用Jinja2循环渲染 `categories` 数据，生成聚合视图。
    -   每个分类的详情部分（`items` 和 `tasks`）默认包裹在一个 `div` 中，并设置 `display: none;`。
    -   为每个分类标题添加一个可点击的 `[+]` 按钮，并附加 `data-target` 属性指向其对应的详情 `div`。
-   **JavaScript逻辑**:
    -   编写一个 `click` 事件监听器，绑定到所有展开/折叠按钮上。
    -   当按钮被点击时，获取其 `data-target` 值，找到对应的详情 `div`。
    -   切换该 `div` 的显示状态（`display: none;` <=> `display: block;` 或使用更平滑的动画效果）。
    -   同时切换按钮的文本内容，从 `[+]` 变为 `[-]`，反之亦然。

### 3.4. 图表实现
-   **周期趋势图**: 创建一个柱状图，X轴为周期内的每一天，Y轴为当天的总耗时。如果周期太长（如月报），则X轴可以变为每周。
-   **分类总览图**: 创建一个饼图或条形图，展示周期内各大分类的总时间占比。
-   所有图表数据均从Jinja2渲染的JSON数据中获取。 