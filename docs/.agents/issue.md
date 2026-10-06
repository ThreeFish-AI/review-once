# Issue 台账

## RSI-001 `review-once` 缺少可收敛的 Review-Fix 闭环

**日期**：2026-10-04

**问题描述**：用户需要反复执行“Review 当前 workspace → 发现缺陷 → 直接修复 → 再 Review”，不再依赖人工反复点击 Review 和 Fix；该过程同时需要适配 Conductor 和无 Conductor 的普通 Git workspace。

**表因与根因**：一次性 Review 结果与工作区修复之间没有统一状态机；Conductor 的 Diff、Comments 和 Checks 能力也不能直接假设存在于所有 Runtime。若没有明确的 Finding 判定、重新取证和停止条件，循环容易变成重复评论、无效重构或无限运行。

**处理方式**：新增 `review-once` Portable Skill，使用一个 Skill 加两个 Mode 路由；以 [Review Contract](../../references/review-contract.md) 约束 Finding 的证据和唯一性，以 [Conductor Mode](../../references/conductor-mode.md) 与 [Git Mode](../../references/git-mode.md) 分离工具边界；默认最多 8 轮，并在重复 Finding、连续无进展、工具/验证阻塞或产品决策不足时停止。

**后续防范**：后续新增自动化脚本前，先证明操作顺序、权限边界或校验逻辑确实需要确定性执行；所有新增 Mode 必须补充 output eval、trigger eval 和失败路径；不得将用户凭证、Review 私有内容或平台内部状态写入仓库。

**同类问题影响与注意事项**：凡是“自动循环直到通过”的 Agent workflow，都必须同时定义成功状态、阻塞状态、有界停止和证据报告；“没有新发现”与“工具不可用”不是同一种结果，不能混写为已通过。

## RSI-002 Trigger eval Runner 的正例证据不足

**日期**：2026-10-04

**问题描述**：官方 `run_eval.py` 在本机对 24 条 Trigger query 执行单次 smoke 时得到 12/24；12 条负例通过，12 条正例均未记录触发。该结果不能直接证明 Description 不触发，因为单 query trace 已确认临时 Skill 命令被加载，但 Runner 未观察到 `Skill` tool invocation。

**表因与根因**：Trigger Runner 的判定依赖模型在短超时窗口内显式调用临时 Skill/Read 工具；当前 Runtime 使用的模型与命令发现路径会先读取 `Review request.md`，不一定调用临时命令名，导致自然语言正例出现 false negative。

**处理方式**：保留官方数组格式的 24 条 query、负例边界和本机 smoke 输出；不把 12/24 宣称为通过。以 `quick_validate.py`、`jq`、单 query trace 和后续真实宿主验证作为补充证据，并在评测文档中明确该限制。

**后续防范**：在支持原生 Skill loader 的 Runtime 中重复运行 Trigger eval；同时保留显式 `/review-once` / `$review-once` 调用样例，区分“Description 触发能力”和“Runner 是否观察到工具调用”。

**同类问题影响与注意事项**：任何依赖模型主动调用工具的 eval 都必须记录 Runtime、模型、超时、命令发现方式和工具事件；没有事件证据时只能标记“未验证”，不能把 false negative 当作 Skill 逻辑缺陷。

## RSI-003 发布前独立 Review 发现的契约漂移

**日期**：2026-10-04

**问题描述**：发布前独立 Review 发现 Archify workflow 曾将 Verify 直接连接到终态，重复 Finding eval 曾把行位置隐含为身份字段，Trigger eval 指南曾与官方 Runner 的 threshold 判定不一致。

**表因与根因**：视觉资产、行为评测和运行契约分别演进，缺少一次跨资产的发布前交叉核对。

**处理方式**：使用 Archify Lifecycle 表达 `Verify → Review/Re-review → 终态` 的语义路径，避免 Workflow 布局中的脆弱回环路由；将 Finding 断言改为规范化路径、失败模式/根因和触发场景；将 Trigger 指南同步为官方 Runner 的 `>= 0.5` / `< 0.5` 判定。

**后续防范**：发布前同时审查运行时主循环、评测断言和可视化资产；任何图表只能作为说明，不得改变运行契约的状态机语义。

**同类问题影响与注意事项**：视觉图、eval 和 runtime reference 出现同一概念时，只允许引用同一事实源；若图表为可读性做拓扑简化，必须保持所有关键状态转移可追踪。

## RSI-004 合并前外部 Review 发现的三项工具链漂移

**日期**：2026-10-05

**问题描述**：对 PR #1 的独立深度 Review 发现三项非阻塞缺陷：`evals/evals.json` 的字段名 `assertions` 与官方 skill-creator `references/schemas.md` 定义的 `expectations` 漂移（并附加非 schema 字段 `mode`）；README 两条安装命令硬编码 `--branch feat/review-once`，合并后分支删除即失效；[Review Contract](../../references/review-contract.md) 状态机首节点 `DISCOVER` 在 SKILL.md 主循环中无对应术语。

