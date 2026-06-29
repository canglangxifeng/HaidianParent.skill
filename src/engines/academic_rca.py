from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ErrorLogsRCA:
    concept_confusion: int = 0
    careless_mistake: int = 0
    reading_comprehension_error: int = 0


class AcademicRCAEngine:
    """学科审计错题 RCA 引擎"""
    
    def __init__(self):
        self.habit_threshold = 0.6
    
    def calculate_habit_ratio(self, rca: ErrorLogsRCA) -> float:
        total = rca.concept_confusion + rca.careless_mistake + rca.reading_comprehension_error
        if total == 0:
            return 0.0
        return rca.careless_mistake / total
    
    def determine_action(self, rca: ErrorLogsRCA) -> str:
        """RCA 决策矩阵"""
        habit_ratio = self.calculate_habit_ratio(rca)
        
        if habit_ratio > self.habit_threshold:
            return "HABIT_CORRECTION"
        elif rca.concept_confusion >= rca.reading_comprehension_error:
            return "REMEDIATE_CONCEPT"
        else:
            return "READING_DRILL"
    
    def execute(self, child_name: str, rca: ErrorLogsRCA) -> str:
        # 硬性事实
        facts = f"""## 📋 硬性事实
- 概念混淆错误数：{rca.concept_confusion}
- 习惯粗心错误数：{rca.careless_mistake}
- 阅读理解错误数：{rca.reading_comprehension_error}
- 习惯粗心占比：{self.calculate_habit_ratio(rca):.1%}"""
        
        # 逻辑推演
        action = self.determine_action(rca)
        reasoning = f"""## 🧠 逻辑推演
- 习惯粗心占比{'超过' if self.calculate_habit_ratio(rca) > self.habit_threshold else '未超过'} 60% 阈值
- RCA 结论：{action}
- **禁止模糊安慰**：不得输出“没关系下次努力”"""
        
        # 行动方案
        if action == "HABIT_CORRECTION":
            actions = """## ✅ 可执行行动方案
1. **立即降低题目难度**，专注注意力训练
2. 每日 10 分钟“慢速检查”练习
3. 使用错题本记录粗心模式
4. **不增加题目难度**直到习惯纠正完成"""
        elif action == "REMEDIATE_CONCEPT":
            actions = """## ✅ 可执行行动方案
1. 调用 question_bank_router.json 获取概念讲解视频
2. 安排 3 次专项练习
3. 每周一次概念巩固测试"""
        else:
            actions = """## ✅ 可执行行动方案
1. 阅读理解专项训练（每日 1 篇）
2. 关键词标注练习
3. 口头复述训练"""
        
        return "\n\n".join([facts, reasoning, actions])