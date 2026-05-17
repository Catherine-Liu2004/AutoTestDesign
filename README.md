# AutoTestDesign

> 基于 AI 的自动化测试设计工具 —— 自动运用**等价类划分（EP）**、**边界值分析（BVA）**、**判定表（Decision Table）**、**状态转换（State Transition）**四种测试技术生成测试用例，内置风险分析、测试预言生成与套件优化能力，符合 ISTQB 及 ISO 29119-4 标准。

---

## 环境要求

| 工具 | 版本要求 |
|------|---------|
| Python | 3.11+ |
| Poetry | 2.x |
| Node.js | 18+ |
| npm | 9+ |
| DeepSeek / OpenAI API Key | 必填 |

---

## 安装与启动

### 1. 克隆仓库

```bash
git clone <repo-url>
cd AutoTestDesign
```

### 2. 后端安装与配置

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 API 密钥（默认使用 DeepSeek）
poetry install --with dev
```

`.env` 关键配置项：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | DeepSeek / OpenAI API 密钥（必填） | — |
| `OPENAI_BASE_URL` | API 端点 | `https://api.deepseek.com/v1` |
| `OPENAI_MODEL` | 模型名称 | `deepseek-chat` |
| `DATABASE_URL` | 数据库连接串 | `sqlite:///./autotestdesign.db` |

### 3. 前端安装

```bash
cd ../frontend
npm install
```

### 4. 启动服务

