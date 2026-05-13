#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM-Tools 预设配置管理
"""

import json
from pathlib import Path

# 预设配置
PRESETS = {
    'fast': {
        'name': 'Fast',
        'description': '快速推理，适合测试',
        'model': 'Qwen3.5-9B-Q3_K_S.gguf',
        'port': 1235,
        'ngl': 35,
        'ctx': 4096,
        'threads': 8,
        'temp': 0.7,
        'seed': 42,
        'flash_attn': True
    },
    'quality': {
        'name': 'Quality',
        'description': '高质量推理，最佳效果',
        'model': 'Qwen3.5-9B-Q4_K_M.gguf',
        'port': 1235,
        'ngl': 99,
        'ctx': 32000,
        'threads': 8,
        'temp': 0.05,
        'seed': 42,
        'flash_attn': True
    },
    'balance': {
        'name': 'Balance',
        'description': '平衡配置，速度与质量兼顾',
        'model': 'Qwen3.5-9B-Q4_K_M.gguf',
        'port': 1235,
        'ngl': 50,
        'ctx': 8192,
        'threads': 8,
        'temp': 0.1,
        'seed': 42,
        'flash_attn': True
    },
    'vl': {
        'name': 'VL Vision',
        'description': '视觉语言模型',
        'model': 'Qwen3-VL-4B-Instruct-Q6_K.gguf',
        'port': 1235,
        'ngl': 40,
        'ctx': 4096,
        'threads': 8,
        'temp': 0.1,
        'seed': 42,
        'flash_attn': True
    }
}

def get_presets():
    """获取所有预设配置"""
    return PRESETS

def get_preset(name):
    """获取特定预设配置"""
    return PRESETS.get(name, None)

def apply_preset(name):
    """应用预设配置"""
    preset = get_preset(name)
    if preset:
        # 可以在这里保存为 bat 文件
        return preset
    return None

# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("Presets Configuration")
    print("=" * 60)
    
    for name, config in PRESETS.items():
        print(f"\n{name}: {config['name']}")
        print(f"  Description: {config['description']}")
        print(f"  Model: {config['model']}")
        print(f"  GPU Layers: {config['ngl']}")
        print(f"  Context: {config['ctx']}")
    
    print("\n" + "=" * 60)