# TOOLS.md - LLM-Tools 工具系统说明

> 最后更新: 2026-05-13 14:25 (Asia/Shanghai)

## 一、工具分类

### 【文件操作工具】
```
read_file(path: string) - 读取文件内容
  Example: {"tool": "read_file", "args": {"path": "E:/file.py"}}
  用途: 查看配置文件、日志文件、文本文件

write_file(path: string, content: string) - 写入文件
  Example: {"tool": "write_file", "args": {"path": "E:/file.py", "content": "data"}}
  用途: 创建新文件、保存数据、生成报告
  ⚠️ 需要用户确认

list_files(dir: string, ext: string optional) - 列出目录文件
  Example: {"tool": "list_files", "args": {"dir": "E:/project", "ext": ".py"}}
  用途: 查看目录结构、查找特定类型文件

code_read(path: string) - 读取代码文件（带行号）
  Example: {"tool": "code_read", "args": {"path": "E:/csi10/*.py"}}
  用途: 查看代码、分析代码结构、定位问题代码
  特点: 支持glob通配符、行号显示、编码自动检测

code_edit(path: string, edits: array) - 编辑代码
  Example: {"tool": "code_edit", "args": {"path": "E:/file.py", "edits": [...]}}
  用途: 修改代码、替换文本

file_patch(path: string, patches: array) - 按行号修改文件
  Example: {"tool": "file_patch", "args": {"path": "E:/file.py", "patches": [{"start_line": 1, "end_line": 3, "new_content": "..."}]}}
  用途: 精准修改、自动备份、预览模式
  特点: 不依赖上下文匹配，更可靠
```

### 【代码执行工具】
```
run_command(cmd: string) - 执行系统命令
  Example: {"tool": "run_command", "args": {"cmd": "dir E:/"}}
  用途: 执行系统命令、批处理操作

run_python(code: string) - 执行Python代码文件
  Example: {"tool": "run_python", "args": {"code": "script.py"}}
  用途: 运行Python脚本

exec_python(code: string) - 执行Python代码字符串
  Example: {"tool": "exec_python", "args": {"code": "import os; print(os.listdir())"}}
  用途: 快速计算、数据处理、自动化任务
  特点: 直接执行代码字符串，立即返回结果
```

### 【网络工具】
```
web_search(query: string) - 网络搜索
  Example: {"tool": "web_search", "args": {"query": "福州天气"}}
  用途: 查询天气、新闻、实时信息
  特点: 使用wttr.in API查询天气，支持中文

web_fetch(url: string) - 获取网页内容
  Example: {"tool": "web_fetch", "args": {"url": "https://weather.com"}}
  用途: 访问特定网址、获取网页数据
  特点: 使用BeautifulSoup提取文本，自动清理HTML
```

### 【其他工具】
```
get_time() - 获取当前时间
  Example: {"tool": "get_time", "args": {}}
  用途: 查看当前日期时间

search_memory(query: string) - 搜索记忆库
  Example: {"tool": "search_memory", "args": {"query": "之前修改"}}
  用途: 查找历史记录、决策点、遗留待办

code_diff(file1: string, file2: string) - 代码对比
  Example: {"tool": "code_diff", "args": {"file1": "E:/old.py", "file2": "E:/new.py"}}
  用途: 查看代码变更、对比两个版本
  特点: 带行号的unified diff
```

---

## 二、判断规则（System Prompt）

**用户意图识别**：

| 用户关键词 | 推荐工具 | 示例 |
|-----------|---------|------|
| "天气"、"气温"、"温度" | `web_search`（wttr.in国内可用） | "今天福州天气" |
| "访问网页"、"打开网页"、"获取网页" | `web_fetch`（国内可用） | "访问https://weather.com" |
| "搜索"、"baidu"、"google" | `web_fetch` + 搜索URL | "搜索福州天气（需构造搜索URL）" |
| "读取文件"、"查看文件" | `read_file` | "读取E:/test.py文件" |
| "列出文件"、"查看目录" | `list_files` | "列出E:/llm-tools目录" |
| "执行命令"、"运行" | `run_command` | "执行dir命令" |
| "当前时间"、"几点了" | `get_time` | "现在几点" |
| "代码对比"、"查看差异" | `code_diff` | "对比old.py和new.py" |

---

## 三、安全机制

### 安全目录限制
只有以下目录允许文件操作：
```
E:/csi10
E:/brain-system
E:/llm-tools
C:/dev
C:/Users/10341/.openclaw
```

### 危险操作确认
以下操作需要用户确认：
- ✅ `write_file` - 写入文件
- ✅ `run_command` - 执行系统命令
- ✅ `exec_python` - 执行Python代码（可能修改文件）

---

## 四、工具执行流程

```
用户输入: "baidu一下福州天气"
  ↓
LLM决策: {"tool": "web_search", "args": {"query": "福州天气"}}
  ↓
Backend解析: execute_tool("web_search", {"query": "福州天气"})
  ↓
工具执行: wttr.in API → 返回天气数据
  ↓
前端显示: "21°C，小阵雨，风速4km/h，湿度94%"
```

---

## 五、工具调用透明性

**前端显示**：
- 📋 显示正在使用的工具名称
- 📋 显示工具参数
- 📋 显示工具执行结果
- 📋 如果工具失败，显示错误原因

**实现方式**：
- 前端调用 `/api/tool_chat` 端点
- Backend返回 `tool_used`, `tool`, `arguments`, `result`
- 前端解析并显示工具调用信息

---

## 六、工具优先级（借鉴OpenClaw）

| 操作场景 | 优先工具 | 原因 |
|----------|----------|------|
| 文件读取 | `code_read` | 带行号、编码自动检测、支持glob |
| 文件修改 | `file_patch` | 按行号精准替换、自动备份+预览 |
| Python执行 | `exec_python` | 直接执行代码字符串、支持timeout |
| 代码对比 | `code_diff` | 带行号的unified diff |
| 网络搜索 | `web_search` | 使用wttr.in API，支持天气查询 |

---

未经用户明确授权，不得修改本文件内容。