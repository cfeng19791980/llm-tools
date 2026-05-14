#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multi_search_engine_17.py - 集成17个搜索引擎（来自multi-search-engine-2-0-1项目）

搜索引擎：
- 国内（8个）：Baidu、Bing CN、Bing INT、360、Sogou、WeChat、Toutiao、Jisilu
- 国际（9个）：Google、Google HK、DuckDuckGo、Yahoo、Startpage、Brave、Ecosia、Qwant、WolframAlpha

特性：
- 无需API密钥（直接URL访问）
- 支持高级搜索操作符
- 国内引擎优先
- 失败自动降级
"""

import requests
import json
import re
from bs4 import BeautifulSoup
import time

# 加载搜索引擎配置
SEARCH_ENGINES = [
    {"name": "Baidu", "url": "https://www.baidu.com/s?wd={keyword}", "region": "cn", "priority": 1},
    {"name": "Bing CN", "url": "https://cn.bing.com/search?q={keyword}&ensearch=0", "region": "cn", "priority": 2},
    {"name": "Bing INT", "url": "https://cn.bing.com/search?q={keyword}&ensearch=1", "region": "cn", "priority": 3},
    {"name": "360", "url": "https://www.so.com/s?q={keyword}", "region": "cn", "priority": 4},
    {"name": "Sogou", "url": "https://sogou.com/web?query={keyword}", "region": "cn", "priority": 5},
    {"name": "WeChat", "url": "https://wx.sogou.com/weixin?type=2&query={keyword}", "region": "cn", "priority": 6},
    {"name": "Toutiao", "url": "https://so.toutiao.com/search?keyword={keyword}", "region": "cn", "priority": 7},
    {"name": "Jisilu", "url": "https://www.jisilu.cn/explore/?keyword={keyword}", "region": "cn", "priority": 8},
    {"name": "Google", "url": "https://www.google.com/search?q={keyword}", "region": "global", "priority": 9},
    {"name": "Google HK", "url": "https://www.google.com.hk/search?q={keyword}", "region": "global", "priority": 10},
    {"name": "DuckDuckGo", "url": "https://duckduckgo.com/html/?q={keyword}", "region": "global", "priority": 11},
    {"name": "Yahoo", "url": "https://search.yahoo.com/search?p={keyword}", "region": "global", "priority": 12},
    {"name": "Startpage", "url": "https://www.startpage.com/sp/search?query={keyword}", "region": "global", "priority": 13},
    {"name": "Brave", "url": "https://search.brave.com/search?q={keyword}", "region": "global", "priority": 14},
    {"name": "Ecosia", "url": "https://www.ecosia.org/search?q={keyword}", "region": "global", "priority": 15},
    {"name": "Qwant", "url": "https://www.qwant.com/?q={keyword}", "region": "global", "priority": 16},
    {"name": "WolframAlpha", "url": "https://www.wolframalpha.com/input?i={keyword}", "region": "global", "priority": 17}
]

class MultiSearchEngine17:
    """集成17个搜索引擎"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search(self, keyword: str, engine: str = 'auto', max_results: int = 5) -> dict:
        """
        统一搜索接口
        
        Args:
            keyword: 搜索关键词
            engine: 搜索引擎名称或'auto'
            max_results: 最大结果数
        
        Returns:
            dict: {
                'success': True/False,
                'engine': '使用的引擎',
                'results': [{'title': '标题', 'url': '链接', 'snippet': '摘要'}],
                'fallback_used': '是否使用降级引擎'
            }
        """
        
        if engine == 'auto':
            # 国内引擎优先
            engine_list = [e for e in SEARCH_ENGINES if e['region'] == 'cn']
        else:
            # 指定引擎
            engine_list = [e for e in SEARCH_ENGINES if e['name'] == engine]
        
        # 依次尝试
        for engine_info in engine_list:
            result = self._search_single_engine(keyword, engine_info, max_results)
            
            if result['success']:
                return result
        
        # 所有引擎失败
        return {
            'success': False,
            'engine': 'all',
            'results': [],
            'error': '所有搜索引擎失败'
        }
    
    def _search_single_engine(self, keyword: str, engine_info: dict, max_results: int) -> dict:
        """单个搜索引擎搜索"""
        
        engine_name = engine_info['name']
        
        url_template = engine_info['url']
        
        url = url_template.replace('{keyword}', keyword)
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                # 解析结果
                results = self._parse_results(response.text, engine_name, max_results)
                
                if results:
                    return {
                        'success': True,
                        'engine': engine_name,
                        'results': results,
                        'fallback_used': False
                    }
                
                else:
                    return {
                        'success': False,
                        'engine': engine_name,
                        'results': [],
                        'error': '无搜索结果'
                    }
            
            else:
                return {
                    'success': False,
                    'engine': engine_name,
                    'results': [],
                    'error': f'HTTP {response.status_code}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'engine': engine_name,
                'results': [],
                'error': str(e)[:100]
            }
    
    def _parse_results(self, html: str, engine_name: str, max_results: int) -> list:
        """解析搜索结果（简化版）"""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        results = []
        
        # 根据不同引擎解析
        if engine_name == 'Baidu':
            # 百度结果解析
            for result in soup.find_all('div', class_='result', limit=max_results):
                title_elem = result.find('h3', class_='t')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    
                    link_elem = result.find('a', href=True)
                    
                    url = link_elem['href'] if link_elem else ''
                    
                    results.append({'title': title, 'url': url, 'snippet': ''})
        
        elif 'Bing' in engine_name:
            # Bing结果解析
            for result in soup.find_all('li', class_='b_algo', limit=max_results):
                title_elem = result.find('h2')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    
                    link_elem = title_elem.find('a', href=True)
                    
                    url = link_elem['href'] if link_elem else ''
                    
                    snippet_elem = result.find('p')
                    
                    snippet = snippet_elem.get_text(strip=True)[:100] if snippet_elem else ''
                    
                    results.append({'title': title, 'url': url, 'snippet': snippet})
        
        elif engine_name == 'DuckDuckGo':
            # DuckDuckGo结果解析
            for result in soup.find_all('div', class_='result', limit=max_results):
                title_elem = result.find('a', class_='result__a')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    
                    url = title_elem['href']
                    
                    results.append({'title': title, 'url': url, 'snippet': ''})
        
        else:
            # 通用解析（提取所有链接）
            for link in soup.find_all('a', href=True, limit=max_results * 2):
                href = link['href']
                
                # 过滤有效链接
                if href.startswith('http') and 'javascript' not in href:
                    title = link.get_text(strip=True)
                    
                    if title and len(title) > 5:  # 过滤短标题
                        results.append({'title': title[:100], 'url': href, 'snippet': ''})
        
        return results[:max_results]


# 全局实例
multi_search_17 = MultiSearchEngine17()


def multi_search_17_func(keyword: str, engine: str = 'auto') -> str:
    """统一搜索接口（供LLM-Tools调用）"""
    
    result = multi_search_17.search(keyword, engine, max_results=3)
    
    if result['success']:
        # 格式化输出
        output = f"✅ {result['engine']}搜索成功\n找到 {len(result['results'])} 个结果:\n"
        
        for i, res in enumerate(result['results'], 1):
            output += f"{i}. {res['title']}\n   URL: {res['url']}\n"
        
        return output
    
    else:
        return f"❌ 搜索失败: {result.get('error', '未知错误')}"


# 测试代码
if __name__ == '__main__':
    print('测试multi_search_engine_17...')
    
    # 测试Bing CN
    result = multi_search_17_func('Python教程', engine='Bing CN')
    
    print(result)