**后端：**
```bash
cd backend
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger API 文档：http://localhost:8000/docs

**前端：**
```bash
cd frontend
npm run dev
```

- 前端页面：http://localhost:5173

### 5. 运行测试

```bash
cd backend
poetry run pytest -v
# 预期：68/68 tests PASSED
```

---

## 功能操作说明

工具分为四个页面，对应完整的测试设计工作流：**Import → Requirements → Test Cases → Export**。

---

## 功能需求（FR）对应操作速查

下表说明每个 FR 在工具的哪个**页面**、点击哪个**按钮**来体现。导航栏从左到右依次为：**Import → Requirements → Test Cases → Export**。

---

### FR 1.0 — 需求导入（Input / Parsing）

**页面：导航栏 → `Import`**

1. 在 **Source Type** 中选择 `Direct Text`（直接输入）/ `CSV` / `TXT File`
2. 在文本框中粘贴需求内容，多条需求之间**用空行分隔**
3. 点击蓝色 **Import** 按钮
4. 右侧显示已导入的需求 ID + 文本预览，确认导入成功

---

### FR 1.1 — 需求结构化（Requirement Structuring）

**页面：导航栏 → `Requirements`**

- **单条解析**：在需求列表 → 找到目标需求行 → 点击 Actions 列第 1 个按钮 **Parse** → AI 提取 Input Fields / Conditions / Expected Actions
- **批量解析**：回到 `Import` 页 → 点击 **Parse All with AI** 按钮 → 一次性解析所有未解析的需求
- **人工校正**：解析完成后，点击 Actions 列第 2 个按钮蓝色 **Structure** → 在对话框中编辑 AI 提取的字段 → 点击 **Save**
- **查看结果**：点击每行左侧 **▶ 展开箭头**，可在展开区域查看完整的结构化内容

---

### FR 2.0 — 风险分析与优先级排序（Risk Analysis）

**页面：导航栏 → `Requirements`**

1. 点击页面顶部工具栏中的黄色 **Analyze Risk (AI)** 按钮
2. AI 为每条需求打分（0–10）并设置优先级（high / medium / low），结果自动填入表格
3. 如需手动调整：直接在表格的 `Risk Score` 和 `Priority` 列编辑 → 点击该行 **Save** 保存
4. 页面顶部统计卡会实时显示高风险需求数量

---

### FR 3.0 — 黑盒测试设计（Black-box Test Design，EP / BVA / Decision Table）

**页面：导航栏 → `Test Cases`**

1. 在顶部配置区，勾选 **Select Requirements** 中的目标需求（可多选）
2. 在 **Techniques** 中勾选测试技术（可同时选多种）：
   - `EP` = 等价类划分
   - `BVA` = 边界值分析
   - `Decision Table` = 判定表
3. 点击 **Generate** 按钮 → 系统生成一个测试套件，列表展示所有用例
4. 每条用例显示：技术类型 Tag、标题、优先级；点击 **▶ 展开**可查看完整输入/预期

---

### FR 4.0 — 白盒测试建模（White-box Modeling，状态转换图）

**分为两步，分别在两个页面体现：**

**第 1 步 — 生成状态图（`Requirements` 页）**

1. 导航栏 → `Requirements`
2. 在需求列表中，找到目标需求行，点击 Actions 列第 3 个按钮 **绿色 Diagram**
   > Actions 列共 4 个按钮顺序：**Parse**（灰）→ **Structure**（蓝）→ **Diagram**（绿）→ **Del**（红）
3. 弹出"State Transition Diagram"对话框，点击 **Generate Diagram (AI)**
4. AI 生成 Mermaid 状态图，对话框中同时显示：图形化渲染 + Mermaid 源码

**第 2 步 — 生成状态转换测试序列（`Test Cases` 页）**

1. 导航栏 → `Test Cases`
2. 在 **Techniques** 中勾选 `State Transition`
3. 点击 **Generate** → 生成基于状态图的测试序列用例

---

### FR 5.0 — 测试预言生成（Test Oracle Generation）

**页面：导航栏 → `Test Cases`**

1. 在测试用例列表中，勾选一条或多条用例左侧的 **复选框**
2. 点击套件信息栏中的 **Generate Oracle (AI)** 按钮
3. AI 为每条选中用例的预期结果生成更详细的验证条件，保存至 `ai_oracle` 字段
4. 展开用例行（点击 **▶**），可在展开区域看到 **AI Oracle** 内容

---

### FR 6.0 — 输出与导出（Export，JSON / Excel / CSV）

**页面：导航栏 → `Export`**

1. 在 **Test Suite** 下拉框中选择要导出的套件（右侧卡片显示套件详情）
2. 在 **Export Format** 中选择格式：`Excel (.xlsx)` / `JSON` / `CSV`
3. 在 **Include Sheets** 中勾选要包含的内容：测试用例 / 风险报告 / 追溯矩阵
4. 点击绿色 **Download Export** 按钮，文件自动下载

---

### FR 7.0 — 测试套件优化（Test Suite Optimization）

**页面：导航栏 → `Test Cases`**

1. 生成测试套件后，套件信息栏显示 Suite ID 和统计数据
2. 点击信息栏中的 **Optimize Suite** 按钮
3. 在弹出的优化对话框中选择优化策略：
   - `Risk-Based`：标记低风险需求对应的低优先级用例（可精简）
   - `Coverage Efficiency`：检测标题或输入数据重复的冗余用例
4. 列表显示被标记为候选删除的用例及原因
5. 勾选要删除的用例 → 点击 **Remove Selected** 批量删除

---

### 页面 1：Import（需求导入）

**访问路径：** 导航栏 → Import

#### 操作步骤

1. 在 **Source Type** 选择导入方式：
   - `Direct Text`：在文本框直接粘贴需求文本
   - `CSV` / `TXT File`：粘贴对应格式的内容
2. 在文本框输入需求内容（多条需求之间**用空行分隔**），例如：
   ```
   用户登录需输入邮箱（格式 xxx@xxx.xx）和密码（8–32位，含字母和数字）。
   连续输入错误密码 5 次后账户锁定 15 分钟。
   
   系统支持文件上传，单文件大小限制 10 MB，支持 JPG / PNG / PDF 格式。
   ```
3. 点击 **Import** 按钮 → 右侧显示已导入的需求列表（ID + 文本预览）。
4. 点击 **Parse All with AI** 按钮 → AI 一次性解析所有需求的结构化信息。

> 导入后需前往 Requirements 页查看和编辑解析结果。

---

### 页面 2：Requirements（需求管理）

**访问路径：** 导航栏 → Requirements

页面顶部展示四格统计卡（总需求数、已解析数、高风险数、已生成状态图数），下方为需求列表。

#### 功能 1：查看需求全文（展开行）

- 点击每行最左侧的 **▶ 展开箭头**，可查看需求完整文本和已解析的结构化字段：
  - `Input Fields`：输入参数及约束
  - `Conditions`：业务规则和触发条件
  - `Expected Actions`：预期行为

#### 功能 2：解析单条需求（Parse）

- 点击操作列的 **Parse** 按钮 → AI 对该需求进行结构化解析，提取输入字段、条件、预期行为。

#### 功能 3：编辑结构化信息（Structure）

- 点击操作列的 **Structure** 按钮（需求已解析后才可用）→ 弹出编辑对话框，可手动修改 AI 提取的结构化字段内容，修改完成后点击 **Save** 保存。

  > 用途：当 AI 解析不准确时，人工校正结构化信息，确保后续测试用例生成的准确性。

#### 功能 4：批量风险分析（Analyze Risk）

- 点击工具栏的 **Analyze Risk (AI)** 按钮 → AI 对所有需求评分（0–10）并设定优先级（high / medium / low）。
- 可在表格中直接编辑 `Risk Score` 和 `Priority` 字段，点击 **Save** 保存人工调整结果。

  > 风险分数越高，后续生成的测试用例覆盖越全面，优先级越高的需求会优先生成。

#### 功能 5：生成状态转换图（Diagram）— FR 4.0

这是白盒测试建模功能的入口，对应作业 **FR 4.0**。

- 在需求列表中，找到目标需求所在行，点击最右侧 **Actions** 列中的绿色 **Diagram** 按钮。
- 弹出"State Transition Diagram"对话框，点击 **Generate Diagram (AI)** 按钮，AI 基于需求描述生成 Mermaid 状态图（`stateDiagram-v2`）。
- 对话框中同时展示：
  - **图形化渲染**：状态节点和迁移箭头可视化展示
  - **原始 Mermaid 代码**：可复制用于文档
- 再次点击 Diagram 按钮时，若已有缓存图则直接展示；点击 **Regenerate** 可重新生成。

  > **找不到按钮？** 需求列表最右侧共有 4 个操作按钮：**Parse**（灰）→ **Structure**（蓝）→ **Diagram**（绿）→ **Del**（红）。Diagram 是第三个。

#### 功能 6：删除需求

- 点击操作列的 **Del** 按钮（红色）→ 确认后删除该需求及其关联数据。

---

### 页面 3：Test Cases（测试用例）

**访问路径：** 导航栏 → Test Cases

页面分为三个区域：顶部生成配置区、中部用例列表区、底部覆盖分析区。

#### 功能 1：生成测试用例

1. 在 **Select Requirements** 复选框中勾选目标需求（可多选）。
2. 在 **Techniques** 中选择测试技术（可多选）：
   - `EP`：等价类划分 —— 有效/无效等价类各取代表值
   - `BVA`：边界值分析 —— 最小值、最大值、边界±1
   - `Decision Table`：判定表 —— 多条件组合的规则覆盖
   - `State Transition`：状态转换 —— 适合有状态流转的功能
3. 可选勾选 **Include Whitebox** 生成额外的语句/分支覆盖用例。
4. 点击 **Generate** 按钮 → 系统生成测试套件并展示所有测试用例。

#### 功能 2：查看用例详情（展开行）

- 点击每行最左侧的 **▶ 展开箭头**，查看完整的：
  - 前置条件（Preconditions）
  - 输入数据（Input Data）
  - 预期结果（Expected Result）
  - AI 测试预言（AI Oracle，生成后显示）

#### 功能 3：编辑单条测试用例

- 点击操作列的 **Edit（铅笔图标）** → 弹出编辑对话框，可修改：标题、前置条件、输入数据、预期结果、优先级、执行状态（pending / pass / fail）。
- 点击 **Save** 保存修改。

#### 功能 4：删除测试用例

- 点击操作列的 **Delete（垃圾桶图标）** → 弹出确认框后删除。

#### 功能 5：AI 测试预言生成（Generate Oracle）

- 选中一条或多条测试用例（勾选复选框）。
- 点击套件信息栏的 **Generate Oracle (AI)** 按钮 → AI 为每条用例的预期结果提供更详细、更精确的测试预言描述，结果保存在 `ai_oracle` 字段中。
- 展开用例行可查看 AI Oracle 内容。

  > 用途：当 AI 生成的预期结果较简短时，使用此功能获取更具体的验证条件，例如具体的 HTTP 状态码、错误消息格式等。

#### 功能 6：套件优化（Optimize Suite）

- 点击套件信息栏的 **Optimize Suite** 按钮 → 弹出优化分析对话框。
- 选择优化策略：
  - `Risk-Based`：标记低风险需求对应的低优先级用例（可考虑精简）
  - `Coverage Efficiency`：检测标题或输入数据重复的冗余用例
- 列表中显示被标记为候选删除的用例和原因。
- 勾选要删除的用例后点击 **Remove Selected** 批量删除。

#### 功能 7：覆盖率追溯矩阵（Traceability Matrix）

- 页面底部 **Coverage & Traceability** 卡片中，点击 **Load Traceability** 按钮 → 展示需求 → 测试用例的对应关系矩阵。
- 可直观看到每条需求被哪些测试用例覆盖，快速发现未被覆盖的需求。

#### 功能 8：更新测试策略（Update Strategy）

- 在 Coverage 卡片中选择新的测试技术组合（可多选），点击 **Update Strategy** 按钮。
- 系统会删除旧的 AI 生成用例，按新策略重新生成（手动添加的用例不受影响）。

#### 功能 9：手动添加测试用例

- 点击工具栏的 **Add Test Case** 按钮 → 填写完整字段（标题、技术类型、前置条件、输入数据、预期结果、优先级）后保存。

---

### 页面 4：Export（导出）

**访问路径：** 导航栏 → Export

1. 在 **Test Suite** 下拉框中选择要导出的测试套件（右侧显示套件详情：用例数、技术、创建时间）。
2. 选择 **Export Format**：
   - `Excel (.xlsx)`：多 Sheet 表格，包含测试用例 + 风险报告 + 追溯矩阵
   - `JSON`：结构化数据，便于与 CI/CD 工具集成
   - `CSV`：简单表格，可导入 Jira / TestRail 等测试管理工具
3. 勾选要包含的内容（**Include Sheets**）：测试用例 / 风险报告 / 追溯矩阵。
4. 点击 **Download Export** 按钮 → 文件自动下载到本地。

---

## 典型完整使用示例

**场景：为"用户登录"功能生成完整测试套件**

```
1. Import 页
   → 粘贴需求：
     "用户登录需输入邮箱（格式：xxx@xxx.xx）和密码（8-32位，含字母和数字）。
      连续输入错误密码 5 次后账户锁定 15 分钟，锁定期间禁止登录尝试。"
   → 点击 Import → 点击 Parse All with AI

