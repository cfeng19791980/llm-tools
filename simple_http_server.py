# -*- coding: utf-8 -*-
"""
simple_http_server.py - Flask静态文件服务器（替代Python http.server）
解决缓存问题，强制加载最新版本文件
"""

from flask import Flask, send_file
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # 启用CORS

BASE_DIR = 'E:/llm-tools'

@app.route('/')
def index():
    """返回index.html"""
    return send_file(os.path.join(BASE_DIR, 'index.html'))

@app.route('/index.html')
def index_html():
    """返回index.html"""
    return send_file(os.path.join(BASE_DIR, 'index.html'))

@app.route('/<path:filename>')
def static_files(filename):
    """返回静态文件（强制不缓存）"""
    file_path = os.path.join(BASE_DIR, filename)
    
    if os.path.exists(file_path):
        response = send_file(file_path)
        # 强制不缓存（每次都加载最新版本）
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    else:
        return f"File not found: {filename}", 404

if __name__ == '__main__':
    print("=" * 70)
    print("Flask静态文件服务器启动")
    print("端口: 8082")
    print("目录: E:/llm-tools")
    print("CORS: 已启用")
    print("=" * 70)
    
    app.run(host='127.0.0.1', port=8082, debug=False)