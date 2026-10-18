"""Run three examples without typing Chinese into a terminal."""
import json
from planner import plan

for text in ["把桌面上的红色方块放进左边的盒子。", "把蓝色方块放进盒子", "倒水"]:
    print("\n输入：", text)
    print(json.dumps(plan(text), ensure_ascii=False, indent=2))
