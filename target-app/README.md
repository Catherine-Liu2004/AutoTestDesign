# TodoApp — Target Application

> 一个轻量级 **Flask RESTful API** 任务管理系统，作为 AutoTestDesign 工具的待测目标应用。  
> 内置丰富的业务规则，覆盖等价划分（EP）、边界值分析（BVA）、决策表、状态转换等全部测试技术。

---

## 系统架构

```
target-app/
├── app.py           # Flask 工厂函数 + 全部路由
├── models.py        # SQLAlchemy 数据模型（User / Task）
├── config.py        # 配置类（Config / TestConfig）
├── requirements.txt # 依赖包
└── README.md
```

---

## 环境要求

| 工具 | 版本 |
|------|------|
| Python | 3.11+ |
| pip | 23+ |

---

## 安装与启动

```bash
cd target-app

# 1. 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务（默认 http://127.0.0.1:5000）
python app.py
```

---

## API 端点总览

| 方法   | 路径                            | 说明                | 认证  |
|--------|---------------------------------|---------------------|-------|
| GET    | `/api/health`                   | 服务健康检查        | 否    |
| POST   | `/api/auth/register`            | 注册新用户          | 否    |
| POST   | `/api/auth/login`               | 登录，返回 JWT      | 否    |
| GET    | `/api/auth/me`                  | 当前用户信息        | 是    |
| GET    | `/api/tasks`                    | 获取任务列表        | 是    |
| POST   | `/api/tasks`                    | 创建任务            | 是    |
| GET    | `/api/tasks/<id>`               | 获取单个任务        | 是    |
| PUT    | `/api/tasks/<id>`               | 更新任务字段        | 是    |
| DELETE | `/api/tasks/<id>`               | 删除任务            | 是    |
| PATCH  | `/api/tasks/<id>/status`        | 变更任务状态        | 是    |
| GET    | `/api/tasks/export?format=json` | 导出任务（JSON）    | 是    |
| GET    | `/api/tasks/export?format=csv`  | 导出任务（CSV）     | 是    |

认证方式：`Authorization: Bearer <token>`

---

## 业务规则（测试设计依据）

### 用户注册/登录

| 字段     | 规则                                      | EP 分类                            |
|----------|-------------------------------------------|------------------------------------|
| username | 4–20 字符，`[a-zA-Z0-9_]+`              | 有效 / 过短(<4) / 过长(>20) / 非法字符 |
| password | 8–32 字符                                 | 有效 / 过短(<8) / 过长(>32)        |

### 登录锁定（决策表）

| 连续失败次数 | 账户状态    | 登录响应    |
|--------------|-------------|-------------|
| 0–4          | 正常        | 401 Invalid |
| 第 5 次失败  | **锁定 15 分钟** | 423 Locked |
| 锁定中       | 已锁定      | 423 Locked（含剩余分钟数）|
| 成功登录     | 重置计数    | 200 OK      |

### 任务字段

| 字段        | 规则                             | BVA 边界点             |
|-------------|----------------------------------|------------------------|
| title       | 1–100 字符（必填）               | 0, 1, 2, 99, 100, 101  |
| description | 0–500 字符（可选）               | 0, 1, 499, 500, 501    |
| priority    | `low` / `medium` / `high`        | EP: 3 有效类 + 1 无效类 |
| due_date    | YYYY-MM-DD，创建时不可为过去日期 | 昨天, 今天, 明天        |
| 任务上限    | 每用户最多 100 条                | 99, 100, 101           |

### 任务状态转换（FSM）

```
         ┌─────────────┐
         │   pending   │────────────────────────┐
         └──────┬──────┘                        │
                │ start work                    │ cancel
                ▼                               │
       ┌────────────────┐                       │
       │  in_progress   │──── pause ────►pending│
       └────────┬───────┘                       │
                │ finish          abandon        │
                ▼                    │           │
        ┌───────────────┐            ▼           ▼
        │   completed   │──────► archived ◄──────┘
        └───────────────┘        (终止态)
```

**允许的转换（6 条）：**

| 当前状态    | 目标状态    | 动作     |
|-------------|-------------|----------|
| pending     | in_progress | 开始工作 |
| pending     | archived    | 取消任务 |
| in_progress | completed   | 完成任务 |
| in_progress | pending     | 暂停/重置|
| in_progress | archived    | 放弃任务 |
| completed   | archived    | 归档完成 |

**禁止的转换（测试负面用例）：**  
`completed → pending`、`completed → in_progress`、`archived → *`（任意）

---

## 快速测试示例

```bash
# 注册
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test1234"}'

# 登录
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test1234"}'

# 创建任务（TOKEN 替换为登录返回值）
curl -X POST http://127.0.0.1:5000/api/tasks \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"My first task","priority":"high","due_date":"2026-12-31"}'

# 状态转换
curl -X PATCH http://127.0.0.1:5000/api/tasks/1/status \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}'
```
