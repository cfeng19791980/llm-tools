#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TriAttention校准文件生成脚本
运行llama-server.exe生成TriAttention校准文件
"""

import subprocess
import time
import os
import json
import requests
from pathlib import Path

# ============================================================
# 配置读取
# ============================================================

CONFIG_FILE = Path("E:/llm-tools/llm-tools-config.json")

def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print("❌ config.json不存在")
        return None

# ============================================================
# TriAttention校准文件生成
# ============================================================

def generate_triattention_calibration():
    """生成TriAttention校准文件"""
    
    print('='*60)
    print('TriAttention校准文件生成')
    print('='*60)
    
    # 加载配置
    config = load_config()
    
    if not config:
        return False
    
    print('\n配置信息:')
    print(f'  模型: {config["llm"]["model"]}')
    print(f'  模型路径: {config["paths"]["modelsDir"]}/{config["llm"]["modelSubpath"]}')
    print(f'  llama-server路径: {config["paths"]["llamaServerPath"]}')
    
    # 构建模型路径
    models_dir = Path(config['paths']['modelsDir'])
    model_subpath = config['llm']['modelSubpath']
    model_name = config['llm']['model']
    model_path = models_dir / model_subpath / model_name
    
    if not model_path.exists():
        print(f'\n❌ 模型文件不存在: {model_path}')
        return False
    
    print(f'\n✅ 模型文件存在: {model_path}')
    
    # 构建llama-server路径
    llama_server_path = Path(config['paths']['llamaServerPath'])
    
    if not llama_server_path.exists():
        print(f'\n❌ llama-server.exe不存在: {llama_server_path}')
        return False
    
    print(f'\n✅ llama-server.exe存在: {llama_server_path}')
    
    # TriAttention校准文件路径
    calibration_file = Path("E:/llm-tools/Qwen3.5-9B-Q4_K_M.triattention")
    
    print(f'\n校准文件路径: {calibration_file}')
    
    # 构建启动命令（包含TriAttention参数）
    launch_params = config['llm']['launchParams']
    
    cmd = [
        str(llama_server_path),
        "-m", str(model_path),
        "--host", "127.0.0.1",
        "--port", str(config['llm']['port']),
        "-t", str(launch_params['threads']),
        "-ngl", str(launch_params['ngl']),
        "-c", str(launch_params['ctx']),
        "--temp", str(config['llm']['temperature']['toolJudge']),
        "-s", str(launch_params['seed']),
        "--flash-attn", "on" if launch_params['flashAttn'] else "off",
        "--reasoning", "off" if not launch_params['reasoning'] else "on"
    ]
    
    # 添加cache量化参数
    if launch_params['cacheQuantization']:
        cmd.extend(["-ctk", launch_params['cacheQuantization']])
        cmd.extend(["-ctv", launch_params['cacheQuantization']])
    
    # 添加--no-warmup
    if launch_params['noWarmup']:
        cmd.append("--no-warmup")
    
    # 添加--context-shift
    if launch_params['contextShift']:
        cmd.append("--context-shift")
    
    # ✅ 添加TriAttention参数（生成校准文件）
    cmd.extend(["--triattention-stats", str(calibration_file)])
    cmd.extend(["--triattention-budget", "4096"])  # 最大KV tokens保留
    cmd.extend(["--triattention-window", "256"])   # 最近token保护窗口
    cmd.append("--triattention-log")               # 日志修剪事件
    
    print('\n启动命令:')
    print(' '.join(cmd))
    
    # 启动llama-server（生成校准文件）
    print('\n' + '='*60)
    print('启动llama-server生成校准文件...')
    print('='*60)
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    print(f'\n✅ llama-server已启动 (PID {proc.pid})')
    
    # 等待启动
    print('\n等待llama-server启动（15秒）...')
    time.sleep(15)
    
    # 检查端口
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', config['llm']['port']))
    sock.close()
    
    if result == 0:
        print(f'\n✅ llama-server运行正常（端口 {config["llm"]["port"]}）')
    else:
        print(f'\n❌ llama-server启动失败')
        return False
    
    # 发送一些测试请求（触发TriAttention校准）
    print('\n发送测试请求触发TriAttention校准...')
    
    test_messages = [
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
    
    try:
        response = requests.post(
            f'http://127.0.0.1:{config["llm"]["port"]}/v1/chat/completions',
            json={
                'model': config['llm']['model'],
                'messages': test_messages,
                'max_tokens': 100
            },
            timeout=30
        )
        
        print(f'\n✅ 测试请求成功')
        
    except Exception as e:
        print(f'\n⚠️ 测试请求失败: {e}')
    
    # 等待校准文件生成
    print('\n等待校准文件生成（30秒）...')
    time.sleep(30)
    
    # 检查校准文件是否生成
    if calibration_file.exists():
        print(f'\n✅✅✅ 校准文件生成成功: {calibration_file}')
        print(f'文件大小: {calibration_file.stat().st_size} bytes')
        
        # 关闭llama-server
        proc.terminate()
        
        print(f'\n✅ llama-server已关闭')
        
        return True
    
    else:
        print(f'\n❌ 校准文件未生成')
        
        # 关闭llama-server
        proc.terminate()
        
        return False

# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    success = generate_triattention_calibration()
    
    if success:
        print('\n' + '='*60)
        print('✅✅✅ TriAttention校准文件生成完成！')
        print('='*60)
        print('\n下一步:')
        print('  1. 校准文件已生成: E:/llm-tools/Qwen3.5-9B-Q4_K_M.triattention')
        print('  2. config.json已更新（TriAttention参数）')
        print('  3. 启动_LLM-Tools.bat已修改（自动启动llama-server）')
        print('  4. 双击启动_LLM-Tools.bat启动完整服务')
    
    else:
        print('\n' + '='*60)
        print('❌ TriAttention校准文件生成失败')
        print('='*60)
        print('\n可能原因:')
        print('  1. 模型文件不存在')
        print('  2. llama-server.exe启动失败')
        print('  3. 端口冲突')
        print('\n请检查config.json配置是否正确')