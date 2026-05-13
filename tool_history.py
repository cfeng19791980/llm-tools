#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具执行历史记录
记录工具调用历史，支持搜索和重放

功能：
1. 记录每次工具调用的详细信息
2. 支持搜索历史记录
3. 支持重放历史任务
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class ToolExecutionHistory:
    """工具执行历史记录"""
    
    def __init__(self, log_file="E:/llm-tools/logs/history.json"):
        self.log_file = log_file
        self.history: List[Dict[str, Any]] = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_history(self):
        """保存历史记录"""
        os.makedirs(os.path.dirname(self.log_file) if os.path.dirname(self.log_file) else ".", exist_ok=True)
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def record_execution(self, tool_name: str, args: Dict[str, Any], result: str, success: bool = True):
        """记录执行"""
        entry = {
            "id": len(self.history) + 1,
            "timestamp": datetime.now().isoformat(),
            "time_str": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "tool": tool_name,
            "args": args,
            "result": result[:500],  # 限制长度
            "success": success,
        }
        self.history.append(entry)
        self._save_history()
        return entry["id"]
    
    def search_history(self, query: str) -> List[Dict[str, Any]]:
        """搜索历史"""
        matches = []
        for entry in self.history:
            if query.lower() in str(entry).lower():
                matches.append(entry)
        return matches
    
    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的历史记录"""
        return self.history[-limit:] if len(self.history) >= limit else self.history
    
    def get_history_by_tool(self, tool_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取指定工具的历史记录"""
        matches = [entry for entry in self.history if entry["tool"] == tool_name]
        return matches[-limit:] if len(matches) >= limit else matches
    
    def replay_execution(self, entry_id: int, tool_registry):
        """重新执行历史任务"""
        entry = self.history[entry_id - 1]
        tool_name = entry["tool"]
        args = entry["args"]
        
        # 执行工具
        result = tool_registry.execute_tool(tool_name, args)
        
        # 记录新的执行
        new_entry_id = self.record_execution(tool_name, args, result, success=result.startswith("✅"))
        
        return {
            "original_entry_id": entry_id,
            "new_entry_id": new_entry_id,
            "tool": tool_name,
            "args": args,
            "result": result,
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_calls = len(self.history)
        success_calls = sum(1 for entry in self.history if entry.get("success"))
        
        # 按工具统计
        tool_stats = {}
        for entry in self.history:
            tool_name = entry["tool"]
            if tool_name not in tool_stats:
                tool_stats[tool_name] = {"total": 0, "success": 0}
            tool_stats[tool_name]["total"] += 1
            if entry.get("success"):
                tool_stats[tool_name]["success"] += 1
        
        return {
            "total_calls": total_calls,
            "success_calls": success_calls,
            "success_rate": success_calls / total_calls * 100 if total_calls > 0 else 0,
            "tool_stats": tool_stats,
        }
    
    def clear_history(self):
        """清空历史记录"""
        self.history = []
        self._save_history()


# ── 全局历史记录实例 ──
tool_history = ToolExecutionHistory()


# ── 使用示例 ──
if __name__ == "__main__":
    # 模拟记录
    tool_history.record_execution("read_file", {"path": "E:/csi10/live_runner.py"}, "✅ 读取成功", success=True)
    tool_history.record_execution("code_diff", {"file1": "file1.py", "file2": "file2.py"}, "✅ 对比成功", success=True)
    
    # 搜索历史
    print("搜索 'live_runner':")
    matches = tool_history.search_history("live_runner")
    print(matches)
    
    # 获取统计
    print("\n统计信息:")
    stats = tool_history.get_statistics()
    print(stats)