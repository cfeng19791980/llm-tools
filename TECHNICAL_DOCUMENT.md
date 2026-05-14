# LLM-Tools v3.0 技术文档

---

## 文档版本

| 项目 | 信息 |
|------|------|
| **文档版本** | v1.0 |
| **系统版本** | v3.0（集中配置管理） |
| **文档日期** | 2026-05-14 |
| **作者** | LLM-Tools团队 |

---

## 目录

1. [设计原理](#一设计原理)
2. [系统架构](#二系统架构)
3. [核心功能](#三核心功能)
4. [API接口文档](#四api接口文档)
5. [工具注册机制](#五工具注册机制)
6. [配置管理](#六配置管理)
7. [部署指南](#七部署指南)
8. [版本演进](#八版本演进)

---

## 一、设计原理

### 1.1 核心设计理念

LLM-Tools的设计借鉴了**OpenClaw**的Agent架构，实现真正的Agent级别多轮决策系统。

#### **设计原则**：

| 原则 | 说明 |
|------|------|
| **Agent级别决策** | LLM自动决策工具调用，无需用户干预 |
| **Steering机制** | 工具执行后注入决策指令，引导LLM下一步行动 |
| **错误感知深度** | 识别具体错误类型，自动切换工具 |
| **集中配置管理** | 借鉴openclaw.json，参数集中管理 |
| **流式输出** | 实时返回LLM输出，提升用户体验 |

---

### 1.2 OpenClaw架构借鉴

#### **OpenClaw核心机制**：

| 机制 | LLM-Tools实现 |
|------|--------------|
| **Steering机制** | 工具执行后注入决策指令（model_manager.py Line 792-834） |
| **Runtime Boundary** | Turn → Tool Execution → Steering → Next Turn |
| **Queue模式** | steer（失败决策） / followup（成功决策） |
| **集中配置管理** | llm-tools-config.json（借鉴openclaw.json） |

---

### 1.3 Agent级别能力验证

#### **v2.1达到的Agent级别能力**：

| 能力 | 验证结果 |
|------|---------|
| **自动决策** | ✅ 不询问用户，直接决策执行 |
| **任务连贯性** | ✅ 工具执行 → Steering → 完成 |
| **错误感知深度** | ✅ 识别TimeoutError/PermissionError/FileNotFoundError/KeyError |
| **动态路由** | ✅ 自动选择替代工具 |

---

## 二、系统架构

### 2.1 架构层级图

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (index.html)                  │
│              用户界面 + 流式对话 + 工具调用显示            │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP请求（端口5003）
┌────────────────────────▼────────────────────────────────┐
│              Backend API (model_manager.py)               │
│           Flask + Steering机制 + 工具调用路由              │
└────────────────────────┬────────────────────────────────┘
                         │ LLM调用（端口1235）
┌────────────────────────▼────────────────────────────────┐
│           LLM Inference (llama-server.exe)                │
│           Qwen3.5-9B-Q4_K_M.gguf + 工具决策               │
└────────────────────────┬────────────────────────────────┘
                         │ 工具执行请求
┌────────────────────────▼────────────────────────────────┐
│            Tool Registry (tool_registry.py)               │
│          工具注册 + 安全检查 + 错误感知深度                 │
└────────────────────────┬────────────────────────────────┘
                         │ 工具执行
┌────────────────────────▼────────────────────────────────┐
│                  System Tools (16个工具)                  │
│      read_file, write_file, run_command, web_search等    │
└─────────────────────────────────────────────────────────┘
```

---

### 2.2 核心模块说明

#### **model_manager.py**（Backend核心逻辑）：

| 功能模块 | 代码位置 | 说明 |
|---------|---------|------|
| **配置管理** | Line 19-49 | 读取llm-tools-config.json |
| **进程管理** | Line 54-94 | PID保存/加载/检查 |
| **API端点** | Line 100-1040 | 18个API端点 |
| **Steering机制** | Line 792-834 | 工具执行后决策注入 |
| **工具调用路由** | Line 703-920 | /api/tool_chat_stream核心逻辑 |

---

#### **tool_registry.py**（工具注册机制）：

| 功能模块 | 代码位置 | 说明 |
|---------|---------|------|
| **配置管理** | Line 12-31 | 读取llm-tools-config.json |
| **工具定义** | Line 42-51 | ToolDefinition数据类 |
| **工具注册** | Line 180-280 | 16个内置工具注册 |
| **工具执行** | Line 106-168 | 安全检查 + 错误感知深度 |
| **错误感知** | Line 148-167 | TimeoutError/PermissionError/FileNotFoundError/KeyError识别 |

---

#### **llm-tools-config.json**（集中配置管理）：

| 配置模块 | 说明 |
|---------|------|
| **backend** | Backend端口（5003）、host、cors配置 |
| **llm** | LLM端口（1235）、模型名、max_tokens、temperature |
| **tools** | safe_dirs、requiresConfirmation、maxHistory |
| **memory** | historyFile路径 |
| **version** | 版本信息（v3.0） |
| **paths** | 配置目录、PID文件、模型目录 |

---

### 2.3 数据流架构

#### **工具调用完整流程**：

```
用户输入（前端）
  ↓ POST /api/tool_chat_stream
Backend接收请求
  ↓ 构建messages（携带历史）
调用LLM推理服务（端口1235）
  ↓ 流式返回输出
检测工具JSON输出
  ↓ {"tool": "read_file", "args": {"path": "..."}}
执行工具（tool_registry.py）
  ↓ 安全检查 + 工具执行
Steering机制注入
  ↓ "请根据结果立即决策下一步行动"
再次调用LLM
  ↓ LLM分析结果并决策
流式返回最终回复
  ↓ 用户看到完整回复
```

---

## 三、核心功能

### 3.1 流式对话（Streaming Chat）

#### **功能说明**：

| 功能 | 说明 |
|------|------|
| **流式输出** | 实时返回LLM输出，提升用户体验 |
| **对话历史** | 携带完整历史（修复对话连贯性问题） |
| **工具调用显示** | 显示工具名称、参数、执行结果 |

#### **API端点**：

```
POST /api/tool_chat_stream
```

#### **参数设定**：

| 参数 | 类型 | 说明 |
|------|------|------|
| **messages** | array | 对话历史（role + content） |
| **port** | int | LLM端口（默认1235） |

---

### 3.2 Agent级别多轮决策

#### **Steering机制**：

| Steering类型 | 触发条件 | 决策内容 |
|-------------|---------|---------|
| **失败决策** | 工具执行失败（包含"❌"/"失败"/"错误"/"Error"） | "识别错误类型 → 自动切换工具 → 修复参数重试" |
| **成功决策** | 工具执行成功（包含"✅"/"成功"/"完成"） | "自动后续调用 → 无需用户二次输入" |

#### **Steering指令格式**：

```python
# 失败决策（Line 799-817）
steering_content = steering_base + """
请立即采取修复行动（不询问用户）：
1. 识别错误类型 - 根据错误信息识别是超时、权限、参数还是路径错误
2. 自动切换工具 - 根据错误类型选择替代工具
3. 修复参数重试 - 如果参数错误，修正后立即重试
4. 直接决策执行 - 不询问用户，直接输出工具JSON
"""

# 成功决策（Line 818-828）
steering_content = steering_base + """
请立即执行后续逻辑（不询问用户）：
1. 确认任务完成 - 如果任务已完成，回复用户"任务已完成"
2. 自动后续调用 - 如果需要后续操作，直接输出工具JSON
3. 整合结果回复 - 整合工具执行结果回复用户
"""
```

---

### 3.3 错误感知深度

#### **错误类型识别**：

| 错误类型 | 工具执行结果 | 应对策略 |
|---------|-------------|---------|
| **TimeoutError** | "❌ TimeoutError: 工具执行超时，建议切换到run_command工具绕过Python层" | 切换run_command |
| **PermissionError** | "❌ PermissionError: 权限不足，建议切换到run_command工具使用系统命令" | 切换run_command |
| **FileNotFoundError** | "❌ FileNotFoundError: 文件不存在，建议检查路径或创建文件" | 检查路径 |
| **KeyError** | "❌ KeyError: 缺少必需参数 '{param}'，建议补充参数后重试" | 补充参数 |

#### **代码位置**：

```python
# tool_registry.py Line 148-167
except TimeoutError:
    error_result = f"❌ TimeoutError: 工具执行超时，建议切换到run_command工具绕过Python层"
    ...
except PermissionError:
    error_result = f"❌ PermissionError: 权限不足，建议切换到run_command工具使用系统命令"
    ...
except FileNotFoundError:
    error_result = f"❌ FileNotFoundError: 文件不存在，建议检查路径或创建文件"
    ...
except KeyError as e:
    error_result = f"❌ KeyError: 缺少必需参数 '{str(e)}'，建议补充参数后重试"
    ...
```

---

### 3.4 集中配置管理

#### **设计借鉴**：

借鉴**openclaw.json**的集中配置管理架构，将分散在各处的配置参数集中到单一文件管理。

#### **优势**：

| 优势 | 说明 |
|------|------|
| **一目了然** | 直观而简单 |
| **修改便捷** | 只改config.json，不改代码 |
| **版本管理** | 单文件Git管理 |
| **配置备份** | 只备份config.json |
| **配置迁移** | 只迁移config.json |

---

## 四、API接口文档

### 4.1 API端点列表

| 端点 | 功能 | 位置 |
|------|------|------|
| `/` | 提供前端页面 | Line 100 |
| `/api/status` | 获取模型状态 | Line 106 |
| `/api/start` | 启动模型 | Line 112 |
| `/api/stop` | 停止模型 | Line 197 |
| `/api/save_config` | 保存配置为bat文件 | Line 242 |
| `/api/load_config` | 载入配置 | Line 304 |
| `/api/list_configs` | 列出所有配置 | Line 337 |
| `/api/models` | 列出可用模型 | Line 359 |
| `/api/inference_status` | 获取推理服务状态 | Line 442 |
| `/api/test_inference` | 测试推理服务 | Line 449 |
| `/api/list_tools` | 列出可用工具 | Line 496 |
| `/api/execute_tool` | 执行工具 | Line 521 |
| `/api/tool_chat` | 工具对话（非流式） | Line 540 |
| `/api/stream_chat` | 流式聊天（无工具） | Line 640 |
| `/api/tool_chat_stream` | 智能流式聊天（工具+流式） | Line 703 |
| `/api/system_status` | 获取系统状态 | Line 931 |
| `/api/list_presets` | 列出预设配置 | Line 965 |
| `/api/apply_preset` | 应用预设配置 | Line 985 |

---

### 4.2 核心API详细说明

#### **4.2.1 /api/tool_chat_stream**（智能流式聊天）

**功能**：工具调用 + 流式输出 + 对话历史 + Steering机制

**请求方法**：POST

**请求参数**：

```json
{
  "messages": [
    {"role": "user", "content": "用户输入"}
  ],
  "port": 1235
}
```

**响应格式**：流式SSE

```json
data: {"content": "LLM输出片段"}

data: {"tool_used": "read_file", "arguments": {"path": "E:/test.txt"}}

data: {"tool_result": "✅ 文件内容..."}

data: {"done": true}
```

**代码位置**：model_manager.py Line 703-920

---

#### **4.2.2 /api/status**（获取模型状态）

**功能**：检查LLM推理服务是否运行

**请求方法**：GET

**响应格式**：

```json
{
  "running": true,
  "pid": 12345,
  "model": "Qwen3.5-9B-Q4_K_M.gguf",
  "port": 1235,
  "start_time": "2026-05-14 20:00:00"
}
```

**代码位置**：model_manager.py Line 106-110

---

#### **4.2.3 /api/list_tools**（列出可用工具）

**功能**：列出所有注册工具及参数说明

**请求方法**：GET

**响应格式**：

```json
{
  "tools": [
    {
      "name": "read_file",
      "description": "读取文件内容",
      "parameters": {
        "path": {"type": "string", "required": true}
      },
      "category": "file"
    }
  ]
}
```

**代码位置**：model_manager.py Line 496-520

---

### 4.3 API参数设定

#### **Backend端口**：5003（从config.json读取）

#### **LLM端口**：1235（从config.json读取）

#### **max_tokens设定**：

| 场景 | max_tokens | 说明 |
|------|-----------|------|
| **工具决策** | 500 | 允许输出完整工具JSON |
| **最终回复** | 1000 | 允许输出完整回复 |

---

## 五、工具注册机制

### 5.1 工具列表

| 工具名 | 类别 | 功能说明 | requires_confirmation |
|--------|------|---------|---------------------|
| **read_file** | file | 读取文件内容 | false |
| **write_file** | file | 写入文件 | true |
| **list_files** | file | 列出目录文件 | false |
| **code_read** | code | 读取代码文件（支持行号、通配符） | false |
| **code_edit** | code | 编辑代码文件（精确替换） | true |
| **run_command** | system | 执行shell命令 | true |
| **web_search** | web | 网络搜索（17个搜索引擎） | false |
| **multi_search_engine** | web | 多搜索引擎聚合（17引擎） | false |

---

### 5.2 工具注册位置

#### **tool_registry.py Line 180-280**：

```python
def _register_builtin_tools(self):
    """注册内置工具"""
    
    # 文件操作工具
    self.register_tool(ToolDefinition(
        name="read_file",
        description="读取文件内容",
        parameters={"path": {"type": "string", "required": True}},
        function=self._read_file,
        category="file",
    ))
    
    # ... 其他工具注册
```

---

### 5.3 工具执行流程

#### **execute_tool()函数**（Line 106-168）：

```python
def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
    """执行工具"""
    
    # 1. 工具查找
    tool = self.get_tool(tool_name)
    
    # 2. 参数验证
    for param_name, param_def in tool.parameters.items():
        if param_def.get("required") and param_name not in args:
            return f"❌ 缺少必需参数: {param_name}"
    
    # 3. 安全检查（文件操作）
    if tool.category == "file":
        path = args.get("path", "")
        if not self._is_safe_path(path, tool.safe_dirs):
            return f"❌ 拒绝访问：路径不在允许目录中"
    
    # 4. 工具执行（错误感知深度）
    try:
        result = tool.function(**args)
        ...
    except TimeoutError:
        return f"❌ TimeoutError: 工具执行超时，建议切换到run_command工具"
    except PermissionError:
        return f"❌ PermissionError: 权限不足，建议切换到run_command工具"
    ...
```

---

### 5.4 safe_dirs配置

#### **从config.json读取**（tool_registry.py Line 68）：

```python
self.safe_dirs = CONFIG['tools']['safeDirs']
```

#### **允许目录**：

```
E:/llm-tools
E:/csi10
E:/web-test-platform
```

---

## 六、配置管理

### 6.1 llm-tools-config.json结构

```json
{
  "backend": {
    "port": 5003,
    "host": "127.0.0.1",
    "cors": true
  },
  "llm": {
    "port": 1235,
    "model": "Qwen3.5-9B-Q4_K_M.gguf",
    "maxTokens": {
      "toolJudge": 500,
      "finalReply": 1000
    },
    "temperature": {
      "toolJudge": 0.05,
      "finalReply": 0.7
    }
  },
  "tools": {
    "safeDirs": [
      "E:/llm-tools",
      "E:/csi10",
      "E:/web-test-platform"
    ],
    "requiresConfirmation": [
      "run_command",
      "write_file",
      "code_edit"
    ],
    "maxHistory": 100
  },
  "memory": {
    "historyFile": "E:/llm-tools/logs/history.json"
  },
  "version": {
    "current": "v3.0",
    "phase": "config-management",
    "agentLevel": true,
    "configVersion": "v1.0"
  },
  "paths": {
    "configDir": "E:/llm-tools/model_configs",
    "pidFile": "E:/llm-tools/.model_pid.json",
    "modelsDir": "C:/Users/10341/.lmstudio/models"
  }
}
```

---

### 6.2 配置读取代码

#### **model_manager.py Line 23-37**：

```python
def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 默认配置（兼容旧版本）
        return {
            'backend': {'port': 5003, 'host': '127.0.0.1', 'cors': True},
            'llm': {'port': 1235, 'model': 'Qwen3.5-9B-Q4_K_M.gguf'},
            'tools': {'safeDirs': ['E:/llm-tools']}
        }

# 加载配置
CONFIG = load_config()
```

---

### 6.3 配置参数使用

#### **参数使用位置**：

| 参数 | 使用位置 | 说明 |
|------|---------|------|
| **Backend端口** | model_manager.py Flask启动 | app.run(port=CONFIG['backend']['port']) |
| **LLM端口** | model_manager.py API调用 | requests.post(f'http://127.0.0.1:{port}') |
| **模型名** | model_manager.py Line 119 | model_name = CONFIG['llm']['model'] |
| **max_tokens** | model_manager.py Line 765 | CONFIG['llm']['maxTokens']['toolJudge'] |
| **safe_dirs** | tool_registry.py Line 68 | CONFIG['tools']['safeDirs'] |

---

## 七、部署指南

### 7.1 系统要求

| 项目 | 要求 |
|------|------|
| **操作系统** | Windows 10/11 |
| **Python版本** | Python 3.8+ |
| **LLM推理引擎** | llama-server.exe（llama.cpp） |
| **LLM模型** | Qwen3.5-9B-Q4_K_M.gguf |
| **依赖包** | Flask, Flask-CORS, psutil, requests |

---

### 7.2 目录结构

```
E:/llm-tools/
├── model_manager.py          # Backend核心逻辑
├── tool_registry.py           # 工具注册机制
├── llm-tools-config.json      # 集中配置管理
├── index.html                 # 前端界面
├── multi_search_engine_17.py  # 多搜索引擎
├── tool_history.py            # 工具历史记录
├── VERSION.json               # 版本信息
├── 启动_LLM-Tools.bat         # 一键启动脚本
└── logs/
    └── history.json           # 对话历史
```

---

### 7.3 启动步骤

#### **步骤1：启动LLM推理服务**

```bash
python model_manager.py
# 自动检查并启动LLM推理服务（端口1235）
```

#### **步骤2：访问前端界面**

```
http://127.0.0.1:5003/
```

---

### 7.4 端口配置

| 端口 | 服务 | 说明 |
|------|------|------|
| **5003** | Backend API | Flask服务 |
| **1235** | LLM Inference | llama-server推理服务 |

---

## 八、版本演进

### 8.1 版本历史

| 版本 | 改进内容 | 时间 |
|------|---------|------|
| **v1.x** | 工具执行者（硬编码参数） | 早期版本 |
| **v2.0** | Agent级别（Steering决策机制） | 2026-05-14 |
| **v2.1** | Agent级别优化（自动决策，不询问用户） | 2026-05-14 |
| **v3.0** | 集中配置管理（llm-tools-config.json） | 2026-05-14 |

---

### 8.2 关键改进

#### **v2.0改进**：

- Steering决策机制实施
- 工具调用多步骤流程
- max_tokens修复（100→500）

#### **v2.1改进**：

- Steering指令优化（不询问用户）
- 错误感知深度（识别具体错误类型）
- Agent级别能力验证通过

#### **v3.0改进**：

- llm-tools-config.json创建
- model_manager.py读取config.json
- tool_registry.py读取config.json
- 借鉴openclaw.json集中配置管理

---

### 8.3 Git提交记录

| 版本 | Commit Hash | 说明 |
|------|------------|------|
| **v2.0** | 4e5c73e | Phase 2完整实施 |
| **v3.0** | ddd8db4 | 集中配置管理实施 |

---

## 附录

### A. 关键代码位置索引

| 功能 | 文件 | 行号 |
|------|------|------|
| **配置读取** | model_manager.py | 19-37 |
| **Steering机制** | model_manager.py | 792-834 |
| **工具调用路由** | model_manager.py | 703-920 |
| **错误感知** | tool_registry.py | 148-167 |
| **工具注册** | tool_registry.py | 180-280 |

---

### B. 参数设定参考

| 参数 | 默认值 | 说明 |
|------|-------|------|
| **backend.port** | 5003 | Backend API端口 |
| **llm.port** | 1235 | LLM推理服务端口 |
| **llm.model** | Qwen3.5-9B-Q4_K_M.gguf | 模型名 |
| **llm.maxTokens.toolJudge** | 500 | 工具决策max_tokens |
| **llm.maxTokens.finalReply** | 1000 | 最终回复max_tokens |
| **llm.temperature.toolJudge** | 0.05 | 工具决策temperature |
| **llm.temperature.finalReply** | 0.7 | 最终回复temperature |

---

### C. 备份位置

| 备份版本 | 位置 |
|---------|------|
| **v1.x备份** | E:/llm-tools-backups/v1.x-before-agent-upgrade/ |
| **v2.0备份** | E:/llm-tools-backups/v2.0-before-phase2/ |
| **v2.1备份** | E:/llm-tools-backups/v2.1-before-config-json/ |

---

**文档结束**

**文档作者**: LLM-Tools团队

**文档日期**: 2026-05-14

**系统版本**: v3.0（集中配置管理）

**状态**: ✅✅✅✅✅✅✅✅✅✅✅✅✅ 完整技术文档