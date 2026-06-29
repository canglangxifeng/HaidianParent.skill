"""
运行时约束模块 – 实现 Zoo 规格要求的硬性约束
"""
from typing import List
import re


class PreconditionChecker:
    """412 前置条件检查器"""
    
    REQUIRED_FIELDS = {
        "school_matching": ["geographic_district", "monthly_budget_cap_cny"],
        "academic_rca": ["error_logs_rca_summary"],
        "physical_performance": ["height_cm", "weight_kg"],
    }

    def check(self, engine: str, state: dict) -> None:
        """检查引擎所需字段是否存在"""
        required = self.REQUIRED_FIELDS.get(engine, [])
        missing = []
        
        for field in required:
            # 嵌套字段检查简化处理
            if field not in str(state):  # 简化实现
                missing.append(field)
        
        if missing:
            raise PreconditionFailedError(
                status_code=412,
                message=f"缺少必要字段: {missing}",
                required_fields=missing,
            )


class NeutralFilter:
    """中立性情绪过滤器 + Token 熔断"""
    
    BLOCKED_TOKENS = [
        "输在起跑线", "鸡娃", "焦虑", "内卷",
        "别人家的孩子", "再不努力就晚了", "考不上好学校",
        "完了", "没救了", "彻底输了",
    ]
    
    def sanitize(self, text: str) -> str:
        for token in self.BLOCKED_TOKENS:
            if token in text:
                raise TokenMeltdownError(f"检测到禁止词汇: {token}")
        return text


class MarkdownFormatter:
    """Markdown 事实/逻辑分块输出"""
    
    def format(self, facts: str, reasoning: str, actions: str) -> str:
        return f"""## 📋 硬性政策 / 物理事实

{facts}

---

## 🧠 逻辑推演

{reasoning}

---

## ✅ 可执行行动方案

{actions}"""


class PreconditionFailedError(Exception):
    def __init__(self, status_code: int, message: str, required_fields: list):
        self.status_code = status_code
        self.message = message
        self.required_fields = required_fields
        super().__init__(f"{status_code} – {message}")


class TokenMeltdownError(Exception):
    """Token 熔断异常"""
    pass