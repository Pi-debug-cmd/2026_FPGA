# 归档说明（2026-10-16 文档整理）

本次整理目标：根目录只留入口文档，去掉重复堆叠的历史状态块。**所有被移动的文件都还在，没有删除任何内容**。

## 目录内容

| 路径 | 内容 | 为什么归档 |
| --- | --- | --- |
| `handoff/` | 每日交接 `handoff_20261012/13/14.md` | 已被 `handoff_20261015.md` 与 [协作记录](../../report/ai_worklog.md) 覆盖，属历史逐日记录 |
| `topics/` | `topic.md`（选题文档） | 候选阶段资料，选题早已确定（见 [project_guide.md](../../project_guide.md)） |
| `team/` | `team_roles.md` | 与 `team_project/team_roles.md` 重复；用户已说明分工由接手方统筹 |
| `状态文档原文/` | 整理前的 `project_guide.md`、`plan.md`、`team_project/project_status.md` 全文 | 三份文档各自堆了约 10 层历史状态块且互相重复；原文留档以便回溯 |

## 路径对照（旧 → 新）

- `handoff_20261012.md` → `交接/归档_md_20261016/handoff/handoff_20261012.md`
- `handoff_20261013.md` → `交接/归档_md_20261016/handoff/handoff_20261013.md`
- `handoff_20261014.md` → `交接/归档_md_20261016/handoff/handoff_20261014.md`
- `topics/topic.md` → `交接/归档_md_20261016/topics/topic.md`
- `team/team_roles.md` → `交接/归档_md_20261016/team/team_roles.md`

`report/ai_worklog.md` 及 `report/` 下历史开发日志里指向 `handoff_2026101x.md` 的链接按上表解析；这些是历史记录，未逐条改写。

## 未归档、仍在一线的文件

`report/` 下的 JSON 报告、原始日志与开发记录属正式证据链（嵌赛要求可复现），一概保留原位；其中日期命名的开发日志（如 `report/world_live_development_20261013.md`）保留供追溯。

要彻底删除归档内容，直接删本目录即可；在此之前不会丢失任何历史。
