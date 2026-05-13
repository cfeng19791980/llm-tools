# ── 工具注册机制 ──
import os
import json
import subprocess
import sys
import re
import dataclasses
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime

# 导入历史记录
import sys
sys.path.insert(0, os.path.dirname(__file__))
from tool_history import tool_history

# ── 工具定义 ──
@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    category: str
    safe_dirs: List[str] = dataclasses.field(default_factory=list)
    requires_confirmation: bool = False


class ToolRegistry:
    """工具注册中心"""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.categories = {
            "file": "文件操作",
            "code": "代码操作",
            "system": "系统操作",
            "openclaw": "OpenClaw 工具",
            "web": "网络操作",
        }
        
        # 安全目录配置
        self.safe_dirs = [
            "E:/csi10",
            "E:/brain-system",
            "E:/llm-tools",
            "C:/dev",
        ]
        
        # 注册基础工具
        self._register_builtin_tools()
    
    def register_tool(self, tool_def: ToolDefinition):
        """注册工具"""
        self.tools[tool_def.name] = tool_def
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具"""
        return self.tools.get(name)
    
    def get_all_tools_description(self) -> str:
        """获取所有工具描述（供模型选择）"""
        desc = "你是一个智能助手，可以使用以下工具：\n\n"
        
        for category, category_name in self.categories.items():
            tools_in_category = [t for t in self.tools.values() if t.category == category]
            if tools_in_category:
                desc += f"## {category_name}\n"
                for tool in tools_in_category:
                    desc += f"{tool.name}: {tool.description}\n"
                    desc += f"  参数: {json.dumps(tool.parameters, ensure_ascii=False)}\n"
                desc += "\n"
        
        desc += """
## 输出格式要求
如果需要使用工具，请严格按照以下 JSON 格式输出：
{"tool": "工具名", "args": {"参数名": "参数值"}}