**表因与根因**：evals.json 官方仓库自身也存在命名漂移（其 SKILL.md 叙述称 assertions、schemas.md 示例用 expectations），且 `jq`/`quick_validate.py` 均不校验该文件，漂移被本地校验绿灯掩盖；安装命令在 PR 阶段编写，缺少“合并后时效”视角；状态机为图示性命名，未与运行时主循环的词汇表对齐。

**处理方式**：`assertions` 全部更名为 `expectations`，`mode` 在 [evals/README.md](../../evals/README.md) 明示为项目扩展；安装命令改为 `--branch main`（合并后即刻生效，当时的安装节说明保持解释合并时序）；状态机首节点更名为 `BASELINE` 并标注对应主循环步骤 1–2。

**后续防范**：接入官方 skill-creator 工具链的字段以 `references/schemas.md` 为准，而不是官方文档叙述；任何硬编码分支名的面向用户命令都必须回答“该 Ref 在合并后是否仍存在”；跨文件共享的图示节点名必须能在运行时文档中检索到同词汇。

**同类问题影响与注意事项**：与 RSI-003 同属“多资产各自演进导致的漂移”，但此次漂移源部分来自上游（官方仓库内部不一致）；引用上游 schema 时应同时记录核验日期与具体文件，上游漂移不能自动豁免本仓库的一致性义务。

## RSI-005 评测文档覆盖声明与 Trigger 数据漂移

**日期**：2026-10-05

**问题描述**：外部 Review 发现 [evals/README.md](../../evals/README.md) 两处声明与数据不符：trigger-evals 实为“正负各半”（id 8、9 为连续两条负例），却被描述为“正负交替”；覆盖声明列出“发布 Release”，但当时 24 条 query 中无 Release 形态负例，导致 SKILL.md 触发边界中该项未被评测验证。

**表因与根因**：描述性声明沿用最初的数据组织方式，trigger 数据增删后未回查文档；覆盖清单按 SKILL.md 边界逐项抄写，但缺少“声明 ↔ 数据条目”的核对步骤。

**处理方式**：“正负交替”改为按数据陈述“共 25 条（12 正 / 13 负）”；新增 id 25 Release 形态负例（复用“变更/Review”词汇构造 collision case），并在 smoke 记录中标注该条晚于 2026-10-04 smoke 加入。

**后续防范**：评测文档中的数量、极性比例与覆盖清单必须与数据文件同批修改、同批校验；覆盖类声明逐条对应数据条目核对，不凭记忆抄写。

**同类问题影响与注意事项**：与 RSI-003、RSI-004 同属“多资产各自演进导致的漂移”，差异在于漂移源是本仓库内部的数据演进而非上游；凡“汇总类描述”（数量、比例、清单）都应视为可漂移资产，改动数据时同批回查。

## RSI-006 自审收敛与人工 Review 结论不一致（假收敛）

**日期**：2026-10-05

**问题描述**：在 to-video/nassau 对同一 Diff 连续两次执行 review-once，两次均报告「已收敛」；随后人工 Review 仍连续发现 4 个新 Issue：① 上一轮修复自身引入的缺陷（豁免按列表末位而非时间轴末位）；② 行为收窄后 docstring/模块头/注释未同步；③ 与同文件已有 `js_round` 重复的舍入实现；④ 两个模块各持一份 CLI 解析规则（split-brain）。