2. Requirements 页
   → 展开行查看解析结果（输入字段：邮箱、密码；条件：格式校验、失败计数；预期：锁定）
   → 若 AI 解析有误 → 点击 Structure 按钮手动校正
   → 点击 Analyze Risk (AI) → 需求评分 8/10，优先级 high
   → 点击 Diagram 按钮 → 查看状态图（Idle → Authenticating → LoggedIn / Locked）

3. Test Cases 页
   → 勾选该需求，选择技术：EP + BVA + Decision Table
   → 点击 Generate → 生成约 12–18 条测试用例
   → 展开单条用例查看完整输入/预期
   → 选中所有用例 → 点击 Generate Oracle (AI) → AI 细化预期结果
   → 点击 Optimize Suite → 选 Coverage Efficiency 策略，检查并删除重复用例
   → 在 Coverage 卡片查看追溯矩阵，确认需求被覆盖

4. Export 页
   → 选择该套件，格式选 Excel
   → 勾选：Test Cases + Risk Report + Traceability Matrix
   → 点击 Download Export → 提交 .xlsx 文件给测试团队执行
```

---

## 项目结构

```
AutoTestDesign/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI 路由（requirements / risk / testcases /
│   │   │                 #   export / coverage / whitebox / optimize）
│   │   ├── core/         # 配置、数据库初始化、LLM 客户端
│   │   ├── models/       # SQLAlchemy ORM 数据模型
│   │   ├── schemas/      # Pydantic 请求/响应 Schema
│   │   ├── services/     # 业务逻辑（解析 / 风险 / 生成 / 状态图 /
│   │   │                 #   预言 / 优化）
│   │   └── main.py       # FastAPI 应用入口（注册所有路由）
│   ├── tests/
│   │   ├── test_sprint1.py  # 需求导入、解析（17 tests）
│   │   ├── test_sprint2.py  # 测试用例生成、导出（15 tests）
│   │   ├── test_sprint3.py  # 结构编辑、追溯矩阵、策略（12 tests）
│   │   └── test_sprint4.py  # 状态图、预言、优化（12 tests）
│   ├── .env.example
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/index.js  # 所有 Axios API 调用
│   │   ├── views/
│   │   │   ├── ImportView.vue       # 需求导入页面
│   │   │   ├── RequirementsView.vue # 需求管理 + 风险 + 状态图
│   │   │   ├── TestCasesView.vue    # 用例生成 + 预言 + 优化 + 覆盖
│   │   │   └── ExportView.vue       # 导出页面
│   │   ├── App.vue       # 应用外壳（导航栏）
│   │   └── main.js
│   └── package.json
└── README.md
```

---

## 已知限制

- 暂无用户认证机制，适合单用户本地运行
- LLM 偶尔返回格式异常时工具会自动降级（返回占位符内容）
- 需求数量超过 100 条时，建议分批导入以保证 AI 响应质量


---

## 环境要求

| 工具 | 版本要求 |
|------|---------|
| Python | 3.11+ |
| Poetry | 2.x |
| Node.js | 18+ |
| npm | 9+ |
| OpenAI API Key | 必填 |

---

## 安装步骤

### 1. 克隆仓库

```bash
git clone <repo-url>
cd AutoTestDesign
```

### 2. 后端安装

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，填入你的 OPENAI_API_KEY
poetry install --with dev
```

