#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Electron ffmpeg.dll 依赖修复脚本
检查 ffmpeg.dll 是否存在，并提供解决方案

常见问题：
1. Electron 应用启动时找不到 ffmpeg.dll
2. ffmpeg.dll 是 Electron 的音视频处理依赖
3. 通常位于 Electron 根目录或 resources 目录

解决方案：
1. 下载 ffmpeg.dll
2. 放置到 Electron 应用目录
3. 或重新安装 Electron
"""

import os
import subprocess
import sys

def check_ffmpeg_dll():
    """检查 ffmpeg.dll 是否存在"""
    search_paths = [
        "E:/csi10",
        "C:/Users/10341/.openclaw",
        "C:/Users/10341/AppData/Local/Programs",
        "C:/Program Files",
        "C:/Windows/System32",
    ]
    
    found = []
    for path in search_paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower() == "ffmpeg.dll":
                        found.append(os.path.join(root, file))
    
    return found

def check_electron_installation():
    """检查 Electron 安装状态"""
    try:
        result = subprocess.run(
            ["npm", "list", "electron"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout
    except:
        return "Electron 未安装或 npm 命令不可用"

def main():
    print("=" * 60)
    print("Electron ffmpeg.dll 依赖检查工具")
    print("=" * 60)
    
    # 检查 ffmpeg.dll
    print("\n[检查 ffmpeg.dll]")
    ffmpeg_dlls = check_ffmpeg_dll()
    
    if ffmpeg_dlls:
        print(f"✅ 找到 ffmpeg.dll 文件:")
        for dll in ffmpeg_dlls[:5]:
            print(f"   {dll}")
    else:
        print("❌ 未找到 ffmpeg.dll 文件")
    
    # 检查 Electron
    print("\n[检查 Electron 安装]")
    electron_status = check_electron_installation()
    print(electron_status[:200])
    
    # 提供解决方案
    print("\n" + "=" * 60)
    print("解决方案")
    print("=" * 60)
    
    if not ffmpeg_dlls:
        print("""
方案 1：下载 ffmpeg.dll
  - 下载地址：https://ffmpeg.org/download.html
  - 或从 Electron 官方版本中提取
  
方案 2：重新安装 Electron
  npm install electron --save-dev
  
方案 3：重新下载完整 Electron 包
  npm install electron@latest --force
  
方案 4：放置 ffmpeg.dll 到应用目录
  - 将 ffmpeg.dll 放到 E:/csi10 目录
  - 或放到 Electron 应用根目录
""")
    else:
        print("\n✅ ffmpeg.dll 已存在，无需修复")

if __name__ == "__main__":
    main()