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

# =====================================================================
# Agent v2.0 核心架构：工具验证、重试机制、安全检查
# =====================================================================

class ToolValidator:
    """工具结果验证"""
    def validate_result(self, tool_name, result, user_intent):
        """验证工具结果是否满足用户意图"""
        # 相关性检查
        if tool_name == 'web_search' or tool_name == 'browser':
            # 检查搜索结果是否与用户意图相关
            if user_intent and '访华' in user_intent:
                if '访日' in str(result) and '访华' not in str(result):
                    return {
                        'valid': False,
                        'reason': '搜索结果与用户意图不匹配（访日 vs 访华）',
                        'suggestion': '建议重试，使用更精确的关键词'
                    }
        
        # 完整性检查
        if tool_name == 'read_file' or tool_name == 'code_read':
            if not result or len(str(result)) < 100:
                return {
                    'valid': False,
                    'reason': '文件内容可能不完整（长度<100字符）',
                    'suggestion': '建议检查文件是否完整'
                }
        
        # 错误检查
        if isinstance(result, dict) and 'error' in result:
            return {
                'valid': False,
                'reason': result.get('error', '未知错误'),
                'suggestion': '建议检查工具参数是否正确'
            }
        
        return {'valid': True}

class RetryHandler:
    """重试机制"""
    def __init__(self, max_retries=3):
        self.max_retries = max_retries
        self.retry_count = {}  # 每个工具的重试计数
    
    def handle_failure(self, tool_name, error, context):
        """处理工具失败"""
        # 增加错误计数
        if tool_name not in self.retry_count:
            self.retry_count[tool_name] = 0
        
        self.retry_count[tool_name] += 1
        
        if self.retry_count[tool_name] < self.max_retries:
            # 重试机制
            return {
                'action': 'retry',
                'message': f"工具失败，正在重试（第{self.retry_count[tool_name]}次）",
                'suggestion': '建议使用相同参数重试'
            }
        else:
            # 降级策略
            return {
                'action': 'fallback',
                'message': f"工具多次失败（{self.max_retries}次），尝试备选方案",
                'suggestion': self.get_fallback_tool(tool_name)
            }
    
    def get_fallback_tool(self, tool_name):
        """获取备选工具"""
        fallback_map = {
            'web_search': 'web_fetch',
            'browser': 'web_fetch',
            'read_file': 'code_read',
            'exec_python': 'run_command',
            'run_command': 'exec_python'
        }
        return fallback_map.get(tool_name, '无备选工具')
    
    def reset_retry_count(self, tool_name):
        """重置重试计数"""
        if tool_name in self.retry_count:
            self.retry_count[tool_name] = 0

class SecurityChecker:
    """安全检查（高危操作确认）"""
    HIGH_RISK_OPERATIONS = [
        'write_file', 'run_command', 'exec_python', 'file_patch'
    ]
    
    def check_operation_risk(self, tool_name, args):
        """检查操作风险等级"""
        if tool_name in self.HIGH_RISK_OPERATIONS:
            # 生成风险提示
            risk_message = self.get_risk_message(tool_name, args)
            return {
                'risk_level': 'HIGH',
                'confirmation_required': True,
                'risk_message': risk_message,
                'tool_name': tool_name,
                'args': args
            }
        return {'risk_level': 'LOW', 'confirmation_required': False}
    
    def get_risk_message(self, tool_name, args):
        """生成风险提示"""
        if tool_name == 'write_file':
            return f"⚠️ 将写入文件 {args.get('path', '未知路径')}，请确认是否继续？"
        elif tool_name == 'run_command':
            return f"⚠️ 将执行命令 {args.get('command', '未知命令')}，请确认是否继续？"
        elif tool_name == 'exec_python':
            return f"⚠️ 将执行Python代码，请确认是否继续？"
        elif tool_name == 'file_patch':
            return f"⚠️ 将修改文件 {args.get('path', '未知路径')}，请确认是否继续？"
        return f"⚠️ 该操作可能修改文件或执行代码，请确认是否继续？"

# 全局实例
validator = ToolValidator()
retry_handler = RetryHandler()
security_checker = SecurityChecker()

# =====================================================================

# ✅ v3.0改进：集中配置管理（借鉴openclaw.json）
# 读取llm-tools-config.json配置文件
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'llm-tools-config.json')

def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 默认配置（兼容旧版本）
        return {
            'tools': {
                'safeDirs': ['E:/llm-tools', 'E:/csi10'],
                'requiresConfirmation': ['run_command', 'write_file']
            }
        }

# 加载配置
CONFIG = load_config()

