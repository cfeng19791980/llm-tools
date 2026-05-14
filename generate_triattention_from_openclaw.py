#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用OpenClaw对话历史生成TriAttention校准文件
"""

import subprocess
import time
import os
import json
import requests
from pathlib import Path

print('使用OpenClaw对话历史生成TriAttention校准文件...')
print('='*60)

# ============================================================
# 配置读取
# ============================================================

CONFIG_FILE = Path("E:/llm-tools/llm-tools-config.json")

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

print(f'\n配置信息:')
print(f'  模型: {config["llm"]["model"]}')
print(f'  端口: {config["llm"]["port"]}')

# ============================================================
# 提取OpenClaw对话历史
# ============================================================

print('\n' + '='*60)
print('\n提取OpenClaw对话历史...')

trajectory_file = 'C:\\Users\\10341\\.openclaw\\agents\\main\\sessions\\3ba4cc67-3110-4406-8352-6f9f90de7808.trajectory.jsonl'

messages = []

with open(trajectory_file, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            
            trace_type = data.get('type', '')
            
            if 'prompt' in trace_type or 'model' in trace_type:
                trace_data = data.get('data', {})
                
                # 提取content字段
                if 'content' in trace_data:
                    content = trace_data['content']
                    
                    # 如果content是数组（包含text）
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and 'text' in item:
                                text = item['text']
                                
                                # 过滤有意义的内容（长度>50）
                                if len(text) > 50:
                                    messages.append({
                                        'role': 'user' if 'prompt' in trace_type else 'assistant',
                                        'content': text[:500]  # 截取前500字符
                                    })
        
        except:
            pass

print(f'\n✅ 提取对话历史: {len(messages)}条')

# 统计
role_count = {}

for msg in messages:
    role = msg['role']
    
    if role in role_count:
        role_count[role] += 1
    
    else:
        role_count[role] = 1

print(f'消息角色: {role_count}')

# ============================================================
# 启动llama-server
# ============================================================

print('\n' + '='*60)
print('\n启动llama-server（带TriAttention参数）...')

models_dir = Path(config['paths']['modelsDir'])
model_subpath = config['llm']['modelSubpath']
model_name = config['llm']['model']
model_path = models_dir / model_subpath / model_name

llama_server_path = Path(config['paths']['llamaServerPath'])
calibration_file = Path("E:/llm-tools/Qwen3.5-9B-Q4_K_M.triattention")

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
    "--reasoning", "off",
    "-ctk", launch_params['cacheQuantization'],
    "-ctv", launch_params['cacheQuantization'],
    "--no-warmup",
    "--context-shift",
    "--triattention-stats", str(calibration_file),
    "--triattention-budget", "4096",
    "--triattention-window", "256",
    "--triattention-log"
]

proc = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    creationflags=subprocess.CREATE_NEW_CONSOLE
)

print(f'\n✅ llama-server已启动 (PID {proc.pid})')

time.sleep(20)

# ============================================================
# 发送OpenClaw对话历史（分批）
# ============================================================

print('\n' + '='*60)
print('\n发送OpenClaw对话历史触发TriAttention校准...')

# 分批发送（每批10条消息）
batch_size = 10
total_batches = min(50, len(messages) // batch_size)  # 最多发送50批

print(f'\n总批次: {total_batches}批（每批{batch_size}条消息）')

port = config['llm']['port']
model = config['llm']['model']

for batch_idx in range(total_batches):
    start_idx = batch_idx * batch_size
    end_idx = start_idx + batch_size
    
    batch_messages = messages[start_idx:end_idx]
    
    if not batch_messages:
        break
    
    print(f'\n发送批次{batch_idx+1}/{total_batches}...')
    
    try:
        response = requests.post(
            f'http://127.0.0.1:{port}/v1/chat/completions',
            json={
                'model': model,
                'messages': batch_messages,
                'max_tokens': 100
            },
            timeout=60
        )
        
        print(f'✅ 批次{batch_idx+1}成功')
        
    except Exception as e:
        print(f'⚠️ 批次{batch_idx+1}失败: {e}')
    
    # 每批间隔2秒
    time.sleep(2)

print('\n✅✅✅ OpenClaw对话历史发送完成')

# ============================================================
# 等待校准文件生成
# ============================================================

print('\n' + '='*60)
print('\n等待校准文件生成（60秒）...')

time.sleep(60)

if calibration_file.exists():
    file_size = calibration_file.stat().st_size
    
    print(f'\n✅✅✅✅✅✅✅✅✅✅✅✌✅ TriAttention校准文件生成成功！')
    print(f'文件路径: {calibration_file}')
    print(f'文件大小: {file_size} bytes')
    
    proc.terminate()
    
    print('\n下一步:')
    print('  1. config.json enabled=true启用TriAttention')
    print('  2. 重启llama-server验证TriAttention生效')

else:
    print(f'\n⚠️ 校准文件未生成')
    
    proc.terminate()

print('\n✅✅✅✅✅✅✅✅✅✅✅✌✅ 完成！')