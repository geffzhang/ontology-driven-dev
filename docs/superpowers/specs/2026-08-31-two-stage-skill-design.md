# 两阶段技能收敛设计

## 目标

将 ontology-driven-dev 从“需求探索 → 本体建模 → 应用构建”收敛为“需求探索 → 本体建模”。技能的终态是经过一致性校验的七模型 YAML 与 `manifest.json`，不再生成或运行业务应用。

## 范围

- 删除 `techbase/` 下的全部技术底座源码。
- 删除以下构建专用参考文档：
  - `references/本体模型业务功能开发指导书.md`
  - `references/AI 原生应用技术架构设计文档.md`
  - `references/UI-UE界面设计规范.md`
- 更新 `SKILL.md`、`README.md` 和 `README_EN.md`：
  - 将流程、介绍和触发语改为两阶段能力。
  - 将需求探索限定为阶段零至阶段六，移除可选的阶段七 UI 原型。
  - 删除应用构建、仅构建入口、`code-app`、`code-paas`、AI 对话、运行命令、默认账号及构建环境要求。
  - 保留需求规格与七模型 YAML 的产物、门禁、范例和安装方式。

## 不在范围

- 不修改 `reference-example/` 中的需求文档和 YAML 范例。
- 不修改需求探索和本体建模所依赖的两份参考文档。
- 不新增应用构建的替代实现或外部链接。

## 验收

- 仓库不再包含 `techbase/` 和三份指定参考文档。
- `SKILL.md` 及中英文 README 均只描述两阶段流程。
- 对 `SKILL.md`、`README.md`、`README_EN.md` 搜索 `techbase`、`code-app`、`code-paas`、`应用构建`、`App Construction`、`仅构建`、`AI 对话` 等构建术语时无匹配。
- 搜索三份已删除参考文档名时无匹配。
