#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stream_api.py - 流式输出API
实时返回LLM输出，提升用户体验
"""

import requests
import json
from flask import Response, stream_with_context


class StreamAPI:
    """流式输出API"""
    
    def __init__(self, backend_api, llama_server):
        self.backend_api = backend_api
        self.llama_server = llama_server
    
    def stream_chat(self, user_input, port=1235, max_tokens=1000, temperature=0.7):
        """
        流式聊天（实时返回LLM输出）
        
        Args:
            user_input: 用户输入
            port: llama-server端口
            max_tokens: 最大token数
            temperature: 温度
            
        Returns:
            Flask Response（流式）
        """
        
        def generate():
            """生成器函数（流式输出）"""
            
            # 调用llama-server流式API
            response = requests.post(
                f'http://127.0.0.1:{port}/v1/chat/completions',
                json={
                    'model': 'Qwen3.5-9B-Q4_K_M.gguf',
                    'messages': [
                        {'role': 'user', 'content': user_input}
                    ],
                    'max_tokens': max_tokens,
                    'temperature': temperature,
                    'stream': True  # 启用流式输出
                },
                stream=True,  # requests启用stream
                timeout=60
            )
            
            if response.status_code != 200:
                yield f'data: {json.dumps({"error": "LLM request failed"})}\n\n'
                return
            
            # 流式接收llama-server输出
            full_content = ''
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    
                    if line_text.startswith('data: '):
                        data_str = line_text[6:]
                        
                        if data_str.strip() == '[DONE]':
                            # 流式结束
                            yield f'data: {json.dumps({"done": True, "full_content": full_content})}\n\n'
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            content = data['choices'][0]['delta'].get('content', '')
                            
                            if content:
                                full_content += content
                                
                                # 实时返回chunk
                                yield f'data: {json.dumps({"content": content})}\n\n'
                                
                        except json.JSONDecodeError:
                            pass
        
        # 返回Flask流式响应
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream'
        )


def register_stream_api(app, stream_api):
    """
    注册流式API端点到Flask
    
    Args:
        app: Flask app
        stream_api: StreamAPI实例
    """
    
    @app.route('/api/stream_chat', methods=['POST'])
    def api_stream_chat():
        """流式聊天端点"""
        from flask import request
        
        data = request.json
        user_input = data.get('input', '')
        port = data.get('port', 1235)
        
        return stream_api.stream_chat(user_input, port)