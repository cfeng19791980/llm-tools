#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LM Studio Embedding Wrapper
替代 SentenceTransformer，使用 LM Studio 的 embedding API
避免重复加载模型，节省 GPU 资源
"""

import requests
import numpy as np
from typing import List, Union

class LMStudioEmbedding:
    """使用 LM Studio API 的 embedding 类"""
    
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234/v1",
        model: str = "text-embedding-bge-m3",
        timeout: int = 30
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_seq_length = 8192  # BGE-M3 的最大序列长度
        
        # 测试连接
        self._test_connection()
    
    def _test_connection(self):
        """测试 LM Studio API 是否可用"""
        try:
            response = requests.get(
                f"{self.base_url.replace('/v1', '')}/v1/models",
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ LM Studio embedding API connected")
                print(f"  URL: {self.base_url}")
                print(f"  Model: {self.model}")
            else:
                print(f"⚠️ LM Studio API status: {response.status_code}")
        except Exception as e:
            print(f"❌ LM Studio API connection failed: {e}")
    
    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress_bar: bool = False,
        convert_to_numpy: bool = True
    ) -> Union[np.ndarray, List[List[float]]]:
        """
        生成 embedding 向量
        
        Args:
            texts: 单个文本或文本列表
            show_progress_bar: 是否显示进度条（暂不支持）
            convert_to_numpy: 是否转换为 numpy 数组
        
        Returns:
            embedding 向量（numpy 数组或列表）
        """
        # 确保输入是列表
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        
        for text in texts:
            try:
                response = requests.post(
                    f"{self.base_url}/embeddings",
                    json={
                        "model": self.model,
                        "input": text
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # 提取 embedding
                    embedding_data = result['data'][0]['embedding']
                    embeddings.append(embedding_data)
                else:
                    print(f"❌ Embedding request failed: {response.status_code}")
                    # 返回零向量作为 fallback
                    embeddings.append([0.0] * 1024)
                    
            except Exception as e:
                print(f"❌ Embedding error: {e}")
                # 返回零向量作为 fallback
                embeddings.append([0.0] * 1024)
        
        # 转换为 numpy 数组
        if convert_to_numpy:
            return np.array(embeddings, dtype=np.float32)
        else:
            return embeddings
    
    def get_sentence_embedding_dimension(self) -> int:
        """返回 embedding 维度"""
        return 1024  # BGE-M3 的维度
    
    def __repr__(self):
        return f"LMStudioEmbedding(base_url={self.base_url}, model={self.model})"


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("LM Studio Embedding Wrapper Test")
    print("=" * 60)
    
    # 创建 embedding 实例
    embedding = LMStudioEmbedding()
    
    # 测试单个文本
    print("\nTest 1: Single text")
    text = "这是一个测试文本"
    vector = embedding.encode(text)
    print(f"  Input: '{text}'")
    print(f"  Vector shape: {vector.shape}")
    print(f"  Vector dtype: {vector.dtype}")
    print(f"  Vector dim: {embedding.get_sentence_embedding_dimension()}")
    print(f"  First 5 values: {vector[0][:5]}")
    
    # 测试多个文本
    print("\nTest 2: Multiple texts")
    texts = [
        "股票分析系统测试",
        "embedding模型优化",
        "GPU资源节省方案"
    ]
    vectors = embedding.encode(texts)
    print(f"  Inputs: {texts}")
    print(f"  Vector shape: {vectors.shape}")
    print(f"  Vector dtype: {vectors.dtype}")
    
    print("\n" + "=" * 60)
    print("✅ Test Complete")
    print("=" * 60)
    print("Benefits:")
    print("  ✅ No model loading to GPU")
    print("  ✅ Share LM Studio's embedding model")
    print("  ✅ Save GPU memory for Qwen")
    print("=" * 60)