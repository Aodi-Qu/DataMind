"""
llm.py — 大模型调用模块
职责：封装 API 调用逻辑，对外暴露一个简单的 chat() 函数
"""
from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


# 初始化客户端（模块级别，只创建一次）
_client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)


def chat(prompt: str, system_prompt: str = "你是一个专业的 SQL 分析师。") -> str:
    """
    发送消息给大模型，返回回复内容。

    参数:
        prompt: 用户的问题（具体要生成什么 SQL）
        system_prompt: 系统角色设定

    返回:
        大模型的回复字符串
    """
    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,  # 生成 SQL 要稳定，温度调低
            max_tokens=1024,
        )
        return response.choices[0].message.content

    except Exception as e:
        # 生产环境中应该记录日志，这里先简单处理
        return f"[错误] 调用大模型失败: {str(e)}"