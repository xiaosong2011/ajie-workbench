# 📖 GitHub 上传 + GitHub Pages 部署指南

## 第一步：注册 GitHub 账号（如已有跳过）

1. 打开 https://github.com/signup
2. 输入用户名、邮箱、密码
3. 验证邮箱

## 第二步：创建新仓库

1. 登录 GitHub，点击右上角 **+** → **New repository**
2. Repository name 填：`ajie-workbench`
3. 选择 **Public**（公开，才能用免费 Pages）
4. 勾选 **Add a README file**
5. 点击 **Create repository**

## 第三步：生成 Personal Access Token

1. 点击右上角头像 → **Settings**
2. 左侧菜单最底部 → **Developer settings**
3. 点击 **Personal access tokens** → **Tokens (classic)**
4. 点击 **Generate new token** → **Generate new token (classic)**
5. Note 填：`workbench`
6. Expiration 选：`30 days`（或更长）
7. 勾选 **repo**（全部子项）
8. 点击底部 **Generate token**
9. **复制 Token**（只显示一次！格式如 `ghp_xxxx...`）

## 第四步：上传代码

在有电脑时，打开终端（Windows 用 Git Bash），执行：

```bash
# 1. 下载代码（从 surge.sh 下载）
curl -o index.html https://ajie-workbench-2026.surge.sh

# 2. 初始化 Git
git init
git add index.html
git commit -m "feat: 阿杰工作台男生版"

# 3. 关联 GitHub 仓库（把 YOUR_USERNAME 换成你的用户名）
git remote add origin https://github.com/YOUR_USERNAME/ajie-workbench.git

# 4. 推送（会要求输入用户名和密码，密码填刚才的 Token）
git push -u origin main
```

> 如果分支名是 master，先执行 `git branch -M main`

## 第五步：启用 GitHub Pages

1. 打开你的仓库页面：`https://github.com/YOUR_USERNAME/ajie-workbench`
2. 点击 **Settings** → 左侧菜单 **Pages**
3. Source 选择 **Deploy from a branch**
4. Branch 选择 **main** → 文件夹选 **/ (root)**
5. 点击 **Save**
6. 等待 1-2 分钟，页面顶部会显示你的网址：
   ```
   https://YOUR_USERNAME.github.io/ajie-workbench/
   ```

## 完成！

现在任何人都可以通过这个链接访问你的工作台了！

## 备选方案（不用 GitHub）

如果暂时没有电脑操作 GitHub，可以直接使用已部署的公网链接：

```
https://ajie-workbench-2026.surge.sh
```

这个链接已经可以正常访问，支持完整的增删改查功能。
