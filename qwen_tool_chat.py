#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen3.5-9B 工具调用 - 简易交互式界面
可以在命令行中直接与 Qwen 对话，自动执行工具调用

使用方法：
1. 启动 llama.cpp-server：llama-server -m Qwen3.5-9B-Q4_K_M.gguf --port 1235
2. 运行此脚本：python qwen_tool_chat.py
3. 在命令行中输入指令，Qwen 会自动执行工具调用
"""

import requests
import json
import os
import sys
from typing import Dict, Any, Optional

# ── 配置 ──
LLAMA_SERVER_URL = "http://127.0.0.1:1235"
MODEL_NAME = "Qwen3.5-9B-Q4_K_M.gguf"

# ── 系统提示词 ──
SYSTEM_PROMPT = """
你是一个智能助手，可以使用以下工具：

## 可用工具
1. read_file(path): 读取文件内容
2. write_file(path, content): 写入文件（UTF-8 编码）
3. list_files(dir): 列出目录文件
4. count_lines(path): 统计文件行数
5. search_in_file(path, keyword): 在文件中搜索关键词

## 输出格式要求
如果需要使用工具，请严格按照以下 JSON 格式输出（不要添加任何额外文字）：
{"tool": "工具名", "args": {"参数名": "参数值"}}

例如：
{"tool": "read_file", "args": {"path": "E:/csi10/live_runner.py"}}
{"tool": "write_file", "args": {"path": "E:/csi10/test.txt", "content": "Hello World"}}
{"tool": "list_files", "args": {"dir": "E:/csi10"}}

你可以多次调用工具，每次调用一个工具。
完成所有工具调用后，请总结结果回答用户问题。

## 重要提醒
- 工具调用必须严格按照 JSON 格式输出
- 不要添加任何解释性文字
- JSON 必须是有效的格式（双引号、正确缩进）
"""

# ── 工具实现 ──
def execute_tool(tool_call: Dict[str, Any]) -> str:
    """执行工具调用"""
    tool_name = tool_call.get("tool")
    args = tool_call.get("args", {})
    
    try:
        if tool_name == "read_file":
            path = args.get("path")
            if not os.path.exists(path):
                return f"❌ 文件不存在: {path}"
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return content[:2000] if len(content) > 2000 else content
        
        elif tool_name == "write_file":
            path = args.get("path")
            content = args.get("content", "")
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"✅ 写入成功: {path} ({len(content)} 字符)"
        
        elif tool_name == "list_files":
            dir = args.get("dir")
            if not os.path.exists(dir):
                return f"❌ 目录不存在: {dir}"
            files = [f for f in os.listdir(dir) if f.endswith('.py')]
            return "\n".join(files[:20])
        
        elif tool_name == "count_lines":
            path = args.get("path")
            if not os.path.exists(path):
                return f"❌ 文件不存在: {path}"
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            return f"✅ 文件 {path} 共有 {len(lines)} 行"
        
        elif tool_name == "search_in_file":
            path = args.get("path")
            keyword = args.get("keyword", "")
            if not os.path.exists(path):
                return f"❌ 文件不存在: {path}"
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            matches = [line for line in content.split('\n') if keyword in line]
            return f"✅ 找到 {len(matches)} 行包含 '{keyword}'\n" + "\n".join(matches[:10])
        
        else:
            return f"❌ 未知工具: {tool_name}"
    
    except Exception as e:
        return f"❌ 执行失败: {str(e)}"


# ── LLaMA API 调用 ──
def call_llama(user_input: str, conversation_history: list = []) -> str:
    """调用 llama.cpp-server OpenAI 兼容 API"""
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_input})
        
        response = requests.post(
            f"{LLAMA_SERVER_URL}/v1/chat/completions",
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500,
            },
            timeout=60
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ API 调用失败: {e}"


def parse_tool_call(text: str) -> Optional[Dict[str, Any]]:
    """解析工具调用 JSON"""
    try:
        return json.loads(text.strip())
    except:
        return None


# ── 主交互循环 ──
def interactive_chat():
    """交互式聊天循环"""
    print("\n" + "=" * 60)
    print("Qwen3.5-9B 工具调用交互式界面")
    print("=" * 60)
    print(f"服务器: {LLAMA_SERVER_URL}")
    print(f"模型: {MODEL_NAME}")
    print("=" * 60)
    print("可用工具: read_file, write_file, list_files, count_lines, search_in_file")
    print("输入 'quit' 或 'exit' 退出")
    print("=" * 60 + "\n")
    
    conversation_history = []
    max_iterations = 10  # 每次最多 10 步工具调用
    
    while True:
        try:
            # 读取用户输入
            user_input = input("你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n再见！")
                break
            
            # 工具调用循环
            iteration = 0
            current_input = user_input
            
            while iteration < max_iterations:
                print(f"\n[步骤 {iteration + 1}]")
                
                # 调用模型
                output = call_llama(current_input, conversation_history)
                print(f"Qwen: {output[:150]}...")
                
                # 解析工具调用
                tool_call = parse_tool_call(output)
                
                if tool_call:
                    # 执行工具
                    print(f"🔧 工具调用: {tool_call}")
                    result = execute_tool(tool_call)
                    print(f"📤 工具结果: {result[:100]}...")
                    
                    # 将结果添加到对话历史
                    conversation_history.append({"role": "user", "content": current_input})
                    conversation_history.append({"role": "assistant", "content": output})
                    conversation_history.append({"role": "user", "content": f"工具执行结果: {result}\n请继续或总结回答。"})
                    
                    # 更新输入，让模型决定下一步
                    current_input = "根据工具执行结果，继续执行任务或总结回答。"
                    iteration += 1
                else:
                    # 模型直接回答，结束循环
                    print(f"\n✅ 任务完成！")
                    print(f"Qwen: {output}")
                    
                    # 更新对话历史
                    conversation_history.append({"role": "user", "content": user_input})
                    conversation_history.append({"role": "assistant", "content": output})
                    break
            
            if iteration >= max_iterations:
                print(f"\n⚠️ 达到最大迭代次数 ({max_iterations})，任务可能未完全完成")
            
        except KeyboardInterrupt:
            print("\n\n中断退出")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            continue


# ── 单次任务执行 ──
def run_single_task(task: str, max_iterations: int = 10):
    """执行单次任务（不进入交互模式）"""
    print(f"\n任务: {task}")
    
    conversation_history = []
    current_input = task
    iteration = 0
    
    while iteration < max_iterations:
        print(f"\n[步骤 {iteration + 1}]")
        
        # 调用模型
        output = call_llama(current_input, conversation_history)
        print(f"Qwen: {output[:150]}...")
        
        # 解析工具调用
        tool_call = parse_tool_call(output)
        
        if tool_call:
            # 执行工具
            print(f"🔧 工具调用: {tool_call}")
            result = execute_tool(tool_call)
            print(f"📤 工具结果: {result[:100]}...")
            
            # 更新对话历史
            conversation_history.append({"role": "user", "content": current_input})
            conversation_history.append({"role": "assistant", "content": output})
            conversation_history.append({"role": "user", "content": f"工具执行结果: {result}\n请继续或总结回答。"})
            
            current_input = "根据工具执行结果，继续执行任务或总结回答。"
            iteration += 1
        else:
            # 任务完成
            print(f"\n✅ 任务完成！")
            print(f"Qwen: {output}")
            break
    
    return output


# ── 主入口 ──
if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 单次任务执行
        task = " ".join(sys.argv[1:])
        run_single_task(task)
    else:
        # 交互式聊天
        interactive_chat()