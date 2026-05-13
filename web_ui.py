#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM-Tools Web UI
简单的 Web 界面，让用户通过浏览器与 LLM 交互并自动执行工具

功能：
1. 输入指令 → 自动解析 JSON → 执行工具 → 显示结果
2. 工具列表显示
3. 执行历史记录
4. 实时日志显示

使用方法：
1. 启动服务：python web_ui.py
2. 打开浏览器：http://localhost:5000
3. 输入指令，点击"执行"
"""

from flask import Flask, render_template_string, jsonify, request
import requests
import json
import sys
import os
from datetime import datetime

# ── 导入工具注册中心 ──
sys.path.insert(0, os.path.dirname(__file__))
from tool_registry import tool_registry

# ── 配置 ──
LLAMA_SERVER_URL = "http://127.0.0.1:1235"
MODEL_NAME = "Qwen3.5-9B-Q4_K_M.gguf"

app = Flask(__name__)

# ── HTML 模板 ──
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM-Tools Web UI</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 30px;
        }
        .input-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        textarea {
            width: 100%;
            min-height: 100px;
            padding: 15px;
            border: 2px solid #667eea;
            border-radius: 10px;
            font-size: 14px;
            resize: vertical;
        }
        button {
            background: #667eea;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 10px;
            transition: background 0.3s;
        }
        button:hover {
            background: #764ba2;
        }
        .tools-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .tool-card {
            background: white;
            padding: 15px;
            margin: 10px;
            border-radius: 8px;
            border: 2px solid #667eea;
            display: inline-block;
            width: calc(25% - 20px);
        }
        .tool-name {
            font-weight: bold;
            color: #667eea;
        }
        .tool-desc {
            font-size: 12px;
            color: #666;
        }
        .result-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
        }
        .result-card {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .result-time {
            font-size: 12px;
            color: #999;
        }
        .result-tool {
            font-weight: bold;
            color: #667eea;
        }
        .result-output {
            white-space: pre-wrap;
            font-size: 14px;
        }
        .status {
            text-align: center;
            padding: 10px;
            background: #d4edda;
            color: #155724;
            border-radius: 5px;
            margin-top: 10px;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛠️ LLM-Tools Web UI</h1>
        
        <!-- 输入区域 -->
        <div class="input-section">
            <h2>输入指令</h2>
            <textarea id="input" placeholder="例如：读取 E:/csi10/live_runner.py 的前 20 行"></textarea>
            <button onclick="execute()">执行</button>
            <div id="status"></div>
        </div>
        
        <!-- 工具列表 -->
        <div class="tools-section">
            <h2>可用工具</h2>
            <div id="tools"></div>
        </div>
        
        <!-- 执行结果 -->
        <div class="result-section">
            <h2>执行历史</h2>
            <div id="results"></div>
        </div>
    </div>
    
    <script>
        // 工具列表
        const tools = {{ tools_json }};
        
        function renderTools() {
            const container = document.getElementById('tools');
            container.innerHTML = '';
            
            const categories = {};
            for (const tool of tools) {
                if (!categories[tool.category]) {
                    categories[tool.category] = [];
                }
                categories[tool.category].push(tool);
            }
            
            for (const [category, toolsInCategory] of Object.entries(categories)) {
                toolsInCategory.forEach(tool => {
                    const card = document.createElement('div');
                    card.className = 'tool-card';
                    card.innerHTML = `
                        <div class="tool-name">${tool.name}</div>
                        <div class="tool-desc">${tool.description}</div>
                    `;
                    container.appendChild(card);
                });
            }
        }
        
        // 执行指令
        async function execute() {
            const input = document.getElementById('input').value;
            if (!input.trim()) {
                showStatus('请输入指令', true);
                return;
            }
            
            showStatus('正在执行...');
            
            try {
                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({input: input})
                });
                
                const data = await response.json();
                
                if (data.error) {
                    showStatus('执行失败: ' + data.error, true);
                } else {
                    showStatus('执行成功');
                    renderResults(data.results);
                }
            } catch (error) {
                showStatus('请求失败: ' + error, true);
            }
        }
        
        // 显示状态
        function showStatus(message, isError = false) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = isError ? 'status error' : 'status';
        }
        
        // 显示结果
        function renderResults(results) {
            const container = document.getElementById('results');
            container.innerHTML = '';
            
            results.forEach(result => {
                const card = document.createElement('div');
                card.className = 'result-card';
                card.innerHTML = `
                    <div class="result-time">${result.time}</div>
                    <div class="result-tool">工具: ${result.tool || '模型直接回答'}</div>
                    <div class="result-output">${result.output}</div>
                `;
                container.appendChild(card);
            });
        }
        
        // 初始化
        renderTools();
    </script>
</body>
</html>
"""


# ── Flask 路由 ──
@app.route('/')
def index():
    """主页"""
    # 获取工具列表
    tools = []
    for tool in tool_registry.tools.values():
        tools.append({
            'name': tool.name,
            'description': tool.description,
            'category': tool.category,
        })
    
    return render_template_string(HTML_TEMPLATE, tools_json=json.dumps(tools))


@app.route('/api/execute', methods=['POST'])
def api_execute():
    """执行指令 API"""
    data = request.json
    user_input = data.get('input', '')
    
    if not user_input:
        return jsonify({'error': '请输入指令'})
    
    # 调用 LLM
    try:
        results = execute_with_llm(user_input)
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)})


# ── 核心执行逻辑 ──
def call_llama(prompt: str, system_prompt: str = None) -> str:
    """调用 llama.cpp-server"""
    if system_prompt is None:
        system_prompt = tool_registry.get_all_tools_description()
    
    try:
        response = requests.post(
            f"{LLAMA_SERVER_URL}/v1/chat/completions",
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500,
            },
            timeout=60
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"API 调用失败: {e}"


def parse_tool_call(text: str):
    """解析工具调用 JSON"""
    try:
        return json.loads(text.strip())
    except:
        return None


def execute_with_llm(user_input: str, max_iterations: int = 10):
    """执行用户指令（多轮工具调用）"""
    results = []
    iteration = 0
    
    conversation_history = []
    current_input = user_input
    
    while iteration < max_iterations:
        # 调用 LLM
        output = call_llama(current_input)
        
        # 记录时间
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 解析工具调用
        tool_call = parse_tool_call(output)
        
        if tool_call:
            # 执行工具
            tool_name = tool_call.get('tool')
            args = tool_call.get('args', {})
            
            result_output = tool_registry.execute_tool(tool_name, args)
            
            results.append({
                'time': time_str,
                'tool': tool_name,
                'args': args,
                'output': result_output[:500],  # 限制长度
            })
            
            # 更新对话历史
            conversation_history.append({"role": "user", "content": current_input})
            conversation_history.append({"role": "assistant", "content": output})
            conversation_history.append({"role": "user", "content": f"工具执行结果: {result_output}\n请继续或总结回答。"})
            
            current_input = "根据工具执行结果，继续执行任务或总结回答。"
            iteration += 1
        else:
            # 模型直接回答
            results.append({
                'time': time_str,
                'tool': None,
                'output': output,
            })
            break
    
    return results


# ── 启动服务 ──
if __name__ == '__main__':
    print("=" * 60)
    print("LLM-Tools Web UI")
    print("=" * 60)
    print(f"服务器: {LLAMA_SERVER_URL}")
    print(f"模型: {MODEL_NAME}")
    print("访问地址: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='localhost', port=5000, debug=True)