# 导入历史记录
import sys
sys.path.insert(0, os.path.dirname(__file__))
from tool_history import tool_history

# 导入搜索引擎
from multi_search_engine_17 import multi_search_17_func

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
        
        # 安全目录配置（从config.json读取）
        self.safe_dirs = CONFIG['tools']['safeDirs']  # ✅ 集中配置管理
        
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
        except TimeoutError:
            error_result = f"❌ TimeoutError: 工具执行超时，建议切换到run_command工具绕过Python层"
            tool_history.record_execution(tool_name, args, error_result, success=False)
            return error_result
        except PermissionError:
            error_result = f"❌ PermissionError: 权限不足，建议切换到run_command工具使用系统命令"
            tool_history.record_execution(tool_name, args, error_result, success=False)
            return error_result
        except FileNotFoundError:
            error_result = f"❌ FileNotFoundError: 文件不存在，建议检查路径或创建文件"
            tool_history.record_execution(tool_name, args, error_result, success=False)
            return error_result
        except KeyError as e:
            error_result = f"❌ KeyError: 缺少必需参数 '{str(e)}'，建议补充参数后重试"
            tool_history.record_execution(tool_name, args, error_result, success=False)
            return error_result
        except Exception as e:
            error_result = f"❌ Error: {str(e)}，请分析错误原因并采取相应行动"
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
        
        # 多层搜索工具（集成拦截器）
        self.register_tool(ToolDefinition(
            name="browser_navigate",
            description="多层搜索流程（适用于搜索关键词、点击链接、提取正文）\n支持：百度搜索 → 点击第一条结果 → 提取完整信息",
            parameters={
                "search_query": {"type": "string", "required": True, "description": "搜索关键词（如：特朗普）"},
                "click_first": {"type": "boolean", "required": False, "description": "是否点击第一条结果（默认True）"},
            },
            function=self._browser_navigate,
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
        """网络搜索（使用multi_search_engine_17集成17个搜索引擎）"""
        
        # 使用multi_search_17（国内引擎优先）
        return multi_search_17_func(query, engine='auto')
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
    
    def _browser_navigate(self, search_query: str, click_first: bool = True) -> str:
        """多层搜索流程（集成拦截器）"""
        
        try:
            # 导入拦截器
            sys.path.insert(0, 'c:\\dev')
            
            from browser_interceptor import BrowserInterceptor
            
            import time
            
            # 启动拦截器（可见模式，便于观察）
            interceptor = BrowserInterceptor(headless=False)
            
            # Step 1: 直接跳转到搜索结果页面
            search_url = f'https://www.baidu.com/s?wd={search_query}'
            
            interceptor.start(search_url)
            
            page = interceptor._page
            
            # 等待页面加载
            time.sleep(3)
            
            # Step 2: 识别第一条结果
            selectors_to_try = [
                '.result.c-container a',
                '.result a',
                '#content_left .result a',
                'a[href*="baike.baidu.com"]',
                'a[href*="news"]'
            ]
            
            first_result = None
            first_result_title = None
            first_result_url = None
            
            for selector in selectors_to_try:
                try:
                    first_result = page.locator(selector).first
                    
                    if first_result.count() > 0:
                        first_result_title = first_result.inner_text(timeout=2000)
                        first_result_url = first_result.get_attribute('href')
                        break
                
                except:
                    continue
            
            if not first_result:
                interceptor.close()
                return f"❌ 未找到搜索结果: {search_query}"
            
            # Step 3: 点击第一条结果（如果click_first=True）
            if click_first:
                first_result.click()
                
                page.wait_for_load_state('domcontentloaded')
                
                time.sleep(2)
                
                final_url = page.url
            
            else:
                final_url = first_result_url
            
            
            # Step 4: 提取正文
            content = page.locator('body').inner_text()
            
            # 关闭浏览器
            interceptor.close()
            
            # 返回结果
            result_str = f"✅ 多层搜索成功\n"
            result_str += f"搜索词: {search_query}\n"
            result_str += f"第一条结果: {first_result_title}\n"
            result_str += f"跳转URL: {final_url}\n"
            result_str += f"正文长度: {len(content)}字符\n"
            result_str += f"正文片段: {content[:200]}"
            
            return result_str
        
        except Exception as e:
            return f"❌ 多层搜索失败: {str(e)}"

# ── 全局工具注册中心 ──
tool_registry = ToolRegistry()

# ── 使用示例 ──
if __name__ == "__main__":
    # 获取工具描述
    print(tool_registry.get_all_tools_description())
    
    # 执行工具
    result = tool_registry.execute_tool("read_file", {"path": "E:/csi10/live_runner.py"})
    print(result)