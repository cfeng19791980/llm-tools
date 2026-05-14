
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multi_search_engine.py - 多搜索引擎集成
支持DuckDuckGo、Wikipedia、wttr.in等多种搜索方式
"""

import requests
import json
import re
from bs4 import BeautifulSoup

class MultiSearchEngine:
    """多搜索引擎集成"""
    
    def search(self, query: str, engine: str = 'auto') -> dict:
        """
        统一搜索接口
        
        Args:
            query: 搜索关键词
            engine: 搜索引擎（auto/duckduckgo/wikipedia/weather）
        
        Returns:
            dict: {
                'success': True/False,
                'engine': '使用的引擎',
                'result': '搜索结果',
                'fallback_used': '是否使用降级引擎'
            }
        """
        
        # 自动选择引擎
        if engine == 'auto':
            engine = self._detect_best_engine(query)
        
        # 按引擎执行搜索
        if engine == 'weather':
            return self._search_weather(query)
        
        elif engine == 'wikipedia':
            result = self._search_wikipedia(query)
            
            if not result['success']:
                # 降级到DuckDuckGo
                fallback = self._search_duckduckgo(query)
                fallback['fallback_used'] = True
                
                return fallback
            
            return result
        
        elif engine == 'duckduckgo':
            return self._search_duckduckgo(query)
        
        else:
            return {'success': False, 'error': '未知引擎'}
    
    def _detect_best_engine(self, query: str) -> str:
        """自动检测最佳搜索引擎"""
        
        # 天气查询
        if '天气' in query or 'weather' in query.lower():
            return 'weather'
        
        # 知识类查询（百科、定义、历史）
        knowledge_keywords = ['是什么', '什么是', '百科', '定义', '历史', '人物', '地名']
        
        if any(kw in query for kw in knowledge_keywords):
            return 'wikipedia'
        
        # 其他默认DuckDuckGo
        return 'duckduckgo'
    
    def _search_weather(self, query: str) -> dict:
        """天气查询（wttr.in）"""
        
        # 提取城市名
        city = query.replace('天气', '').replace('weather', '').strip()
        
        if not city:
            city = 'Fuzhou'
        
        try:
            url = f"https://wttr.in/{city}?format=j1"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                current = data['current_condition'][0]
                
                result_str = f"✅ {city}天气查询成功\n"
                result_str += f"温度: {current['temp_C']}°C\n"
                result_str += f"天气: {current['weatherDesc'][0]['value']}\n"
                result_str += f"风速: {current['windspeedKmph']} km/h\n"
                result_str += f"湿度: {current['humidity']}%"
                
                return {
                    'success': True,
                    'engine': 'weather',
                    'result': result_str
                }
            
            else:
                return {'success': False, 'engine': 'weather', 'error': 'HTTP错误'}
        
        except Exception as e:
            return {'success': False, 'engine': 'weather', 'error': str(e)}
    
    def _search_wikipedia(self, query: str) -> dict:
        """Wikipedia搜索"""
        
        try:
            # Wikipedia API
            url = "https://en.wikipedia.org/w/api.php"
            
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'format': 'json',
                'utf8': 1,
                'srlimit': 3
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                search_results = data['query']['search']
                
                if search_results:
                    # 获取第一个结果
                    first_result = search_results[0]
                    
                    title = first_result['title']
                    snippet = first_result['snippet']
                    
                    # 清理HTML标签
                    snippet = re.sub(r'<.*?>', '', snippet)
                    
                    result_str = f"✅ Wikipedia搜索成功\n"
                    result_str += f"标题: {title}\n"
                    result_str += f"摘要: {snippet[:100]}\n"
                    result_str += f"链接: https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                    
                    return {
                        'success': True,
                        'engine': 'wikipedia',
                        'result': result_str
                    }
                
                else:
                    return {'success': False, 'engine': 'wikipedia', 'error': '无结果'}
            
            else:
                return {'success': False, 'engine': 'wikipedia', 'error': 'HTTP错误'}
        
        except Exception as e:
            return {'success': False, 'engine': 'wikipedia', 'error': str(e)}
    
    def _search_duckduckgo(self, query: str) -> dict:
        """DuckDuckGo搜索（HTML抓取）"""
        
        try:
            url = "https://duckduckgo.com/html/"
            
            params = {'q': query}
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取搜索结果
                results = soup.find_all('div', class_='result', limit=3)
                
                if results:
                    result_str = f"✅ DuckDuckGo搜索成功\n找到 {len(results)} 个结果:\n"
                    
                    for i, result in enumerate(results, 1):
                        title_elem = result.find('a', class_='result__a')
                        
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            
                            snippet_elem = result.find('a', class_='result__snippet')
                            
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                            
                            result_str += f"{i}. {title}\n   {snippet[:50]}\n"
                    
                    return {
                        'success': True,
                        'engine': 'duckduckgo',
                        'result': result_str
                    }
                
                else:
                    return {'success': False, 'engine': 'duckduckgo', 'error': '无结果'}
            
            else:
                return {'success': False, 'engine': 'duckduckgo', 'error': 'HTTP错误'}
        
        except Exception as e:
            return {'success': False, 'engine': 'duckduckgo', 'error': str(e)}

# 全局实例
multi_search_engine = MultiSearchEngine()


def multi_search(query: str, engine: str = 'auto') -> str:
    """统一搜索接口（供LLM-Tools调用）"""
    
    result = multi_search_engine.search(query, engine)
    
    if result['success']:
        return result['result']
    
    else:
        return f"❌ 搜索失败: {result.get('error', '未知错误')}"
