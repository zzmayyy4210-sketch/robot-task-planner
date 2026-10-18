# Robot Task Planner · 机器人任务解析与验证

[![Python tests](https://github.com/zzmayyy4210-sketch/robot-task-planner/actions/workflows/tests.yml/badge.svg)](https://github.com/zzmayyy4210-sketch/robot-task-planner/actions/workflows/tests.yml)

**一句话介绍：输入中文搬运任务，输出结构化 JSON；信息不全就追问，异常指令就拒绝。**

| 项目能力 | 当前实现 |
| --- | --- |
| 自然语言输入 | 支持限定中文句式 |
| 结构校验 | Pydantic 枚举和额外字段检查 |
| 缺失信息 | 生成追问，暂停计划生成 |
| 任务计划 | 生成 5 个描述性步骤 |
| 异常记录 | 本地 JSONL 日志 |
| 质量验证 | 单元测试、12 条回归样本、GitHub Actions |

[演示说明](docs/DEMO.md) · [核心代码](planner.py) · [测试](tests/test_planner.py)

## 从 GitHub 下载并运行

```powershell
git clone https://github.com/zzmayyy4210-sketch/robot-task-planner.git
cd robot-task-planner
```

没有 Git 也可以点击 Code → Download ZIP，解压后在文件夹打开终端。

将中文搬运指令转成经过 Pydantic 校验的结构化任务，识别缺失字段，并生成供人查看的执行步骤。

**当前版本是规则模拟解析器，不使用大模型、不控制机器人。** 它用于学习任务解析与验证的完整流程，不能宣称具备任意自然语言理解能力。

## 快速开始

需要 Python 3.10+。在本项目文件夹打开终端：

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python planner.py "把桌面上的红色方块放进左边的盒子。"
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python planner.py --evaluate data/samples.json
```

macOS/Linux 使用 `.venv/bin/python` 替代 `.venv\Scripts\python`。

## 一键演示

```powershell
.venv\Scripts\python -X utf8 demo.py
```

依次演示成功解析、缺失信息追问、不支持任务拒绝。

## 示例输入与输出

输入 `把桌面上的红色方块放进左边的盒子。`，输出的关键字段：

```json
{
  "action": "pick_and_place",
  "object": "red_block",
  "target": "left_box",
  "needs_clarification": false,
  "status": "ready"
}
```

完整输出还包含 `questions`、`error` 和五个描述性步骤。

输入 `把红色方块放进盒子` 时，输出 `status: clarification`，追问“放进哪个盒子：左边还是右边？”，且不生成步骤。当前追问是单轮提示：用户需要重新输入完整指令，例如 `把红色方块放进右边的盒子`；尚未实现多轮会话状态。

## 支持范围

- 动作：一次 pick_and_place。
- 物体：红色方块、蓝色方块、绿色方块；泛称“方块”触发追问。
- 目标：左边的盒子、右边的盒子；泛称“盒子”触发追问。
- 句式：`[请]把[桌面上的]<物体>放进<目标>[。或！]`。
- 不符合句式、未知物体、否定、复合任务均拒绝；空输入和超过 500 字的输入视为无效。

这是一份有限词表。自然语言中的同义词、位置关系和复杂语义留给后续模型版本处理。

## 代码怎么读

1. `Task`：定义动作、物体和目标的合法值，禁止额外字段。
2. `mock_parse()`：用有限句式模拟解析，未来替换为模型调用。
3. `validate_candidate()`：对原始 JSON 做结构校验，未来模型输出也必须经过这里。
4. `plan()`：检查输入、决定追问或生成步骤。
5. `evaluate()`：对样本的预期字段做比较并统计错误类型。
6. `main()`：命令行入口，将输入、结果和 UTC 时间写入 `logs/events.jsonl`。

日志只保存在本地，可能含用户输入，已被 Git 忽略。项目不需要任何 API 密钥；未来密钥通过环境变量提供，不要写进代码。

## 评估指标

`data/samples.json` 包含 12 个教学样本，包括正常任务、缺失字段和异常输入。

- `expected_behavior_accuracy`：输出是否符合样本指定的预期字段；正确追问和正确拒绝也计为正确行为。
- `ready_rate`：能直接生成计划的样本比例，不等于整体理解准确率。
- `error_types`：统计 missing_fields、unsupported_input、invalid_input。

这些样本与规则一同编写，属于回归检查。它们不能证明在真实用户指令上的泛化表现。接入模型后应另外收集独立测试集，并比较字段准确率、错误拒绝率、遗漏追问率、延迟和成本。

## 建议学习顺序

1. 运行三个例子：完整任务、缺少目标、不支持的任务；逐行阅读 `plan()`。
2. 自己增加“黄色方块”：同时修改字段枚举、词表、句式和测试，理解验证约束。
3. 增加独立的测试语句，观察规则法的局限。
4. 写一个模型解析适配器，返回相同的 `Task`；保留本地校验，补充超时、重试和错误日志。
5. 增加会话状态，让“右边的盒子”能补全上一轮任务；防止旧字段串到新任务。
6. 最后才接仿真，加入场景物体 ID、可达性、碰撞检测、执行反馈。

当前 `ready` 只表示字段完整且属于允许词表，不证明物体真实存在、动作安全或任务可执行。执行步骤也只是模板文字。

## 简历描述示例

“实现面向机器人搬运任务的中文指令解析与验证原型，使用 Pydantic 约束任务结构，实现缺失字段追问、异常日志及样本评估；当前使用规则模拟解析，尚未接入大模型或机器人执行系统。”

## 项目文件

```text
robot-task-planner/
  planner.py                 # 解析、校验、计划、日志和评估
  demo.py                    # 三个可直接运行的演示
  requirements.txt           # Python 依赖
  data/samples.json          # 12 条回归样本
  tests/test_planner.py      # 自动化测试
  docs/DEMO.md               # 演示与编码说明
  .github/workflows/tests.yml # GitHub 自动测试
```

## 当前验收结果

本地 5 项单元测试通过；12 条教学样本预期行为匹配率为 100%，直接生成计划比例为 25%。其余样本用于验证追问和拒绝，不能将这组指标解释成通用语言理解能力。
