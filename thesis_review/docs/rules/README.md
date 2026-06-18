# 规则资产目录

本目录是格式审核系统的正式规则资产入口。

## 维护边界

项目中有两套规则资料目录，职责不同：

- `docs/rule/`：人工手动维护区。用于记录人工整理的规范、讨论稿、历史样本索引和临时说明。Agent 不应自动改写这里的内容，除非用户明确指定。
- `thesis_review/docs/rules/`：Agent 维护区。用于存放可被程序加载、测试和校验的结构化规则资产，包括 `rule.yml`、`case.yml` 和样本目录。

本目录属于 Agent 维护区。后续规则落地、拆分、废弃、测试样本绑定，都以本目录为正式结构化入口。

## 目录结构

- `*/rule.yml`：运行时规则元数据，只包含规则编号、标题、严重程度、状态、说明、批注文案和期望值。
- `*/case.yml`：测试样本清单，只用于测试和规则资产校验，不参与生产审核。
- `*/samples/`：真实 Word 样本。

## 维护要求

- 规则编号使用小写英文全词和三位数字，例如 `table-of-contents-title-006`。
- 一个规则编号只代表一个原子检查点。
- `rule.yml` 不包含 `object`、`category`、`scope` 字段。
- `case.yml` 必须写明 `description` 和 `error_description`。
- 已发布的规则编号不能改名、不能复用；不用的规则标记为 `deprecated`。

## 样本维护

Agent 不复制、不生成、不编辑真实 `.docx` 样本。样本文件由维护者手动制作或放置到对应模块的 `samples/` 目录，Agent 只维护样本清单和预期命中规则。

## rule.yml 规则

`rule.yml` 是运行时规则元数据。生产审核只读取 `rule.yml`，不读取 `case.yml`。

必填字段：

| 字段 | 说明 |
|---|---|
| `module` | 模块英文名，必须等于模块目录名，例如 `table-of-contents`。 |
| `module_name` | 模块中文名，例如 `目录`。 |
| `rules` | 当前模块下的原子规则列表。 |
| `id` | 规则唯一编号，使用小写英文全词和三位数字，例如 `table-of-contents-title-006`。发布后不能改名、不能复用。 |
| `title` | 规则短标题，给规则列表和维护者查看。 |
| `severity` | 严重程度，只允许 `error`、`warning`、`info`。 |
| `status` | 规则状态，只允许 `draft`、`active`、`deprecated`。正式审核默认只使用 `active`。 |
| `description` | 给维护者看的详细说明，描述检查对象、判断条件和边界。 |
| `message` | 命中规则时展示给用户的问题文案，用于报告和 Word 批注。 |
| `expected` | 规范要求的正确值，用于报告和 Word 批注。 |

不允许字段：

- `object`
- `category`
- `scope`

规则拆分原则：

```text
一个 rule id = 一个检查对象 + 一个判断条件 + 一条批注文案
```

例如“目录标题格式”不能只写成一条粗规则，应拆成标题文本、字号、字体、居中、行距、标题后空行等原子规则。

## case.yml 规则

`case.yml` 是测试样本清单，只用于测试和规则资产校验，不参与生产审核。

必填字段：

| 字段 | 说明 |
|---|---|
| `cases` | 样本列表。 |
| `id` | 样本唯一编号，建议和主要命中规则相关。 |
| `file` | 样本文件路径，相对当前模块目录，必须指向 `samples/*.docx`。 |
| `description` | 样本整体说明。 |
| `error_description` | 文本描述这个样本错在哪里；无误样本写“无错误，用于验证不误报”。 |
| `expected_rule_ids` | 该样本应该命中的规则编号列表。无误样本写空列表 `[]`。 |

`expected_rule_ids` 中的每个编号必须能在 `rule.yml` 中找到。模块样本通常只填写本模块规则。

## 修改流程

新增或调整规则时，按以下顺序维护：

1. 先在对应模块的 `rule.yml` 增加或修改原子规则。
2. 再在对应模块的 `case.yml` 增加或调整测试样本说明和预期命中规则。
3. 如果需要真实 Word 样本，由维护者手动放入对应模块的 `samples/`。
4. Agent 根据 `rule.yml` 实现或调整代码，规则代码只传 `rule_id`、`actual` 和 `location`，不得硬编码 `message`、`expected`。
5. 运行 catalog、纯 Python 规则测试和 UNO 样本测试。

废弃规则时，不删除旧 `id`，应将 `status` 改为 `deprecated`，并新增替代规则编号。
