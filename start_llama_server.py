#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动llama-server推理服务
通过调用Backend API /api/start启动llama-server
"""

import requests
import time
import sys

def start_llama_server():
    """启动llama-server"""
    
    print('启动llama-server推理服务...')
    print('='*60)
    
    # Backend API地址
    backend_api = 'http://127.0.0.1:5003'
    
    # 尝试启动llama-server
    print('\n调用/api/start API...')
    
    try:
        response = requests.post(
            f'{backend_api}/api/start',
            json={'model': 'Qwen3.5-9B-Q4_K_M.gguf'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result['success']:
                print(f'\n✅✅✅ llama-server启动成功')
                print(f'PID: {result["pid"]}')
                print(f'端口: {result["port"]}')
                
                return True
            
            else:
                print(f'\n❌ llama-server启动失败')
                print(f'原因: {result["message"]}')
                
                # 如果显示"already running"，说明已经启动
                if 'already running' in result['message']:
                    print('\n⚠️ llama-server已在运行（无需重复启动）')
                    return True
                
                return False
        
        else:
            print(f'\n❌ API请求失败: HTTP {response.status_code}')
            return False
    
    except requests.exceptions.ConnectionError:
        print('\n❌ Backend未运行（无法连接API）')
        return False
    
    except requests.exceptions.Timeout:
        print('\n❌ API请求超时')
        return False
    
    except Exception as e:
        print(f'\n❌ 启动失败: {e}')
        return False

if __name__ == "__main__":
    success = start_llama_server()
    
    if success:
        print('\n✅✅✅ llama-server启动完成')
        sys.exit(0)
    
    else:
        print('\n❌ llama-server启动失败')
        sys.exit(1)