## 重要提醒
- 工具调用必须严格按照 JSON 格式输出
- 不要添加任何解释性文字
- JSON 必须是有效的格式（双引号、正确缩进）
"""
        return desc
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """执行工具"""
        tool = self.get_tool(tool_name)
        if not tool:
            return f"❌ 未知工具: {tool_name}"
        
        # 参数验证
        for param_name, param_def in tool.parameters.items():
            if param_def.get("required") and param_name not in args:
                return f"❌ 缺少必需参数: {param_name}"
        
        # 安全检查（文件操作）
        if tool.category == "file":
            path = args.get("path", "")
            if not self._is_safe_path(path, tool.safe_dirs):
                return f"❌ 拒绝访问：路径不在允许目录中"
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """执行工具"""
        tool = self.get_tool(tool_name)
        if not tool:
            return f"❌ 未知工具: {tool_name}"
        
        # 参数验证
        for param_name, param_def in tool.parameters.items():
            if param_def.get("required") and param_name not in args:
                return f"❌ 缺少必需参数: {param_name}"
        
        # 安全检查（文件操作）
        if tool.category == "file":
            path = args.get("path", "")
            if not self._is_safe_path(path, tool.safe_dirs):
                return f"❌ 拒绝访问：路径不在允许目录中"
        
        # 执行工具
        try:
            result = tool.function(**args)
            
            # 记录历史
            success = result.startswith("✅")
            tool_history.record_execution(tool_name, args, result, success)
            
            return result
        except Exception as e:
            error_result = f"❌ 工具执行失败: {str(e)}"
            tool_history.record_execution(tool_name, args, error_result, success=False)
            return error_result
    
    def _is_safe_path(self, path: str, allowed_dirs: List[str]) -> bool:
        """路径安全检查"""
        if not allowed_dirs:
            allowed_dirs = self.safe_dirs
        
        abs_path = os.path.abspath(path)
        # 统一路径格式（Windows: 反斜杠）
        normalized_allowed = [os.path.normpath(d) for d in allowed_dirs]
        return any(abs_path.startswith(d) for d in normalized_allowed)
    
    # ── 内置工具注册 ──
    def _register_builtin_tools(self):
        """注册内置工具"""
        
        # 文件操作工具
        self.register_tool(ToolDefinition(
            name="read_file",
            description="读取文件内容（适用于读取配置文件、日志文件、文本文件）",
            parameters={
                "path": {"type": "string", "required": True, "description": "文件路径"},
            },
            function=self._read_file,
            category="file",
        ))
        
        self.register_tool(ToolDefinition(
            name="write_file",
            description="写入文件（适用于创建新文件、保存数据、生成报告）",
            parameters={
                "path": {"type": "string", "required": True, "description": "文件路径"},
                "content": {"type": "string", "required": True, "description": "文件内容"},
            },
            function=self._write_file,
            category="file",
            requires_confirmation=True,
        ))
        
        self.register_tool(ToolDefinition(
            name="list_files",
            description="列出目录文件（适用于查看目录结构、查找特定类型文件）",
            parameters={
                "dir": {"type": "string", "required": True, "description": "目录路径"},
                "ext": {"type": "string", "required": False, "description": "文件扩展名过滤（如 .py, .txt）"},
            },
            function=self._list_files,
            category="file",
        ))
        
        # 代码操作工具（集成 OpenClaw）
        self.register_tool(ToolDefinition(
            name="code_read",
            description="读取代码文件（适用于查看代码、分析代码结构、定位问题代码）\n支持行号、范围、通配符，比 read_file 更强大",
            parameters={
                "path": {"type": "string", "required": True, "description": "文件路径或 glob 模式（如 E:/csi10/*.py）"},
                "offset": {"type": "int", "required": False, "description": "起始行号（从 1 开始）"},
                "limit": {"type": "int", "required": False, "description": "最大行数"},
            },
            function=self._code_read,
            category="code",
        ))
        
        self.register_tool(ToolDefinition(
            name="code_edit",
            description="编辑代码文件（适用于精确替换代码片段、修复 bug、修改逻辑）\n精确替换，不影响其他代码",
            parameters={
                "path": {"type": "string", "required": True, "description": "文件路径"},
                "oldText": {"type": "string", "required": True, "description": "要替换的旧文本（必须精确匹配）"},
                "newText": {"type": "string", "required": True, "description": "新文本"},
            },
            function=self._code_edit,
            category="code",
            requires_confirmation=True,
        ))
        
        # 系统操作工具
        self.register_tool(ToolDefinition(
            name="run_command",
            description="执行 shell 命令",
            parameters={
                "command": {"type": "string", "required": True, "description": "shell 命令"},
            },
            function=self._run_command,
            category="system",
            requires_confirmation=True,
        ))
        
        self.register_tool(ToolDefinition(
            name="run_python",
            description="执行 Python 代码",
            parameters={
                "code": {"type": "string", "required": True, "description": "Python 代码"},
            },
            function=self._run_python,
            category="system",
            requires_confirmation=True,
        ))
        
        # 信息查询工具
        self.register_tool(ToolDefinition(
            name="get_time",
            description="获取当前时间",
            parameters={},
            function=self._get_time,
            category="system",
        ))
        
        self.register_tool(ToolDefinition(
            name="search_memory",
            description="搜索 Brain Memory 向量库",
            parameters={
                "query": {"type": "string", "required": True, "description": "搜索关键词"},
            },
            function=self._search_memory,
            category="openclaw",
        ))
        # ── OpenClaw 工具集成 ──
        self.register_tool(ToolDefinition(
            name="code_diff",
            description="对比代码差异（适用于查看版本变化、检查代码修改、审核代码变更）\n输出标准 diff 格式，清晰显示差异",
            parameters={
                "file1": {"type": "string", "required": True, "description": "第一个文件路径（旧版本）"},
                "file2": {"type": "string", "required": True, "description": "第二个文件路径（新版本）"},
            },
            function=self._code_diff,
            category="openclaw",
        ))
        
        self.register_tool(ToolDefinition(
            name="file_patch",
            description="按行号替换文件内容（适用于批量修改、精确替换多行、修改配置）\n支持多个不重叠的修补，自动备份",
            parameters={
                "path": {"type": "string", "required": True, "description": "文件路径"},
                "patches": {"type": "array", "required": True, "description": "修补列表 [{start_line, end_line, new_content}]"},
            },
            function=self._file_patch,
            category="openclaw",
            requires_confirmation=True,
        ))
        
        self.register_tool(ToolDefinition(
            name="exec_python",
            description="执行Python代码（适用于快速计算、数据处理、自动化任务）",
            parameters={
                "code": {"type": "string", "required": True, "description": "Python代码字符串"},
            },
            function=self._exec_python,
            category="code",
        ))
        
        # 网络工具
        self.register_tool(ToolDefinition(
            name="web_search",
            description="网络搜索（适用于查询天气、新闻、实时信息）",
            parameters={
                "query": {"type": "string", "required": True, "description": "搜索关键词（如：福州天气）"},
            },
            function=self._web_search,
            category="web",
        ))
        
        self.register_tool(ToolDefinition(
            name="web_fetch",
            description="获取网页内容（适用于访问特定网址、获取网页数据）",
            parameters={
                "url": {"type": "string", "required": True, "description": "网页URL（如：https://weather.com）"},
            },
            function=self._web_fetch,
            category="web",
        ))
    
    def _read_file(self, path: str) -> str:
        """读取文件"""
        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return content[:2000] if len(content) > 2000 else content
    
    def _write_file(self, path: str, content: str) -> str:
        """写入文件"""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"✅ 写入成功: {path} ({len(content)} 字符)"
    
    def _list_files(self, dir: str, ext: str = None) -> str:
        """列出目录文件"""
        if not os.path.exists(dir):
            return f"❌ 目录不存在: {dir}"
        
        files = os.listdir(dir)
        if ext:
            files = [f for f in files if f.endswith(ext)]
        
        return "\n".join(files[:50])
    
    def _code_read(self, path: str, offset: int = None, limit: int = None) -> str:
        """读取代码文件（支持行号）"""
        if not os.path.exists(path):
            # 支持 glob 模式（简化版）
            import glob
            matches = glob.glob(path)
            if matches:
                results = []
                for match in matches[:5]:
                    results.append(f"文件: {match}")
                    with open(match, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    if offset and limit:
                        selected_lines = lines[offset-1:offset-1+limit]
                    elif limit:
                        selected_lines = lines[:limit]
                    else:
                        selected_lines = lines[:20]
                    
                    for i, line in enumerate(selected_lines, start=offset if offset else 1):
                        results.append(f"{i:4d} | {line.rstrip()}")
                return "\n".join(results)
            return f"❌ 文件不存在: {path}"
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        if offset and limit:
            selected_lines = lines[offset-1:offset-1+limit]
        elif limit:
            selected_lines = lines[:limit]
        else:
            selected_lines = lines
        
        results = []
        for i, line in enumerate(selected_lines, start=offset if offset else 1):
            results.append(f"{i:4d} | {line.rstrip()}")
        
        return "\n".join(results)
    
    def _code_edit(self, path: str, oldText: str, newText: str) -> str:
        """编辑代码文件"""
        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if oldText not in content:
            return f"❌ 未找到要替换的文本"
        
        new_content = content.replace(oldText, newText, 1)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return f"✅ 编辑成功: 替换 1 处"
    
    def _run_command(self, command: str) -> str:
        """执行 shell 命令"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return f"✅ 命令执行成功\n输出: {result.stdout[:500]}"
        except Exception as e:
            return f"❌ 命令执行失败: {str(e)}"
    
    def _run_python(self, code: str) -> str:
        """执行 Python 代码"""
        try:
            # 创建临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_file = f.name
            
            # 执行
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            # 清理临时文件
            os.unlink(temp_file)
            
            return f"✅ Python 执行成功\n输出: {result.stdout[:500]}"
        except Exception as e:
            return f"❌ Python 执行失败: {str(e)}"
    
    def _get_time(self) -> str:
        """获取当前时间"""
        now = datetime.now()
        return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def _search_memory(self, query: str) -> str:
        """搜索 Brain Memory"""
        # 调用 memory_search_better
        try:
            import requests
            # OpenClaw memory_search_better API（假设）
            # 这里简化实现，直接搜索文件
            
            memory_dir = "E:/brain-system/memory"
            if not os.path.exists(memory_dir):
                memory_dir = "E:/csi10/memory"
            
            results = []
            for md_file in os.listdir(memory_dir):
                if md_file.endswith('.md'):
                    path = os.path.join(memory_dir, md_file)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if query.lower() in content.lower():
                        results.append(f"文件: {md_file}\n匹配片段: {content[:200]}...")
            
            return "\n".join(results[:5]) if results else "未找到匹配内容"
        except Exception as e:
            return f"❌ Memory 搜索失败: {str(e)}"
    
    # ── OpenClaw 工具实现 ──
    def _code_diff(self, file1: str, file2: str) -> str:
        """对比代码差异"""
        try:
            import difflib
            
            # 检查文件是否存在
            if not os.path.exists(file1):
                return f"❌ 文件不存在: {file1}"
            if not os.path.exists(file2):
                return f"❌ 文件不存在: {file2}"
            
            # 读取文件
            with open(file1, 'r', encoding='utf-8', errors='ignore') as f:
                lines1 = f.readlines()
            with open(file2, 'r', encoding='utf-8', errors='ignore') as f:
                lines2 = f.readlines()
            
            # 生成差异
            diff = difflib.unified_diff(lines1, lines2, fromfile=file1, tofile=file2, lineterm='')
            diff_text = ''.join(diff)
            
            # 限制长度
            return diff_text[:2000] if len(diff_text) > 2000 else diff_text
        except Exception as e:
            return f"❌ 代码差异对比失败: {str(e)}"
    
    def _file_patch(self, path: str, patches: list) -> str:
        """按行号替换文件内容"""
        try:
            if not os.path.exists(path):
                return f"❌ 文件不存在: {path}"
            
            # 读取文件
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 创建备份
            backup_path = path + '.bak'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # 执行修补
            patch_count = 0
            for patch in patches:
                start_line = patch.get('start_line')
                end_line = patch.get('end_line')
                new_content = patch.get('new_content')
                
                # 验证行号
                if start_line < 1 or end_line > len(lines) or start_line > end_line:
                    return f"❌ 行号无效: start={start_line}, end={end_line}"
                
                # 替换内容
                lines[start_line-1:end_line] = [new_content + '\n']
                patch_count += 1
            
            # 写入文件
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return f"✅ 文件修补成功: {patch_count} 处修补\n备份: {backup_path}"
        except Exception as e:
            return f"❌ 文件修补失败: {str(e)}"
    
    def _exec_python(self, code: str) -> str:
        """执行 Python 代码"""
        try:
            # 创建临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_file = f.name
            
            # 执行
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            # 清理临时文件
            os.unlink(temp_file)
            
            # 返回结果
            # 返回结果
        except Exception as e:
            return f"❌ Python执行失败: {str(e)}"
    
    def _web_search(self, query: str) -> str:
        """网络搜索（使用wttr.in API查询天气）"""
        try:
            import requests
            import json
            
            # 对于天气查询，使用wttr.in API
            if '天气' in query or 'weather' in query.lower():
                # 提取城市名
                city = query.replace('天气', '').replace('weather', '').strip()
                if not city:
                    city = 'Fuzhou'  # 默认福州
                
                url = f"https://wttr.in/{city}?format=j1&lang=zh"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    current = data['current_condition'][0]
                    
                    result = f"✅ {city}天气查询成功\n"
                    result += f"温度: {current['temp_C']}°C\n"
                    result += f"天气: {current['lang_zh'][0]['value']}\n"
                    result += f"风速: {current['windspeedKmph']} km/h\n"
                    result += f"湿度: {current['humidity']}%\n"
                    return result
                else:
                    return f"❌ 天气API请求失败: HTTP {response.status_code}"
            
            else:
                # 对于其他搜索，提示用户使用浏览器
                return f"⚠️ 搜索功能暂不支持\n建议: 在浏览器中搜索 '{query}'\n或使用web_fetch工具访问特定网址"
                
        except requests.exceptions.Timeout:
            return "❌ 网络请求超时"
        except requests.exceptions.ConnectionError:
            return "❌ 无法连接网络"
        except Exception as e:
            return f"❌ 网络搜索失败: {str(e)}"
    
    def _web_fetch(self, url: str) -> str:
        """获取网页内容"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                # 提取文本内容
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 移除script和style标签
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # 获取文本
                text = soup.get_text(separator='\n', strip=True)
                
                # 限制长度
                if len(text) > 2000:
                    text = text[:2000] + "..."
                
                return f"✅ 网页获取成功\nURL: {url}\n内容: {text}"
            else:
                return f"❌ 网页请求失败: HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "❌ 网络请求超时"
        except requests.exceptions.ConnectionError:
            return "❌ 无法连接网络"
        except Exception as e:
            return f"❌ 网页获取失败: {str(e)}"

# ── 全局工具注册中心 ──
tool_registry = ToolRegistry()

# ── 使用示例 ──
if __name__ == "__main__":
    # 获取工具描述
    print(tool_registry.get_all_tools_description())
    
    # 执行工具
    result = tool_registry.execute_tool("read_file", {"path": "E:/csi10/live_runner.py"})
    print(result)