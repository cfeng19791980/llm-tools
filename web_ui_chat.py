#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM-Tools Web UI - 类似 OpenClaw 的聊天界面
集成 llama.cpp-server，显示完整的工具调用过程

功能：
1. 聊天界面（类似 OpenClaw）
2. 实时显示模型输出
3. 显示工具调用过程（JSON 解析、工具执行）
4. 显示工具执行结果
5. 多轮对话支持

使用方法：
1. 启动服务：python web_ui_chat.py
2. 打开浏览器：http://localhost:5000
3. 输入指令，查看完整的工具调用过程
"""

from flask import Flask, render_template_string, jsonify, request, Response
import requests
import json
import sys
import os
import time
from datetime import datetime

# ── 导入工具注册中心 ──
sys.path.insert(0, os.path.dirname(__file__))
from tool_registry import tool_registry

# ── 配置 ──
LLAMA_SERVER_URL = "http://127.0.0.1:1235"
MODEL_NAME = "Qwen3.5-9B-Q4_K_M.gguf"

app = Flask(__name__)

# ── HTML 模板（类似 OpenClaw）──
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM-Tools Chat UI</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #1a1a2e;
            margin: 0;
            padding: 0;
            color: #eee;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        h1 {
            margin: 0;
            color: white;
            text-align: center;
        }
        .chat-container {
            background: #16213e;
            border-radius: 15px;
            padding: 20px;
            height: 600px;
            overflow-y: auto;
            border: 2px solid #667eea;
        }
        .message {
            margin: 10px 0;
            padding: 15px;
            border-radius: 10px;
            position: relative;
        }
        .user-message {
            background: #0f3460;
            border-left: 4px solid #667eea;
        }
        .assistant-message {
            background: #1a1a2e;
            border-left: 4px solid #764ba2;
        }
        .tool-call {
            background: #0f3460;
            border: 2px solid #e94560;
            margin: 10px 0;
            padding: 10px;
            border-radius: 8px;
        }
        .tool-result {
            background: #16213e;
            border: 2px solid #00d9ff;
            margin: 10px 0;
            padding: 10px;
            border-radius: 8px;
            color: #00d9ff;
        }
        .label {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        .json-display {
            background: #000;
            padding: 10px;
            border-radius: 5px;
            color: #00ff00;
            font-family: monospace;
            overflow-x: auto;
        }
        .input-container {
            background: #16213e;
            padding: 20px;
            border-radius: 15px;
            margin-top: 20px;
            border: 2px solid #667eea;
        }
        textarea {
            width: 100%;
            min-height: 60px;
            padding: 15px;
            border: 2px solid #667eea;
            border-radius: 10px;
            font-size: 14px;
            background: #1a1a2e;
            color: #eee;
            resize: none;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 10px;
            width: 100%;
        }
        button:hover {
            opacity: 0.9;
        }
        .loading {
            text-align: center;
            color: #667eea;
            padding: 10px;
        }
        .step-counter {
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
            display: inline-block;
            margin-bottom: 5px;
        }
        .clear-btn {
            background: #e94560;
            margin-top: 5px;
            width: auto;
            padding: 10px 20px;
        }
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #16213e;
        }
        ::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛠️ LLM-Tools Chat UI</h1>
            <div style="text-align: center; margin-top: 10px;">
                <span>模型: Qwen3.5-9B</span>
                <span style="margin-left: 20px;">服务器: http://127.0.0.1:1235</span>
            </div>
        </div>
        
        <!-- 聊天容器 -->
        <div class="chat-container" id="chat">
            <div style="text-align: center; color: #667eea; padding: 20px;">
                欢迎使用 LLM-Tools Chat UI！输入指令，查看完整的工具调用过程。
            </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="input-container">
            <textarea id="input" placeholder="输入指令..."></textarea>
            <button onclick="sendMessage()">发送</button>
            <button class="clear-btn" onclick="clearChat()">清空对话</button>
        </div>
    </div>
    
    <script>
        const chatContainer = document.getElementById('chat');
        let conversationHistory = [];
        
        // 发送消息
        async function sendMessage() {
            const input = document.getElementById('input').value;
            if (!input.trim()) return;
            
            // 显示用户消息
            addMessage('user', input);
            
            // 显示加载状态
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.innerHTML = '⏳ 正在处理...';
            chatContainer.appendChild(loadingDiv);
            
            // 发送请求
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({input: input})
                });
                
                // 移除加载状态
                chatContainer.removeChild(loadingDiv);
                
                // 流式读取结果
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                while (true) {
                    const {value, done} = await reader.read();
                    if (done) break;
                    
                    const text = decoder.decode(value);
                    const lines = text.split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const jsonStr = line.substring(6);
                            try {
                                const data = JSON.parse(jsonStr);
                                processEvent(data);
                            } catch (e) {}
                        }
                    }
                }
            } catch (error) {
                chatContainer.removeChild(loadingDiv);
                addMessage('error', '请求失败: ' + error);
            }
            
            // 清空输入
            document.getElementById('input').value = '';
            
            // 滚动到底部
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // 处理事件
        function processEvent(data) {
            if (data.type === 'step') {
                addStep(data.step, data.message);
            } else if (data.type === 'tool_call') {
                addToolCall(data.tool, data.args);
            } else if (data.type === 'tool_result') {
                addToolResult(data.result);
            } else if (data.type === 'assistant') {
                addMessage('assistant', data.content);
            } else if (data.type === 'done') {
                addMessage('system', '✅ 任务完成');
            }
            
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // 添加消息
        function addMessage(type, content) {
            const div = document.createElement('div');
            div.className = 'message ' + type + '-message';
            
            const label = document.createElement('div');
            label.className = 'label';
            label.textContent = type === 'user' ? '👤 用户' : 
                               type === 'assistant' ? '🤖 Qwen' : '系统';
            div.appendChild(label);
            
            const text = document.createElement('div');
            text.textContent = content;
            div.appendChild(text);
            
            chatContainer.appendChild(div);
        }
        
        // 添加步骤计数
        function addStep(step, message) {
            const div = document.createElement('div');
            div.className = 'tool-call';
            
            const stepLabel = document.createElement('div');
            stepLabel.className = 'step-counter';
            stepLabel.textContent = '步骤 ' + step;
            div.appendChild(stepLabel);
            
            const msg = document.createElement('div');
            msg.textContent = message;
            div.appendChild(msg);
            
            chatContainer.appendChild(div);
        }
        
        // 添加工具调用
        function addToolCall(tool, args) {
            const div = document.createElement('div');
            div.className = 'tool-call';
            
            const label = document.createElement('div');
            label.className = 'label';
            label.textContent = '🔧 工具调用';
            div.appendChild(label);
            
            const jsonDiv = document.createElement('div');
            jsonDiv.className = 'json-display';
            jsonDiv.textContent = JSON.stringify({tool: tool, args: args}, null, 2);
            div.appendChild(jsonDiv);
            
            chatContainer.appendChild(div);
        }
        
        // 添加工具结果
        function addToolResult(result) {
            const div = document.createElement('div');
            div.className = 'tool-result';
            
            const label = document.createElement('div');
            label.className = 'label';
            label.textContent = '📤 工具执行结果';
            div.appendChild(label);
            
            const text = document.createElement('div');
            text.style.whiteSpace = 'pre-wrap';
            text.textContent = result;
            div.appendChild(text);
            
            chatContainer.appendChild(div);
        }
        
        // 清空对话
        function clearChat() {
            chatContainer.innerHTML = '<div style="text-align: center; color: #667eea; padding: 20px;">对话已清空</div>';
            conversationHistory = [];
        }
        
        // 回车发送
        document.getElementById('input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""


# ── Flask 路由 ──
@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """聊天 API（流式响应）"""
    data = request.json
    user_input = data.get('input', '')
    
    if not user_input:
        return jsonify({'error': '请输入指令'})
    
    # 流式响应
    def generate():
        try:
            results = execute_with_llm_stream(user_input)
            for event in results:
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


# ── 核心执行逻辑（流式）──
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


def execute_with_llm_stream(user_input: str, max_iterations: int = 10):
    """执行用户指令（流式返回事件）"""
    
    iteration = 0
    current_input = user_input
    
    conversation_history = []
    
    while iteration < max_iterations:
        # 发送步骤事件
        yield {
            'type': 'step',
            'step': iteration + 1,
            'message': f'正在调用模型...'
        }
        
        # 调用 LLM
        output = call_llama(current_input)
        
        # 解析工具调用
        tool_call = parse_tool_call(output)
        
        if tool_call:
            # 发送工具调用事件
            yield {
                'type': 'tool_call',
                'tool': tool_call.get('tool'),
                'args': tool_call.get('args', {})
            }
            
            # 执行工具
            tool_name = tool_call.get('tool')
            args = tool_call.get('args', {})
            result = tool_registry.execute_tool(tool_name, args)
            
            # 发送工具结果事件
            yield {
                'type': 'tool_result',
                'result': result
            }
            
            # 更新对话历史
            conversation_history.append({"role": "user", "content": current_input})
            conversation_history.append({"role": "assistant", "content": output})
            conversation_history.append({"role": "user", "content": f"工具执行结果: {result}\n请继续或总结回答。"})
            
            current_input = "根据工具执行结果，继续执行任务或总结回答。"
            iteration += 1
        else:
            # 模型直接回答
            yield {
                'type': 'assistant',
                'content': output
            }
            break
    
    # 发送完成事件
    yield {
        'type': 'done',
        'iterations': iteration
    }


# ── 启动服务 ──
if __name__ == '__main__':
    print("=" * 60)
    print("LLM-Tools Chat UI - 类似 OpenClaw 的界面")
    print("=" * 60)
    print(f"服务器: {LLAMA_SERVER_URL}")
    print(f"模型: {MODEL_NAME}")
    print("访问地址: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='localhost', port=5000, debug=False, threaded=True)