**表因与根因**：表因是循环在自审无 Finding 后即宣布收敛。根因是两条契约缺陷相互放大：(1) 独立 reviewer 仅「有能力时可选」，且第二次运行中独立 Subagent 只参与了发现 Finding 的轮次，宣布收敛的最后一轮仍由修复者自审，对自己刚写的修复天然失明；(2) 收敛谓词在六条件过滤门下由循环自评，`Fix-worthy: 原作者会修复` 在自动循环中自引用（作者即判定者），且缺少镜头覆盖下限，SSOT/契约同步类问题无镜头负责，还因 Provable 未界定契约类证据而易被过滤。[调研文档 §2.2](../research/2026-10-04-review-once-progressive-loop-research.md#22-三轮缺陷与闭环价值) 已记录 PR #33 中独立盲扫才抓到残余缺陷，但该教训未结晶为硬规则。

**处理方式**：[SKILL.md](../../SKILL.md) 新增收敛门——宣布收敛前须经 fresh-context 独立 reviewer 按[盲审信息包](../../references/review-contract.md#盲审信息包)复审，无法委派时降级为「自审收敛」并披露；新增四[审查镜头](../../references/review-contract.md#审查镜头)覆盖下限；Fix-worthy 改为「严格 PR reviewer 会要求修改」；同根因须两次不同方向修复后才停止；收敛 Review 之后任何改动使结论作废。同批更新状态机、两个 Mode 文档、evals（新增 id 9、10、11，修订 id 1、2、3、4、5、7）、agents/openai.yaml、README、图示资产（新增「自审收敛」终态节点）。修订后以新规则对自身做了一次独立盲审，又发现 11 项（含 2 项会让停止条件失效的 P2：无法委派时「连续两轮无进展」永不触发；新旧重复 Finding 规则与 eval 5 互相矛盾），均已在交付前修复；第二次盲审仍发现 9 项（P2×3、P3×6），根源同为“新增条款之间的缝隙”：修复 Delta 在未提交工作区里取不到（改为首次修改前仓库外快照 + `git diff --no-index`）、换方向重修与无进展计数没有优先级、误报分支被迫改自认正确的代码（新增误报复核与 `DISPUTED` 状态）。第三次盲审发现 9 项（P2×2、P3×7）：误报复核只写进 SKILL.md 与 Contract 而未同步两个 Mode 文档、图示、Fingerprint 状态集；快照方法在同名文件（须按相对路径镜像存放）和删除文件（须以 `/dev/null` 作右侧）两种边界下产出错误 Delta。这再次证明修改契约本身也必须过收敛门，且每次改动后的复审都会暴露上一次修复的缝隙；P2 数量 2→3→2→2→0→0；第四轮的 2 项 P2 仍在新写的快照机制上（Agent 新建文件在后续轮被误快照为基线、清理时机排在最终报告之后而不可执行），均已实测复现并修复；第五轮快照配方经 7 类边界情形实测全部吻合，仅余 2 项一句话级 P3（issue.md 变更清单与数据不符、三处快照入口缺「BASELINE 时已存在」限定词），已修复；第六轮（收敛门）四镜头全查，仅余 1 项 P3（`cp -n` 退出码的平台差异被写成普遍事实），已改为跨平台措辞。

**后续防范**：凡「循环自行宣布成功」的 Agent workflow，成功判定主体必须独立于被判定的产出者；教训类结论（调研文档中的案例）必须同批落实为可检查的契约条款，而不是停留在叙述；评审镜头应按漏网缺陷的类别反推，而不是只枚举「行为是否正确」。

**同类问题影响与注意事项**：与 RSI-001 的「没有 Finding」不等于「已通过」同源，但这次的缺口在判定主体而非判定标准。注意独立复审也有成本与能力边界：降级路径必须诚实标注「自审收敛」，不能让报告措辞把两种收敛等同；盲审信息包不得夹带 Finding 历史，否则 reviewer 会被锚定而退化为复核旧问题。

## RSI-007 图示资产缺 BLOCKED 独立终态与 DISPUTED 转移链（结构性梳理发现）

**日期**：2026-10-06

**问题描述**：对全仓执行结构性梳理清减（preening-substrate）时发现：Lifecycle 图示资产（candidate.json 与 HTML）把 BLOCKED 折叠进「有界停止」sublabel（无独立终态节点），DISPUTED 的恢复转移（→收敛门）在图上断链，BASELINE 建基环节亦不可见——与契约 11 态、交付格式四选一终态及 eval id 6 断言不一致。

**表因与根因**：表因是图示从第一版（PR #1 同批）起就缺这些状态。根因是 RSI-003「拓扑简化必须保持所有关键状态转移可追踪」规则与 BLOCKED 折叠同日同 PR 诞生，但从未回溯适用于其诞生 commit 自身的资产；有记录的同步（RSI-006）只覆盖 self_reviewed 节点新增与「争议」词条文案级修补，无记录的表示法漂移持续存活于六轮盲审之下。

**处理方式**：candidate.json 新增 `blocked` 终态节点（两条代表性入边：verify→blocked「验证失败且与本轮无关」、review→blocked「工具 / 权限 / 决策不足（任何状态可触发）」）与 `disputed` 中间态节点（两条出边：→converged「未再报出 → 按其余结果收敛」、→bounded「再次报出 → 交用户裁决」）；「阻塞」「争议」移出 bounded sublabel；开始节点 sublabel 补「建立基线 BASELINE」；卡片改写并注明「收敛门完整出边以 review-contract.md 状态机为准」；HTML 经 archify finalize（validate/deliver/check/browser-check 四门）再生，未手改。护栏升级：状态词汇登记表断言（终态集=契约四终态、DISPUTED 双出边可追踪、HTML 与 candidate 节点集零漂移）固化为仓库内被跟踪的校验器 [tests/run_all.sh](../../tests/run_all.sh)（evals schema、Markdown 链接锚点、状态词汇矩阵、`git diff --check` 四门），防第七次同类漂移。

**后续防范**（扩展 RSI-003，并将 RSI-003 回溯适用于其诞生 commit 自身的资产）：**契约状态机的每个终态与中间态，要么出现在图示拓扑中，要么出现在图示的显式简化免责声明中**；CONVERGENCE_GATE 以边标签表示属可辩护简化（契约自注非终态），但此类简化决定必须留档。图示资产只准经 candidate.json → archify 流水线再生，严禁手改 HTML 造成 candidate↔html split-brain。

**同类问题影响与注意事项**：与 RSI-003/004/005 同属「多资产各自演进漂移」，本次特殊之处是漂移与防范规则同批诞生、规则从未自检。凡「简化免责」类决定（折叠节点、省略转移）都应视为可漂移资产：要么显式留档，要么机械断言护栏化；不能依赖「下次有人记得」。
