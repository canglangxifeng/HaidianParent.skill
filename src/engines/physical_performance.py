# PhysicalPerformanceEngine 体育膳食引擎

from dataclasses import dataclass

@dataclass
class PhysicalData:
    height_cm: float
    weight_kg: float
    cardio_endurance_score: float
    age: int
    gender: str


class PhysicalPerformanceEngine:
    """体育膳食引擎"""

    def __init__(self):
        self.national_standard_2026 = {
            10: {"height_range": (135, 145), "weight_range": (30, 40), "cardio_min": 75},
            11: {"height_range": (140, 150), "weight_range": (33, 43), "cardio_min": 78},
            12: {"height_range": (145, 155), "weight_range": (36, 46), "cardio_min": 80},
        }

    def calculate_bmi(self, data: PhysicalData) -> float:
        return data.weight_kg / ((data.height_cm / 100) ** 2)

    def assess_gap(self, data: PhysicalData) -> dict:
        """逆向工程推演差距"""
        standard = self.national_standard_2026.get(data.age, {})
        bmi = self.calculate_bmi(data)

        return {
            "height_gap_cm": max(0, standard.get("height_range", (0, 0))[0] - data.height_cm),
            "weight_gap_kg": max(0, standard.get("weight_range", (0, 0))[0] - data.weight_kg),
            "cardio_gap": max(0, standard.get("cardio_min", 0) - data.cardio_endurance_score),
            "bmi": bmi,
        }

    def generate_diet_plan(self, data: PhysicalData, gap: dict) -> str:
        """膳食配给：碳水:蛋白质:脂肪 = 55%:20%:25%"""
        total_calories = 1800 + (gap["cardio_gap"] * 50)  # 基础热量 + 训练补充
        carb_g = int(total_calories * 0.55 / 4)
        protein_g = int(total_calories * 0.20 / 4)
        fat_g = int(total_calories * 0.25 / 9)

        return f"""碳水 {carb_g}g，蛋白质 {protein_g}g，脂肪 {fat_g}g，总计 {total_calories} kcal"""

    def execute(self, data: PhysicalData) -> str:
        # 硬性事实
        gap = self.assess_gap(data)
        facts = f"""## 📋 硬性事实
- 身高：{data.height_cm} cm（标准 {self.national_standard_2026[data.age]['height_range'][0]}-{self.national_standard_2026[data.age]['height_range'][1]} cm）
- 体重：{data.weight_kg} kg（标准 {self.national_standard_2026[data.age]['weight_range'][0]}-{self.national_standard_2026[data.age]['weight_range'][1]} kg）
- 心肺耐力分数：{data.cardio_endurance_score}（标准 ≥ {self.national_standard_2026[data.age]['cardio_min']}）
- BMI：{gap['bmi']:.1f}"""

        # 逻辑推演
        reasoning = f"""## 🧠 逻辑推演
- 当前体能 → 中考达标差距：{gap['cardio_gap']} 分
- 分阶段训练计划：第1周基础有氧，第2-4周间歇训练
- 物理做功消耗估算：{(gap['cardio_gap'] * 300):.0f} kcal/周"""

        # 行动方案
        diet_plan = self.generate_diet_plan(data, gap)
        actions = f"""## ✅ 可执行行动方案
**本周训练**：
1. 每日跳绳 10 分钟（心率维持 140-150）
2. 周末 30 分钟慢跑

**膳食配给**：
{diet_plan}

**检查节点**：
- 第 2 周测量心肺耐力
- 第 4 周评估中考体育达标率（目标 85%+）"""

        return "\n\n".join([facts, reasoning, actions])