### 3. 前端安装

```bash
cd ../frontend
npm install
```

---

## 启动应用

### 启动后端服务

```bash
cd backend
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- 接口文档（Swagger UI）：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/health

### 启动前端服务

```bash
cd frontend
npm run dev
```

- 前端页面：http://localhost:5173

---

## 运行测试套件

```bash
cd backend
poetry run pytest -v
```

---

## 环境变量说明

完整选项参见 [backend/.env.example](backend/.env.example)。

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥（必填） | — |
| `OPENAI_MODEL` | 使用的模型 | `gpt-4o` |
| `DATABASE_URL` | SQLite 或 PostgreSQL 连接串 | `sqlite:///./autotestdesign.db` |
| `CORS_ORIGINS` | 允许的前端来源 | `["http://localhost:5173"]` |

---

## 详细使用说明

本工具的完整工作流分为以下六个阶段，每个阶段均可通过前端页面操作，也可直接调用后端 REST API（http://localhost:8000/docs）。

---

### 第一步：导入需求（Import）

访问前端 **导入页面（Import）**，将待测系统的需求描述导入工具。支持三种导入方式：

| 导入方式 | 说明 |
|----------|------|
| **直接输入（direct）** | 在文本框中粘贴或手写需求文本，多条需求以**空行**分隔 |
| **TXT 文件** | 上传纯文本文件，格式同上，多条需求以空行分隔 |
| **CSV 文件** | 上传 CSV 文件，需包含 `description` 或 `requirement` 列；若无这两列，则自动将每行所有字段拼接为一条需求 |

