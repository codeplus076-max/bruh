from typing import List

def get_daily_routine(age: int, severity_score: float) -> List[str]:
    routine = []
    
    routine.append("Hydration: Drink at least 2 liters of safe, clean water spread throughout the day.")
    if age < 12:
        routine.append("Rest: Ensure the child gets 10-12 hours of uninterrupted sleep, plus daytime naps.")
    elif age > 65:
        routine.append("Rest: Aim for 8-9 hours of sleep. Avoid strenuous physical activity.")
    else:
        routine.append("Rest: Aim for 8 hours of sleep. Reduce physical exertion.")

    if severity_score > 1.5:
        routine.append("Monitoring: Check temperature and symptoms every 4-6 hours.")
    else:
        routine.append("Monitoring: Check symptoms each morning and evening to ensure they are improving.")

    routine.append("Nutrition: Eat light, easily digestible meals. Focus on locally available fruits and cooked vegetables.")
    routine.append("Hygiene: Wash hands frequently with soap and water to prevent spreading illness to family members.")

    return routine
