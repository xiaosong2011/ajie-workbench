# ☁️ Supabase 云同步配置指南

## 效果
配置完成后，多人访问同一个工作台链接，输入相同的工作区 ID，就能看到同一份数据。一个人修改，其他人页面自动刷新。

---

## 第一步：注册 Supabase（免费）

1. 打开 https://supabase.com
2. 点击「Start your project」
3. 用 GitHub 账号注册（最快）或邮箱注册
4. 点击「New Project」创建新项目
5. 填写：
   - **Name**：`workbench`（随便写）
   - **Database Password**：设一个密码，记好
   - **Region**：选离你最近的（如 Northeast Asia - Tokyo）
6. 点「Create new project」，等待 1-2 分钟初始化

---

## 第二步：运行建表 SQL

1. 项目创建好后，左侧菜单点「SQL Editor」
2. 点「New query」
3. 把 `supabase-setup.sql` 文件的全部内容粘贴进去
4. 点「Run」执行
5. 看到绿色 ✅ 提示表示成功

---

## 第三步：启用实时订阅

1. 左侧菜单点「Database」→「Replication」
2. 找到 `supabase_realtime` publication
3. 确认 `workbench_data` 表已勾选（如果没有，手动添加）

---

## 第四步：获取 API 密钥

1. 左侧菜单点「Settings」（齿轮图标）
2. 点「API」
3. 复制两个值：
   - **Project URL**：类似 `https://xxxxxxxx.supabase.co`
   - **anon key**：一串很长的 `eyJhbGci...` 开头的字符串

---

## 第五步：在工作台中配置

1. 打开工作台：https://xiaosong2011.github.io/ajie-workbench/
2. 左侧菜单点「💾 数据管理」
3. 在「☁️ 云同步设置」区域填入：
   - **Supabase 项目 URL**：粘贴刚才复制的 URL
   - **Anon Key**：粘贴刚才复制的 key
   - **工作区 ID**：自己取一个名字，如 `ajie-team`
4. 点「☁️ 启用云同步」
5. 看到提示「云同步已启用」就成功了！

---

## 多人共享

告诉你的朋友/同事：
1. 打开同一个工作台链接
2. 进入「数据管理」
3. 填入**相同的** Supabase URL、Key 和工作区 ID
4. 启用后，所有人的数据实时同步

> 工作区 ID 就是"房间号"，相同 ID = 同一份数据，不同 ID = 各自独立

---

## 安全说明

- **anon key** 是公开密钥，设计上可以放在前端代码中
- 但任何人拿到你的 URL + Key + 工作区 ID 都能读写该工作区数据
- 不要在云端存敏感信息（密码、银行卡等）
- 如果需要权限控制，可以在 Supabase 中启用 RLS（Row Level Security）

---

## 故障排查

| 问题 | 解决方案 |
|:---|:---|
| 连接失败 | 检查 URL 和 Key 是否完整复制 |
| 同步不生效 | 检查 Replication 是否启用了 workbench_data 表 |
| 徽章显示红色 | 检查网络连接，或重新输入配置 |
| 数据冲突 | 最后修改的覆盖之前的，建议协调好编辑时间 |