**示例需求文本：**

```
用户登录时需要输入用户名（3-20个字符）和密码（8-32个字符），
密码需包含字母和数字，连续失败5次后锁定账户15分钟。

系统支持文件上传，单文件大小限制为10MB，
支持格式：JPG、PNG、PDF，超出限制应返回友好错误提示。
```

导入成功后，系统会将每条需求存入数据库并返回需求列表（含自动生成的 `id`）。

---

### 第二步：解析需求结构（Parse）

在**需求列表页面（Requirements）**中，选中一条或多条需求，点击 **"解析（Parse）"** 按钮。

AI 会对每条需求进行结构化分析，提取以下信息并保存：

| 提取字段 | 说明 |
|----------|------|
| `input_fields` | 输入参数名称及约束条件（如字段名、数据类型、取值范围） |
| `conditions` | 业务规则与逻辑条件（如"连续失败5次"、"文件 ≤ 10MB"） |
| `expected_actions` | 预期行为与输出（如"锁定账户"、"返回错误提示"） |

解析完成后，你可以在页面中直接查看和编辑已提取的结构化信息，确保 AI 理解正确后再继续。

---

### 第三步：风险分析（Risk Analysis）

在需求列表页面，点击 **"分析风险（Analyze Risk）"** 按钮（可批量分析所有需求，也可单独分析某条）。

AI 会为每条需求打分并分级：

| 字段 | 说明 |
|------|------|
| `risk_score` | 风险评分，范围 0–10（越高越危险） |
| `priority` | 优先级：`high`（高）/ `medium`（中）/ `low`（低） |
| `rationale` | 评分依据说明 |

风险评分可在页面上**手动调整**，以融入领域专家的判断。高风险需求将优先生成更全面的测试用例。

---

### 第四步：生成测试用例（Generate Test Cases）

在**测试用例页面（Test Cases）**，选择需求并配置生成参数：

#### 可选测试技术（可多选）

