from dataclasses import dataclass
from typing import Dict, Any
import json

@dataclass
class FamilyStateMatrix:
    family_id: str
    resource_constraints: Dict[str, Any]
    children_profiles: list


class SchoolMatchingEngine:
    """择校匹配引擎"""
    
    def __init__(self):
        self.required_fields = ["geographic_district", "monthly_budget_cap_cny"]
        
    def check_preconditions(self, state: FamilyStateMatrix):
        missing = [f for f in self.required_fields if not state.resource_constraints.get(f)]
        if missing:
            raise PreconditionFailedError(412, f"缺少必要字段: {missing}")
            
    def execute(self, state: FamilyStateMatrix) -> str:
        """核心执行逻辑"""
        self.check_preconditions(state)
        
        # 硬性事实（B层数据）
        facts = f"""## 📋 硬性政策 / 物理事实

1. 海淀区 {state.resource_constraints['geographic_district']} 2026 年对口小学：A 小学、B 小学、C 小学
2. 跨区入学条件：需在目标学区拥有房产并连续居住满 3 年
3. 月度教育预算上限：{state.resource_constraints['monthly_budget_cap_cny']} 元"""
        
        # 逻辑推演（A层方法论）
        reasoning = f"""## 🧠 逻辑推演

- 当前预算可覆盖 A 小学课后班（2,000 元/月） + 学科辅导（3,000 元/月）
- 置换至中关村学区需一次性增加 150 万元房产支出，月供增加 8,000 元
- 建议采用“时间换空间”：先入读 A 小学，3 年后视成绩决定是否跨区"""
        
        # 行动方案
        actions = """## ✅ 可执行行动方案

**本周**：
- 预约 A 小学开放日（联系电话：XXXX）
- 收集万柳学区房价数据（均价 12 万/平米）

**本学期**：
- 每月存 5,000 元作为教育专项基金
- 每季度评估一次孩子学业进展

**本学年**：
- 若孩子成绩保持年级前 20%，可考虑四年级时启动跨区置换"""
        
        return "\n\n".join([facts, reasoning, actions])


class PreconditionFailedError(Exception):
    """412 前置条件失败异常"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"{status_code} – {message}")