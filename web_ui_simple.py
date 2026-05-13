#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM-Tools Simple Chat UI - 简化版
确保基本功能能正常工作

使用方法：
1. 启动服务：python web_ui_simple.py
2. 打开浏览器：http://localhost:5000
"""

from flask import Flask, render_template_string, jsonify, request
import requests
import json
import sys
import os

# ── 导入工具注册中心 ──
sys.path.insert(0, os.path.dirname(__file__))
from tool_registry import tool_registry

# ── 配置 ──
LLAMA_SERVER_URL = "http://127.0.0.1:1235"
MODEL_NAME = "Qwen3.5-9B-Q4_K_M.gguf"

app = Flask(__name__)

# ── 简化的 HTML 模板 ──
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LLM-Tools Simple UI</title>
    <style>
        body { font-family: Arial; background: #f0f0f0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        h1 { color: #667eea; text-align: center; }
        .chat { height: 500px; overflow-y: auto; border: 2px solid #667eea; padding: 10px; margin: 20px 0; background: #fafafa; }
        .msg { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user { background: #e3f2fd; border-left: 4px solid #667eea; }
        .assistant { background: #f3e5f5; border-left: 4px solid #9c27b0; }
        .tool { background: #fff3e0; border: 2px solid #ff9800; margin: 10px 0; }
        input { width: 100%; padding: 10px; border: 2px solid #667eea; border-radius: 5px; font-size: 14px; }
        button { width: 100%; padding: 15px; background: #667eea; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; margin-top: 10px; }
        button:hover { background: #764ba2; }
        .label { font-weight: bold; color: #667eea; }
        pre { background: #f5f5f5; padding: 5px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛠️ LLM-Tools Simple UI</h1>
        <div style="text-align: center; color: #999;">
            模型: Qwen3.5-9B | 服务器: http://127.0.0.1:1235
        </div>
        
        <div class="chat" id="chat"></div>
        
        <input id="input" placeholder="输入指令..." type="text">
        <button onclick="send()">发送</button>
    </div>
    
    <script>
        function send() {
            const input = document.getElementById('input').value;
            if (!input) return;
            
            // 显示用户消息
            addMsg('user', '👤 用户: ' + input);
            
            // 发送请求
            fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({input: input})
            })
            .then(r => r.json())
            .then(data => {
                // 显示结果
                if (data.results) {
                    data.results.forEach(r => {
                        if (r.tool) {
                            addMsg('tool', '🔧 工具调用: ' + r.tool + '\\n' + 
                                   '<pre>' + JSON.stringify(r.args, null, 2) + '</pre>\\n' +
                                   '📤 结果: ' + r.output);
                        } else {
                            addMsg('assistant', '🤖 Qwen: ' + r.output);
                        }
                    });
                }
                if (data.error) {
                    addMsg('assistant', '❌ 错误: ' + data.error);
                }
            })
            .catch(e => addMsg('assistant', '❌ 请求失败: ' + e));
            
            document.getElementById('input').value = '';
        }
        
        function addMsg(type, content) {
            const div = document.createElement('div');
            div.className = 'msg ' + type;
            div.innerHTML = content;
            document.getElementById('chat').appendChild(div);
            document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
        }
        
        document.getElementById('input').addEventListener('keypress', e => {
            if (e.key === 'Enter') send();
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    user_input = data.get('input', '')
    
    if not user_input:
        return jsonify({'error': '请输入指令'})
    
    try:
        results = execute_with_llm(user_input)
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)})


def call_llama(prompt):
    """调用 llama.cpp-server"""
    system_prompt = tool_registry.get_all_tools_description()
    
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


def parse_tool_call(text):
    """解析工具调用"""
    try:
        return json.loads(text.strip())
    except:
        return None


def execute_with_llm(user_input, max_iterations=10):
    """执行用户指令"""
    results = []
    iteration = 0
    current_input = user_input
    
    while iteration < max_iterations:
        # 调用 LLM
        output = call_llama(current_input)
        
        # 解析工具调用
        tool_call = parse_tool_call(output)
        
        if tool_call:
            # 执行工具
            tool_name = tool_call.get('tool')
            args = tool_call.get('args', {})
            result = tool_registry.execute_tool(tool_name, args)
            
            results.append({
                'tool': tool_name,
                'args': args,
                'output': result[:500]  # 限制长度
            })
            
            current_input = f"工具结果: {result}\\n继续或总结回答。"
            iteration += 1
        else:
            # 模型直接回答
            results.append({
                'output': output
            })
            break
    
    return results


if __name__ == '__main__':
    print("=" * 60)
    print("LLM-Tools Simple UI")
    print("=" * 60)
    print("访问地址: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='localhost', port=5000, debug=False)