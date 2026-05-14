#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM-Tools Model Manager Backend
提供模型启动/停止、推理服务管理、工具调用、配置保存/载入功能
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import json
import psutil
import time
import socket
import requests
from pathlib import Path
from datetime import datetime

# =====================================================================
# Agent v2.0 核心架构：决策循环与状态管理
# =====================================================================

class AgentState:
    """Agent状态定义"""
    WAITING_FOR_USER_INPUT = "WAITING_FOR_USER_INPUT"
    EXECUTING_TOOL = "EXECUTING_TOOL"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"
    TASK_COMPLETED = "TASK_COMPLETED"
    ERROR_HANDLING = "ERROR_HANDLING"

class TaskContext:
    """任务上下文管理"""
    def __init__(self):
        self.state = AgentState.WAITING_FOR_USER_INPUT
        self.current_tool = None
        self.tool_result = None
        self.verification_needed = False
        self.error_count = 0
        self.max_retries = 3
        self.plan = None  # 执行计划
        self.user_intent = None  # 用户意图
    
    def update_state(self, new_state):
        """更新状态"""
        self.state = new_state
        # 状态持久化（可选：保存到文件）
        # self.save_to_session()
    
    def set_tool(self, tool_name, args):
        """设置当前工具"""
        self.current_tool = tool_name
        self.update_state(AgentState.EXECUTING_TOOL)
    
    def set_result(self, result):
        """设置工具结果"""
        self.tool_result = result
        self.update_state(AgentState.NEEDS_VERIFICATION)
    
    def increment_error(self):
        """增加错误计数"""
        self.error_count += 1
        if self.error_count >= self.max_retries:
            self.update_state(AgentState.ERROR_HANDLING)
    
    def reset(self):
        """重置任务上下文"""
        self.state = AgentState.WAITING_FOR_USER_INPUT
        self.current_tool = None
        self.tool_result = None
        self.verification_needed = False
        self.error_count = 0
        self.plan = None

class ErrorMapper:
    """错误友好提示映射"""
    ERROR_MESSAGES = {
        'ConnectionError': '抱歉，网络连接失败，请稍后重试',
        'TimeoutError': '抱歉，请求超时，请检查网络或减少查询复杂度',
        'FileNotFoundError': '抱歉，文件不存在，请检查路径是否正确',
        'PermissionError': '抱歉，没有权限访问该文件，请检查权限设置',
        'KeyError': '抱歉，缺少必要参数，请检查输入是否完整',
        'ValueError': '抱歉，参数值不正确，请检查输入格式',
        'JSONDecodeError': '抱歉，数据格式错误，请检查数据是否有效'
    }
    
    def get_friendly_error(self, error_type, original_error=None):
        """获取友好错误提示"""
        friendly_msg = self.ERROR_MESSAGES.get(error_type)
        if friendly_msg:
            if original_error:
                return f"{friendly_msg}。详细信息：{original_error}"
            return friendly_msg
        return f"抱歉，执行失败：{error_type}"

# 全局任务上下文实例
task_context = TaskContext()

# =====================================================================

# ✅ v3.0改进：集中配置管理（借鉴openclaw.json）
# 读取llm-tools-config.json配置文件
CONFIG_FILE = Path("E:/llm-tools/llm-tools-config.json")

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

app = Flask(__name__)

# CORS配置（从config.json读取）
if CONFIG['backend']['cors']:
    CORS(app)  # 启用CORS，允许所有来源访问

# 配置（从config.json读取，不再硬编码）
CONFIG_DIR = Path(CONFIG['paths']['configDir'])
LLAMA_SERVER_PATH = Path("E:/llama_bin/llama-server.exe")  # 固定路径
PID_FILE = Path(CONFIG['paths']['pidFile'])
MODELS_DIR = Path(CONFIG['paths']['modelsDir'])

# 确保配置目录存在
CONFIG_DIR.mkdir(exist_ok=True)
# ============================================================
# 进程管理
# ============================================================

def save_pid(pid, model_name, port):
    """保存模型进程信息"""
    with open(PID_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'pid': pid,
            'model': model_name,
            'port': port,
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }, f, ensure_ascii=False, indent=2)