| 技术名称 | 适用场景 |
|----------|----------|
| `EP`（等价类划分） | 将输入域划分为有效/无效等价类，每类取一个代表值 |
| `BVA`（边界值分析） | 针对边界点（最小值、最大值、边界±1）生成测试 |
| `Decision Table`（判定表） | 多条件组合的业务规则测试，覆盖条件组合矩阵 |
| `State Transition`（状态转换） | 针对有状态流转的功能（如登录锁定、订单状态）生成转换测试 |

#### 白盒测试选项

勾选 **"包含白盒测试（include_whitebox）"** 可额外生成语句覆盖、分支覆盖等白盒测试用例（需配合代码结构信息使用）。

#### 生成结果

系统会返回一个**测试套件（TestSuite）**，包含：
- 套件 ID 和名称
- 所有生成的测试用例列表

每条测试用例包含以下字段：

| 字段 | 说明 |
|------|------|
| `title` | 测试用例标题 |
| `technique` | 所用测试技术（EP / BVA / Decision Table / State Transition） |
| `preconditions` | 前置条件 |
| `input_data` | 输入数据 |
| `expected_result` | 预期结果 |
| `priority` | 用例优先级 |
| `status` | 执行状态：`pending`（待执行）/ `pass`（通过）/ `fail`（失败） |

---

### 第五步：审查与编辑（Review & Edit）

在测试用例页面，可以对 AI 生成的内容进行人工复核：

- **编辑测试用例**：点击任意用例的编辑按钮，修改标题、输入数据、预期结果、优先级或状态
- **删除测试用例**：移除不需要的用例
- **修改风险评分**：返回需求列表页面，手动调整风险分数和优先级
- **追溯矩阵**：可查看需求与测试用例的对应关系（Traceability Matrix），确认每条需求是否有足够的测试覆盖

---

### 第六步：导出（Export）

在**导出页面（Export）**，选择测试套件并指定导出内容和格式：

#### 支持导出格式

| 格式 | 说明 |
|------|------|
| `Excel (.xlsx)` | 标准表格格式，含多个 Sheet（测试用例、风险报告、追溯矩阵） |
| `JSON` | 结构化数据，便于与其他工具集成 |
| `CSV` | 简单表格格式，可直接导入 Excel 或测试管理工具 |

#### 可选导出内容

- `test_cases`：测试用例列表
- `risk_report`：风险分析报告
- `traceability`：需求–用例追溯矩阵

---

## 典型使用场景示例

### 场景：为"用户登录"功能生成测试用例

1. **导入**：在导入页输入以下需求文本：
   ```
   用户登录需输入邮箱（格式：xxx@xxx.xx）和密码（8-32位，含字母和数字）。
   连续输入错误密码5次后，账户锁定15分钟，期间禁止登录尝试。
   ```
2. **解析**：点击解析，AI 提取输入字段（邮箱、密码）、条件（格式校验、失败次数）、预期行为（锁定、禁止登录）
3. **风险分析**：AI 对该需求评分为 8/10（高风险），优先级设为 `high`
4. **生成**：勾选 `EP`、`BVA`、`Decision Table`，点击生成
5. **审查**：检查 AI 生成的边界用例（如密码 7 位/8 位/32 位/33 位）和等价类（有效邮箱/无效邮箱），补充或删除不合理用例
6. **导出**：以 Excel 格式导出，包含测试用例和风险报告，提交给测试团队执行

---

## 项目结构

```
AutoTestDesign/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI 路由层（requirements / risk / testcases / export）
│   │   ├── core/         # 配置、数据库、LLM 客户端
│   │   ├── models/       # SQLAlchemy ORM 数据模型
│   │   ├── schemas/      # Pydantic 请求/响应 Schema
│   │   ├── services/     # 业务逻辑（解析、风险分析、测试用例生成）
│   │   └── main.py       # FastAPI 应用入口
│   ├── tests/            # pytest 测试套件
│   ├── .env.example      # 环境变量模板
│   └── pyproject.toml    # Poetry 依赖配置
├── frontend/
│   ├── src/
│   │   ├── api/          # Axios API 客户端
│   │   ├── views/        # 各功能页面（导入、需求、测试用例、导出）
│   │   ├── App.vue
│   │   └── main.js
│   └── package.json
└── README.md
```

---

## 已知限制

- 暂无用户认证机制，适合单用户本地使用
- LLM 偶尔可能返回无法解析的响应，工具会自动降级处理
- 需求数量超过 50 条时，列表渲染可能稍有延迟
