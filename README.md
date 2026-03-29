# TechHub - 科技爱好者论坛

一个基于 Python Flask + SQLite 的轻量级论坛系统，采用深色科技风 UI。

## 功能

- 🏠 首页：帖子列表、分类筛选、关键词搜索、分页
- 👤 用户系统：注册、登录、个人主页、头像设置
- ✏️ 发帖回复：选版块发帖、帖子回复、点赞
- 🛡️ 管理后台：数据总览、用户封禁/解封、帖子置顶/锁定/删除
- 📱 响应式设计：适配桌面和移动端

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库（含示例数据）
python seed.py

# 启动服务
python app.py
```

访问 http://127.0.0.1:5000

## 默认账号

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | admin123 | 管理员 |
| Alice | alice123 | 普通用户 |

## 技术栈

- Python 3.10+
- Flask
- SQLite
- HTML / CSS / JavaScript

## 版块

- 💻 编程技术
- 🔧 硬件数码
- 🤖 AI & 机器学习
- 🌐 开源项目
- 🚀 职场与成长
- ☕ 水吧闲聊

## 许可

MIT License