def load_pid():
    """加载模型进程信息"""
    if PID_FILE.exists():
        with open(PID_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def is_process_running(pid):
    """检查进程是否在运行"""
    try:
        proc = psutil.Process(pid)
        return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def get_model_status():
    """获取模型运行状态"""
    pid_info = load_pid()
    if pid_info and is_process_running(pid_info['pid']):
        return {
            'running': True,
            'pid': pid_info['pid'],
            'model': pid_info['model'],
            'port': pid_info['port'],
            'start_time': pid_info['start_time']
        }
    return {'running': False}

# ============================================================
# API 端点
# ============================================================


@app.route('/')
def index():
    """提供前端页面""" 
    return send_file('index.html')


@app.route('/api/status', methods=['GET'])
def api_status():
    """获取模型状态"""
    status = get_model_status()
    return jsonify(status)

@app.route('/api/start', methods=['POST'])
def api_start():
    """启动模型"""
    try:
        data = request.json
        
        # ✅ v3.1改进：从config.json读取启动参数（集中配置管理）
        model_name = data.get('model', CONFIG['llm']['model'])
        model_subpath = CONFIG['llm']['modelSubpath']  # 模型子路径
        port = data.get('port', CONFIG['llm']['port'])
        
        # 从config.json读取launchParams
        launch_params = CONFIG['llm']['launchParams']
        threads = data.get('threads', launch_params['threads'])
        ngl = data.get('ngl', launch_params['ngl'])
        ctx = data.get('ctx', launch_params['ctx'])
        temp = data.get('temp', launch_params['temperature']['toolJudge'] if 'temperature' in launch_params else 0.05)
        seed = data.get('seed', launch_params['seed'])
        flash_attn = data.get('flash_attn', launch_params['flashAttn'])
        
        # ✅ v3.1改进：防止重复启动（检查llama-server进程）
        # 检查是否已有模型运行（通过PID文件）
        status = get_model_status()
        if status['running']:
            return jsonify({
                'success': False,
                'message': f"Model already running (PID: {status['pid']}, Port: {status['port']})"
            })
        
        # 检查端口是否被占用（防止其他程序启动llama-server）
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port_result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if port_result == 0:
            return jsonify({
                'success': False,
                'message': f"Port {port} already in use (llama-server may be running externally)"
            })
        
        # ✅ v3.1改进：修正模型路径（使用paths.modelsDir + modelSubpath）
        models_dir = Path(CONFIG['paths']['modelsDir'])
        model_path = models_dir / model_subpath / model_name
        
        if not model_path.exists():
            return jsonify({
                'success': False,
                'message': f"Model not found: {model_path}"
            })
        
        # ✅ v3.1改进：添加cache量化、noWarmup、context-shift参数
        llama_server_path = Path(CONFIG['paths']['llamaServerPath'])
        
        cmd = [
            str(llama_server_path),
            "-m", str(model_path),
            "--host", "127.0.0.1",
            "--port", str(port),
            "-t", str(threads),
            "-ngl", str(ngl),
            "-c", str(ctx),
            "--temp", str(temp),
            "-s", str(seed),
            "--flash-attn", "on" if flash_attn else "off",
            "--reasoning", "off" if not launch_params['reasoning'] else "on"
        ]
        
        # ✅ 添加cache量化参数（-ctk q8_0 -ctv q8_0）
        if launch_params['cacheQuantization']:
            cmd.extend(["-ctk", launch_params['cacheQuantization']])
            cmd.extend(["-ctv", launch_params['cacheQuantization']])
        
        # ✅ 添加--no-warmup（加快启动速度）
        if launch_params['noWarmup']:
            cmd.append("--no-warmup")
        
        # ✅ 添加--context-shift（支持超长文本）
        if launch_params['contextShift']:
            cmd.append("--context-shift")
        
        # ✅ v3.2改进：添加TriAttention参数（内存优化 + 推理加速）
        if 'triattention' in launch_params and launch_params['triattention']['enabled']:
            triattention_params = launch_params['triattention']
            
            # 校准文件（必需）
            if triattention_params['statsFile']:
                cmd.extend(["--triattention-stats", triattention_params['statsFile']])
            
            # KV tokens保留数量
            if triattention_params['budget']:
                cmd.extend(["--triattention-budget", str(triattention_params['budget'])])
            
            # 最近token保护窗口
            if triattention_params['window']:
                cmd.extend(["--triattention-window", str(triattention_params['window'])])
            
            # 触发模式
            if triattention_params['trigger']:
                cmd.extend(["--triattention-trigger", triattention_params['trigger']])
            
            # 日志修剪事件
            if triattention_params['log']:
                cmd.append("--triattention-log")
        
        # 启动进程
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        
        # 保存 PID
        save_pid(proc.pid, model_name, port)
        
        # 等待启动（检查端口）
        time.sleep(2)
        
        # 验证是否成功
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            return jsonify({
                'success': True,
                'message': f"Model started successfully",
                'pid': proc.pid,
                'port': port
            })
        else:
            return jsonify({
                'success': False,
                'message': f"Model start failed (port {port} not responding)"
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """停止模型"""
    try:
        status = get_model_status()
        
        if not status['running']:
            return jsonify({
                'success': False,
                'message': "No model running"
            })
        
        pid = status['pid']
        
        # 停止进程
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            time.sleep(2)
            
            # 如果还在运行，强制结束
            if proc.is_running():
                proc.kill()
            
            # 删除 PID 文件
            PID_FILE.unlink(missing_ok=True)
            
            return jsonify({
                'success': True,
                'message': f"Model stopped (PID: {pid})"
            })
            
        except psutil.NoSuchProcess:
            PID_FILE.unlink(missing_ok=True)
            return jsonify({
                'success': True,
                'message': "Process already terminated"
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/save_config', methods=['POST'])
def api_save_config():
    """保存配置为 bat 文件"""
    try:
        data = request.json
        
        config_name = data.get('name', 'default')
        model = data.get('model', CONFIG['llm']['model'])  # ✅ 从config.json读取
        port = data.get('port', 1235)
        ngl = data.get('ngl', 99)
        temp = data.get('temp', 0.05)
        ctx = data.get('ctx', 32000)
        threads = data.get('threads', 8)
        seed = data.get('seed', 42)
        flash_attn = data.get('flash_attn', True)
        
        # 构建 bat 内容
        bat_content = f"""@echo off
title {model} - Port {port}

echo ============================================================
echo Model: {model}
echo Port: {port}
echo GPU Layers: {ngl}
echo Context: {ctx}
echo Temperature: {temp}
echo ============================================================
echo.

:: Start llama-server
"{LLAMA_SERVER_PATH}" ^
  -m "E:/models/{model}" ^
  --host 127.0.0.1 ^
  --port {port} ^
  -t {threads} ^
  -ngl {ngl} ^
  -c {ctx} ^
  --temp {temp} ^
  -s {seed} ^
  --flash-attn {"on" if flash_attn else "off"} ^
  --reasoning off

pause
"""
        
        # 保存 bat 文件
        bat_file = CONFIG_DIR / f"{config_name}.bat"
        with open(bat_file, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        return jsonify({
            'success': True,
            'message': f"Config saved: {bat_file}",
            'path': str(bat_file)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/load_config', methods=['POST'])
def api_load_config():
    """载入配置"""
    try:
        data = request.json
        config_name = data.get('name', 'default')
        
        bat_file = CONFIG_DIR / f"{config_name}.bat"
        
        if not bat_file.exists():
            return jsonify({
                'success': False,
                'message': f"Config not found: {config_name}"
            })
        
        # 解析 bat 文件，提取参数（简单解析）
        with open(bat_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 返回配置内容（前端需要进一步解析）
        return jsonify({
            'success': True,
            'message': f"Config loaded: {config_name}",
            'content': content,
            'path': str(bat_file)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/list_configs', methods=['GET'])
def api_list_configs():
    """列出所有配置"""
    try:
        configs = []
        for bat_file in CONFIG_DIR.glob("*.bat"):
            configs.append({
                'name': bat_file.stem,
                'path': str(bat_file),
                'mtime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(bat_file.stat().st_mtime))
            })
        return jsonify({
            'success': True,
            'configs': configs
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/models', methods=['GET'])
def api_models():
    """列出可用模型"""
    try:
        models = []
        
        # 递归搜索所有 GGUF 文件
        for gguf_file in MODELS_DIR.rglob("*.gguf"):
            # 过滤：只包含主要模型（排除 mmproj、bge等）
            if 'mmproj' in gguf_file.name.lower() or 'bge' in gguf_file.name.lower():
                continue
            
            size_mb = gguf_file.stat().st_size / (1024 * 1024)
            models.append({
                'name': gguf_file.name,
                'path': str(gguf_file),
                'size': f"{size_mb:.1f} MB",
                'relative_path': str(gguf_file.relative_to(MODELS_DIR))
            })
        
        # 按大小排序
        models.sort(key=lambda x: float(x['size'].split()[0]), reverse=True)
        
        # 保存到models_list.json（前端直接读取）
        models_file = Path("E:/llm-tools/models_list.json")
        with open(models_file, 'w', encoding='utf-8') as f:
            json.dump({
                'success': True,
                'models': models,
                'total': len(models)
            }, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'models': models,
            'total': len(models)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# ============================================================
# 推理服务管理 (Port 1235)
# ============================================================
# 推理服务管理 (Port 1235)
# ============================================================

def check_port_status(port):
    """Check if a port is responding"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

def get_inference_service_status(port=1235):
    """Get inference service status"""
    status = check_port_status(port)
    
    if status:
        # Check if it's llama-server
        try:
            response = requests.get(f'http://127.0.0.1:{port}/v1/models', timeout=3)
            if response.status_code == 200:
                models = response.json()
                model_list = [m['id'] for m in models.get('data', [])]
                return {
                    'running': True,
                    'port': port,
                    'type': 'llama-server',
                    'models': model_list
                }
        except:
            pass
    
    return {'running': False, 'port': port}

@app.route('/api/inference_status', methods=['GET'])
def api_inference_status():
    """Get inference service status"""
    port = request.args.get('port', default=1235, type=int)
    status = get_inference_service_status(port)
    return jsonify(status)

@app.route('/api/test_inference', methods=['POST'])
def api_test_inference():
    """Test inference service"""
    try:
        port = request.json.get('port', 1235)
        test_input = request.json.get('input', 'Hello')
        
        response = requests.post(
            f'http://127.0.0.1:{port}/v1/chat/completions',
            json={
                'model': 'test',
                'messages': [{'role': 'user', 'content': test_input}],
                'max_tokens': 50
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True,
                'message': 'Inference test successful',
                'response': result
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Inference test failed: HTTP {response.status_code}'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================================
# 工具调用功能
# ============================================================

# Import tool registry
try:
    import sys
    sys.path.insert(0, 'E:/llm-tools')
    from tool_registry import ToolRegistry
    tool_registry = ToolRegistry()
    TOOLS_AVAILABLE = True
except Exception as e:
    TOOLS_AVAILABLE = False
    print(f"Tool registry not available: {e}")

@app.route('/api/list_tools', methods=['GET'])
def api_list_tools():
    """List available tools"""
    if not TOOLS_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Tool registry not available',
            'tools': []
        })
    
    try:
        # Get tools from registry
        tools = list(tool_registry.tools.keys())
        return jsonify({
            'success': True,
            'tools': tools,
            'total': len(tools)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'tools': []
        })

@app.route('/api/execute_tool', methods=['POST'])
def api_execute_tool():
    """Execute a tool"""
    if not TOOLS_AVAILABLE:
        return jsonify({'success': False, 'message': 'Tool registry not available'})
    
    try:
        data = request.json
        tool_name = data.get('tool')
        arguments = data.get('arguments', {})
        
        result = tool_registry.execute_tool(tool_name, arguments)
        
        return jsonify({'success': True, 'tool': tool_name, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/tool_chat', methods=['POST'])
@app.route('/api/tool_chat', methods=['POST'])
def api_tool_chat():
    """Tool-aware chat (借鉴OpenClaw设计)"""
    try:
        data = request.json
        user_input = data.get('input', '')
        port = data.get('port', 1235)
        
        # Step 1: Ask LLM to decide tool usage
        # 从文件读取system prompt（借鉴OpenClaw）
        try:
            identity_file = 'E:/llm-tools/IDENTITY.md'
            tools_file = 'E:/llm-tools/TOOLS.md'
            
            import os
            system_prompt_parts = []
            
            # 读取IDENTITY.md
            if os.path.exists(identity_file):
                with open(identity_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 提取关键部分（角色定义+行为规范）
                    lines = content.split('\n')
                    sections = [line for line in lines if not line.startswith('## 四')][:50]
                    system_prompt_parts.append('\n'.join(sections))
            
            # 读取TOOLS.md
            if os.path.exists(tools_file):
                with open(tools_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 提取工具列表
                    lines = content.split('\n')
                    sections = [line for line in lines if 'Example:' in line or '用途:' in line][:30]
                    system_prompt_parts.append('\n'.join(sections))
            
            if not system_prompt_parts:
                system_prompt = 'You are a tool-using assistant. Output JSON: {"tool": "tool_name", "args": {...}}'
            else:
                system_prompt = '\n\n'.join(system_prompt_parts)
                system_prompt = '\n\n'.join(system_prompt_parts)
                system_prompt += '''\n\n输出格式规则：\n1. 如果需要调用工具 → 输出JSON格式：\n   {"tool": "tool_name", "args": {"param": "value"}}\n   例如：{"tool": "web_search", "args": {"query": "福州天气"}}\n\n2. 如果不需要调用工具（例如打招呼、闲聊） → 直接回复文字：\n   你好！我是LLM-Tools助手...\n\n判断标准：\n- 用户提到“搜索”、“天气”、“文件操作”、“执行命令” → 调用工具\n- 用户只是打招呼、闲聊、提问简单问题 → 直接回复文字\n- 模糊场景（例如“今天星期几”） → 可选择调用get_time或直接回答\n'''
        
        except Exception as e:
            system_prompt = 'You are a tool-using assistant. Output JSON: {"tool": "tool_name", "args": {...}}'
        
        # Step 2: Call LLM
        response = requests.post(
            f'http://127.0.0.1:{port}/v1/chat/completions',
            json={
                'model': 'assistant',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_input}
                ],
                'max_tokens': 1000,  # 修复截断问题：从100提升到1000
                'temperature': 0.05
            },
            timeout=60  # 修复超时问题：从10秒提升到60秒
        )
        
        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'LLM request failed'})
        
        llm_output = response.json()['choices'][0]['message']['content']
        
        # Step 3: Parse as tool call
        try:
            tool_call = json.loads(llm_output.strip())
            tool_name = tool_call.get('tool')
            arguments = tool_call.get('args', {})
            
            if tool_name and TOOLS_AVAILABLE:
                tool_result = tool_registry.execute_tool(tool_name, arguments)
                
                return jsonify({
                    'success': True,
                    'tool_used': True,
                    'tool': tool_name,
                    'arguments': arguments,
                    'result': tool_result
                })
        except json.JSONDecodeError:
            pass
        
        # Return LLM output directly
        return jsonify({
            'success': True,
            'tool_used': False,
            'llm_output': llm_output
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================================
# 流式输出API
# ============================================================
# 流式输出API
# ============================================================

@app.route('/api/stream_chat', methods=['POST'])
def api_stream_chat():
    """流式聊天端点（实时输出）"""
    from flask import Response, stream_with_context
    
    data = request.json
    user_input = data.get('input', '')
    port = data.get('port', 1235)
    
    def generate():
        """生成器函数（流式输出）"""
        
        # 调用llama-server流式API
        response = requests.post(
            f'http://127.0.0.1:{port}/v1/chat/completions',
            json={
                'model': CONFIG['llm']['model'],  # ✅ 从config.json读取
                'messages': [
                    {'role': 'user', 'content': user_input}
                ],
                'max_tokens': 1000,
                'temperature': 0.7,
                'stream': True  # 启用流式输出
            },
            stream=True,
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
                        yield f'data: {json.dumps({"done": True, "full_content": full_content})}\n\n'
                        break
                    
                    try:
                        chunk_data = json.loads(data_str)
                        
                        content = chunk_data['choices'][0]['delta'].get('content', '')
                        
                        if content:
                            full_content += content
                            yield f'data: {json.dumps({"content": content})}\n\n'
                    except json.JSONDecodeError:
                        pass
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )


@app.route('/api/tool_chat_stream', methods=['POST'])
def api_tool_chat_stream():
    """智能流式聊天：工具调用 + 流式输出 + 对话历史"""
    from flask import Response, stream_with_context
    
    data = request.json
    messages = data.get('messages', [])  # 接收对话历史
    port = data.get('port', 1235)
    
    # 如果messages为空，使用旧方式（兼容）
    if not messages:
        user_input = data.get('input', '')
        if user_input:
            messages = [{'role': 'user', 'content': user_input}]
    
    def generate(messages):
        """生成器函数（流式输出）- 参数传递版本"""
        # 不使用nonlocal，直接使用参数messages
        
        # Step 1: 读取System Prompt
        # Step 1: 读取System Prompt
        # Step 1: 读取System Prompt
        try:
            identity_file = 'E:/llm-tools/IDENTITY.md'
            tools_file = 'E:/llm-tools/TOOLS.md'
            
            import os
            system_prompt_parts = []
            
            if os.path.exists(identity_file):
                with open(identity_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    sections = [line for line in lines if not line.startswith('## 四')][:50]
                    system_prompt_parts.append('\n'.join(sections))
            
            if os.path.exists(tools_file):
                with open(tools_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    system_prompt_parts.append(content)
            
            system_prompt = '\n\n'.join(system_prompt_parts)
            system_prompt += '\n\n输出格式规则：\n1. 如果需要调用工具 → 输出JSON格式：\n   {"tool": "tool_name", "args": {"param": "value"}}\n2. 如果不需要调用工具 → 直接回复文字\n'
        except Exception as e:
            system_prompt = 'You are a tool-using assistant. Output JSON for tool calls: {"tool": "tool_name", "args": {...}}'
        
        # Step 2: 构建完整messages（包含历史）
        # 限制历史长度（避免token过多）
        max_history = 10
        if len(messages) > max_history:
            # 只保留最近的max_history条消息
            messages = messages[-max_history:]
        
        # 添加system prompt
        full_messages = [{'role': 'system', 'content': system_prompt}] + messages
        
        # Step 3: 调用LLM判断是否需要工具（非流式）
        response = requests.post(
            f'http://127.0.0.1:{port}/v1/chat/completions',
            json={
                'model': 'assistant',
                'messages': full_messages,  # 携带历史
                'max_tokens': CONFIG['llm']['maxTokens']['toolJudge'],  # ✅ 从config.json读取
                'temperature': 0.05
            },
            timeout=30
        )
        
        if response.status_code != 200:
            yield f'data: {json.dumps({"error": "LLM判断失败"})}\n\n'
            return
        
        llm_output = response.json()['choices'][0]['message']['content']
        
        # Step 4: 判断是否工具调用
        try:
            tool_call = json.loads(llm_output.strip())
            tool_name = tool_call.get('tool')
            arguments = tool_call.get('args', {})
            
            if tool_name and TOOLS_AVAILABLE:
                # 执行工具
                yield f'data: {json.dumps({"tool_used": True, "tool": tool_name, "arguments": arguments})}\n\n'
                
                tool_result = tool_registry.execute_tool(tool_name, arguments)
                
                # 流式输出工具结果
                yield f'data: {json.dumps({"tool_result": tool_result})}\n\n'
                
                # ✅ Phase 2完整改进：Steering决策机制
                # 根据工具执行结果自动决策（不询问用户）
                
                steering_base = f"工具执行结果：\n{tool_result}\n\n请根据结果立即决策下一步行动："
                
                # 失败决策：自动修复，不询问用户
                if "❌" in tool_result or "失败" in tool_result or "错误" in tool_result or "Error" in tool_result:
                    steering_content = steering_base + """
如果工具执行失败，请立即采取修复行动（不询问用户）：
1. **识别错误类型** - 根据错误信息识别是超时、权限、参数还是路径错误
2. **自动切换工具** - 根据错误类型选择替代工具（Timeout→run_command）
3. **修复参数重试** - 如果参数错误，修正后立即重试
4. **直接决策执行** - 不询问用户，直接输出工具JSON

错误类型应对策略：
- TimeoutError/超时 → 切换run_command（绕过Python层）
- PermissionError/权限 → 切换run_command（系统命令）
- KeyError/缺少参数 → 补充参数后重试
- FileNotFoundError/不存在 → 检查路径或创建文件

决策输出格式（立即执行）：
- 切换工具：{"tool": "<alternative_tool>", "args": {"..."}}
                else:
                    # 成功决策：自动后续调用
                    # ✅ 修复：明确告诉LLM用户的原始任务是什么，必须继续执行
                    steering_content = steering_base + f"""

[WARNING] **用户的原始任务是**: {original_user_task}

当前工具调用只是第一步，**必须继续执行后续工具调用**（不询问用户）:

1. **检查任务完成度** - 当前工具结果是否已经完全解决了用户的原始任务?
2. **如果任务未完成** - 必须立即输出第二轮工具调用JSON（不回复文字）
3. **如果任务已完成** - 才可以回复文字（整合结果）

**强制规则**:
- [ERROR] 禁止在任务未完成时直接回复文字
- [OK] 必须在任务未完成时输出第二轮工具调用JSON
- [OK] 示例: 如果用户任务是"修复bug"，读取文件后必须继续输出"分析bug"和"修复bug"的工具调用JSON

**决策输出格式**（立即执行）:
- 后续工具调用: {"tool": "<next_tool>", "args": {...}}
- 任务完成才回复文字: 直接文字回复（不输出JSON）
"""

                    f'http://127.0.0.1:{port}/v1/chat/completions',
                    json={
                'model': CONFIG['llm']['model'],  # ✅ 从config.json读取
                'messages': tool_result_messages,
                'max_tokens': CONFIG['llm']['maxTokens']['finalReply'],  # ✅ 从config.json读取
                'temperature': CONFIG['llm']['temperature']['finalReply'],  # ✅ 从config.json读取
                'stream': True
                    },
                    stream=True,
                    timeout=60
                )
                
                if response_stream.status_code != 200:
                    yield f'data: {json.dumps({"error": "LLM流式请求失败"})}\n\n'
                    return
                
                # 流式输出LLM的最终回复
                for line in response_stream.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        
                        if line_text.startswith('data: '):
                            data_str = line_text[6:]
                            
                            if data_str.strip() == '[DONE]':
                                yield f'data: {json.dumps({"done": True})}\n\n'
                                break
                            
                            try:
                                chunk_data = json.loads(data_str)
                                content_chunk = chunk_data['choices'][0]['delta'].get('content', '')
                                
                                if content_chunk:
                                    yield f'data: {json.dumps({"content": content_chunk})}\n\n'
                            except json.JSONDecodeError:
                                pass
                
                return
        except json.JSONDecodeError:
            pass
        
        # Step 5: 不需要工具，流式输出LLM回复
        # Step 5: 不需要工具，流式输出LLM回复
        response_stream = requests.post(
            f'http://127.0.0.1:{port}/v1/chat/completions',
            json={
                'model': CONFIG['llm']['model'],  # ✅ 从config.json读取
                'messages': full_messages,  # 携带完整历史（修复对话历史问题）
                'max_tokens': CONFIG['llm']['maxTokens']['finalReply'],  # ✅ 从config.json读取
                'temperature': CONFIG['llm']['temperature']['finalReply'],  # ✅ 从config.json读取
                'stream': True
            },
            stream=True,
            timeout=60
        )
        
        if response_stream.status_code != 200:
            yield f'data: {json.dumps({"error": "LLM流式请求失败"})}\n\n'
            return
        
        # 流式接收llama-server输出
        for line in response_stream.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                
                if line_text.startswith('data: '):
                    data_str = line_text[6:]
                    
                    if data_str.strip() == '[DONE]':
                        yield f'data: {json.dumps({"done": True})}\n\n'
                        break
                    
                    try:
                        chunk_data = json.loads(data_str)
                        content = chunk_data['choices'][0]['delta'].get('content', '')
                        
                        if content:
                            yield f'data: {json.dumps({"content": content})}\n\n'
                    except json.JSONDecodeError:
                        pass
    
    return Response(
        stream_with_context(generate(messages)),
        mimetype='text/event-stream'
    )

# System Status
# ============================================================
# ============================================================
# System Status
# ============================================================
# System Status
# ============================================================

@app.route('/api/system_status', methods=['GET'])
def api_system_status():
    """Get overall system status"""
    model_status = get_model_status()
    inference_status = get_inference_service_status(1235)
    
    return jsonify({
        'model_manager': model_status,
        'inference_service': inference_status,
        'backend': {
            'running': True,
            'port': 5003,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    })

# ============================================================
# 启动服务
# ============================================================

# ============================================================
# 预设配置功能
# ============================================================

# Import presets
try:
    import sys
    sys.path.insert(0, 'E:/llm-tools')
    from presets import PRESETS, get_presets, get_preset
    PRESETS_AVAILABLE = True
except Exception as e:
    PRESETS_AVAILABLE = False
    print(f"Presets not available: {e}")

@app.route('/api/list_presets', methods=['GET'])
def api_list_presets():
    """列出预设配置"""
    if not PRESETS_AVAILABLE:
        return jsonify({'success': False, 'message': 'Presets not available', 'presets': []})
    
    presets_list = []
    for name, config in PRESETS.items():
        presets_list.append({'name': name, 'display_name': config['name'], 'description': config['description'], 'model': config['model']})
    
    print("=" * 60)
    if not PRESETS_AVAILABLE:
        return jsonify({'success': False, 'message': 'Presets not available'})
    
    preset = get_preset(preset_name)
    if preset:
        return jsonify({'success': True, 'preset': preset})
    else:
        return jsonify({'success': False, 'message': f'Preset {preset_name} not found'})

@app.route('/api/apply_preset', methods=['POST'])
def api_apply_preset():
    """应用预设配置"""
    try:
        data = request.json
        preset_name = data.get('preset', 'balance')
        
        if not PRESETS_AVAILABLE:
            return jsonify({'success': False, 'message': 'Presets not available'})
        
        preset = get_preset(preset_name)
        if preset:
            return jsonify({'success': True, 'preset': preset})
        else:
            return jsonify({'success': False, 'message': f'Preset {preset_name} not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================================
# 启动服务
# ============================================================


if __name__ == '__main__':
    print("=" * 60)
    print("LLM-Tools Model Manager Backend v2.0")
    print("=" * 60)
    print(f"Config directory: {CONFIG_DIR}")
    print(f"PID file: {PID_FILE}")
    print(f"LLama-server: {LLAMA_SERVER_PATH}")
    print(f"Models directory: {MODELS_DIR}")
    print(f"Tools available: {TOOLS_AVAILABLE}")
    print(f"Presets available: {PRESETS_AVAILABLE}")
    print("=" * 60)
    print("API Endpoints:")
    print("  - /api/status         : Model manager status")
    print("  - /api/start          : Start model")
    print("  - /api/stop           : Stop model")
    print("  - /api/save_config    : Save config to bat")
    print("  - /api/load_config    : Load config")
    print("  - /api/list_configs   : List configs")
    print("  - /api/models         : List available models")
    print("  - /api/inference_status : Inference service status")
    print("  - /api/test_inference : Test inference")
    print("  - /api/list_tools     : List tools")
    print("  - /api/execute_tool   : Execute tool")
    print("  - /api/tool_chat      : Tool-aware chat")
    print("  - /api/system_status  : Overall status")
    print("  - /api/list_presets   : List presets")
    print("  - /api/get_preset     : Get preset")
    print("  - /api/apply_preset   : Apply preset")
    print("=" * 60)
    print("  - /api/stream_chat   : Stream chat (实时输出)")
    print("=" * 60)
    
    # 启动时自动扫描模型（生成models_list.json）
    # 启动时自动扫描模型（生成models_list.json）
    print("正在扫描模型文件...")
    try:
        with app.app_context():
            api_models()
        print("[OK] models_list.json已生成")
    except Exception as e:
        print(f"[WARN] 模型扫描失败: {e}")
    print(f"Serving on: http://127.0.0.1:5003")
    print("=" * 60)
    print("=" * 60)
    print(f"Serving on: http://127.0.0.1:5003")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=5003, debug=False)