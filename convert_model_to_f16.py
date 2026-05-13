#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 embedding 模型从 f32 转换为 f16 精度
减少内存占用和显存占用
"""

import os
import torch
import json

print("=" * 60)
print("Embedding Model Precision Conversion: f32 -> f16")
print("=" * 60)

# 模型路径
model_path = "C:/Users/10341/models"
model_file = os.path.join(model_path, "pytorch_model.bin")
config_file = os.path.join(model_path, "config.json")

# 检查文件是否存在
if not os.path.exists(model_file):
    print(f"❌ Model file not found: {model_file}")
    exit(1)

# 检查当前文件大小
original_size_mb = os.path.getsize(model_file) / (1024 * 1024)
print(f"\nOriginal model file size: {original_size_mb:.2f} MB")

# 加载模型权重
print("\nLoading model weights...")
try:
    state_dict = torch.load(model_file, map_location='cpu')
    print(f"✅ Model loaded successfully")
    print(f"  Number of parameters: {len(state_dict)}")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    exit(1)

# 检查当前精度
print("\nChecking current precision:")
first_key = list(state_dict.keys())[0]
current_dtype = state_dict[first_key].dtype
print(f"  Current dtype: {current_dtype}")

# 转换为 f16
print("\nConverting to float16...")
for key in state_dict.keys():
    if state_dict[key].dtype == torch.float32:
        state_dict[key] = state_dict[key].half()  # Convert to float16

print(f"✅ Conversion completed")

# 检查转换后的精度
new_dtype = state_dict[first_key].dtype
print(f"  New dtype: {new_dtype}")

# 保存转换后的模型（备份原文件）
backup_file = model_file + ".f32_backup"
print(f"\nBacking up original file to: {backup_file}")
os.rename(model_file, backup_file)

print(f"Saving converted model...")
torch.save(state_dict, model_file)

# 检查转换后的文件大小
new_size_mb = os.path.getsize(model_file) / (1024 * 1024)
print(f"✅ Model saved successfully")
print(f"  New file size: {new_size_mb:.2f} MB")
print(f"  Size reduction: {original_size_mb - new_size_mb:.2f} MB ({(original_size_mb - new_size_mb) / original_size_mb * 100:.1f}%)")

# 更新配置文件
print(f"\nUpdating config.json...")
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

config['torch_dtype'] = 'float16'

with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"✅ Config updated: torch_dtype = 'float16'")

# 验证转换后的模型
print("\nVerifying converted model...")
try:
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer(model_path)
    test_text = "这是一个测试文本"
    embedding = model.encode(test_text)
    
    print(f"✅ Verification successful")
    print(f"  Embedding shape: {embedding.shape}")
    print(f"  Embedding dtype: {embedding.dtype}")
    print(f"  First 5 values: {embedding[:5]}")
    
except Exception as e:
    print(f"⚠️ Warning: Verification failed: {e}")
    print(f"  But conversion was successful, model may need reload")

print("\n" + "=" * 60)
print("Conversion Complete")
print("=" * 60)
print(f"Original size: {original_size_mb:.2f} MB (float32)")
print(f"New size: {new_size_mb:.2f} MB (float16)")
print(f"Backup: {backup_file}")
print("=" * 60)