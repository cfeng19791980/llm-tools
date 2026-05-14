
# LLM-Tools

> 版本: **v2.0.0 - Agent-Level Multi-Turn Decision**
> 发布日期: 2026-05-14
> 升级时间: 18:03:19

---

## 🎯 v2.0新特性

### **Phase 1: Steering决策机制** ✅

- ✅ 工具执行后注入决策指令
- ✅ 失败时自动修复/重试决策
- ✅ 成功时后续任务管理

### **Phase 2: 循环机制** 🔄

- 🔄 允许连续工具调用
- 🔄 Session transcript持久化
- 🔄 最大迭代次数限制

### **Phase 3: Compaction + Retry** 🧹

- 🧹 长对话自动压缩
- 🧹 失败自动重试
- 🧹 Queue多模式管理

---

# LLM-Tools

**AI工具调用平台 - 让本地LLM能够使用工具**

## 🎯 项目简介

LLM-Tools是一个基于llama.cpp的智能工具调用平台，让本地LLM（如Qwen、LLaMA等）能够使用工具（web_search、文件操作、代码执行等）。

## ✨ 核心特性

### **智能聊天API**
- ✅ **工具调用 + 流式输出**：自动判断是否需要工具，流式返回结果
- ✅ **SSE实时通信**：Server-Sent Events实时推送
- ✅ **多种事件类型**：tool_used、tool_result、content、done

### **工具调用**
- ✅ **Web搜索**：实时搜索天气、新闻等
- ✅ **文件操作**：读取、写入、列出文件
- ✅ **代码执行**：运行Python脚本
- ✅ **智能判断**：LLM自动决定是否调用工具

### **美化UI**
- ✅ **霓虹主题**：现代化UI设计（Dark、Light、Eye-Care主题）
- ✅ **流式显示**：逐字输出，实时响应
- ✅ **工具信息可视化**：蓝色框显示工具调用详情

## 🔧 技术栈

| 技术 | 用途 |
|------|------|
| **Flask** | Backend API服务器 |
| **Flask-CORS** | 跨域支持 |
| **llama.cpp** | 本地LLM推理服务 |
| **Qwen3.5-9B** | 智能模型 |
| **SSE** | 流式输出 |
| **Vue.js风格** | 响应式前端 |

## 📊 API端点

| API | 工具调用 | 流式输出 | 说明 |
|------|---------|---------|------|
| `/api/tool_chat_stream` | ✅ | ✅ | **智能聊天（推荐）** |
| `/api/stream_chat` | ❌ | ✅ | 简单流式聊天 |
| `/api/tool_chat` | ✅ | ❌ | 工具调用（非流式） |
| `/api/status` | - | - | Backend状态 |
| `/api/models` | - | - | 模型列表 |
| `/api/list_tools` | - | - | 工具列表 |

## 🚀 快速开始

### **1. 启动llama-server**
```bash
llama-server -m Qwen3.5-9B-Q4_K_M.gguf --port 1235
```

### **2. 启动Backend**
```bash
cd E:/llm-tools
python model_manager.py
```

Backend会在 http://127.0.0.1:5003 运行

### **3. 启动前端**
```bash
# 方式1：Python HTTP服务器
python simple_http_server.py

# 方式2：直接打开
打开浏览器访问 http://127.0.0.1:8082/index.html
```

### **4. 测试**
- 输入"福州天气" → 显示工具调用信息（蓝色框）
- 输入"你好" → 流式显示回复（逐字输出）

## 📁 项目结构

```
E:/llm-tools/
├── model_manager.py          # Backend API服务器
├── index.html                # 前端界面（霓虹主题）
├── simple_http_server.py     # HTTP服务器
├── stream_api.py             # 流式API
├── tool_registry.py          # 工具注册
├── IDENTITY.md               # 角色定义
├── TOOLS.md                  # 工具描述
├── README.md                 # 项目文档
├── requirements.txt          # 依赖列表
└── .gitignore                # Git忽略文件
```

## 🔍 工作原理

### **智能聊天流程**：
```
1. 用户输入
2. Backend读取System Prompt（IDENTITY.md + TOOLS.md）
3. Backend调用LLM判断是否需要工具（非流式，max_tokens=100）
4. 如果需要工具：
   - 执行工具
   - 流式返回工具结果
5. 如果不需要工具：
   - 流式输出LLM回复（逐字显示）
```

### **SSE事件类型**：
```javascript
data: {"tool_used": true, "tool": "web_search", "arguments": {...}}
data: {"tool_result": "工具执行结果"}
data: {"content": "LLM输出的一个字符"}
data: {"done": true}
```

## 💡 关键设计

### **工具调用判断**：
- ✅ LLM根据System Prompt自动决定是否调用工具
- ✅ 输出JSON格式：`{"tool": "tool_name", "args": {...}}`
- ✅ Backend解析JSON，执行工具

### **流式输出实现**：
- ✅ SSE（Server-Sent Events）
- ✅ llama-server启用stream=true
- ✅ 前端逐字显示（打字机效果）

### **美化UI**：
- ✅ 霓虹主题（Dark、Light、Eye-Care）
- ✅ 响应式设计
- ✅ 工具调用信息可视化（蓝色框）

## 🎯 使用场景

- ✅ 智能问答（天气、新闻、知识）
- ✅ 文件操作（读取、写入、编辑）
- ✅ 代码执行（运行Python脚本）
- ✅ 长文本生成（写文章、写诗）
- ✅ 实时聊天（流式输出）

## 📝 更新日志

### **v1.0（2026-05-13）**
- ✅ 流式输出实现（SSE）
- ✅ 工具调用功能（web_search、文件操作、代码执行）
- ✅ 智能聊天API `/api/tool_chat_stream`
- ✅ 美化UI（霓虹主题）
- ✅ 工具调用信息可视化
- ✅ 修复sendMessage未定义问题
- ✅ 修复CORS跨域问题
- ✅ 修复超时问题（timeout=60秒）
- ✅ 修复截断问题（max_tokens=1000）

## 🙏 致谢

- ✅ llama.cpp - 本地LLM推理引擎
- ✅ Qwen团队 - Qwen3.5-9B模型
- ✅ Flask - Backend框架
- ✅ 用户反馈 - 所有问题修复都来自用户洞察

## 📄 License

MIT License

---

**LLM-Tools让本地LLM变得更智能！** 🎉