#!/usr/bin/env python3
"""初始化数据库并插入示例数据"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import init_db, get_db, hash_pw

print("初始化数据库...")
init_db()

db = get_db()

# 添加示例用户
users = [
    ('Alice', 'alice123', 'alice@example.com', '👩‍💻', '前端工程师，Vue/React 爱好者'),
    ('Bob', 'bob123', 'bob@example.com', '🐧', 'Linux 极客，Arch 用户'),
    ('Charlie', 'charlie123', 'charlie@example.com', '🤖', 'AI 研究员，PyTorch 爱好者'),
    ('Dave', 'dave123', 'dave@example.com', '🔧', '硬件发烧友，DIY PC 玩家'),
    ('Eve', 'eve123', 'eve@example.com', '🚀', '全栈开发，开源贡献者'),
]
for name, pw, email, avatar, bio in users:
    try:
        db.execute("INSERT INTO users(username,password,email,avatar,bio) VALUES(?,?,?,?,?)",
                   (name, hash_pw(pw), email, avatar, bio))
    except:
        pass

db.commit()

# 获取用户ID映射
user_ids = {r['username']: r['id'] for r in db.execute("SELECT id,username FROM users").fetchall()}

# 示例帖子
posts = [
    (1, '2024 年值得学习的编程语言排行榜', user_ids.get('Alice',2),
     '每年都有人问这个问题，今年我来总结一下...\n\n1. Python - AI/数据科学首选，语法简洁\n2. TypeScript - 前端工程化必备，JS的超集\n3. Rust - 系统编程新星，内存安全无GC\n4. Go - 云原生后端，并发模型优秀\n5. Kotlin - Android开发，Java的现代替代\n\n你觉得还有哪些值得学？欢迎补充！'),
    (1, 'VS Code 最强插件推荐（2024版）', user_ids.get('Bob',3),
     '用了3年VS Code，推荐几个真正提升效率的插件：\n\n- GitHub Copilot：AI代码补全，效率翻倍\n- GitLens：Git历史一目了然\n- REST Client：.http文件直接测API\n- Error Lens：行内显示错误信息\n- Prettier：代码格式化神器\n\n装上这几个，生产力up！'),
    (3, 'GPT-4o vs Claude 3.5 Sonnet：编程能力对比', user_ids.get('Charlie',4),
     '最近做了一组编程任务对比测试，结论如下：\n\n**代码生成质量**\n- 复杂算法：Claude略胜\n- 前端组件：GPT-4o更好\n\n**调试能力**\n- 两者相近，Claude解释更详细\n\n**上下文窗口**\n- Claude：200K tokens\n- GPT-4o：128K tokens\n\n总体来说各有千秋，看具体场景。大家有什么体验？'),
    (2, 'RTX 5090 值得买吗？深度测评', user_ids.get('Dave',5),
     '等了半年终于入手了5090，分享一下实测数据：\n\n**游戏性能（4K Ultra）**\n- Cyberpunk 2077: 平均145fps\n- Alan Wake 2: 平均98fps（光追全开）\n\n**AI推理**\n- 24GB GDDR7，跑70B量化模型轻松\n- 比4090快约60%\n\n**功耗**\n- 满载约450W，建议配850W以上电源\n\n总结：如果经济允许，绝对值得！'),
    (4, '推荐几个最近发现的宝藏开源项目', user_ids.get('Eve',6),
     '最近在GitHub探索，发现了几个很有意思的项目：\n\n1. **LocalAI** - 本地运行大模型的API服务器\n2. **Zed** - Rust写的极速代码编辑器\n3. **Hoppscotch** - 开源版Postman，界面超好看\n4. **Coolify** - 自托管Heroku替代品\n5. **Outline** - 团队知识库，比Notion快很多\n\n都附上了star，各位可以去看看！'),
    (5, '从小厂跳大厂：我的面试经验分享', user_ids.get('Alice',2),
     '刚拿到某大厂offer，分享一下整个过程：\n\n**准备阶段（3个月）**\n- 刷LeetCode：每天2-3题，共约200题\n- 八股文：整理了一份前端面试手册\n- 项目梳理：准备3-4个有亮点的项目\n\n**面试流程**\n- 一面：基础知识+算法\n- 二面：系统设计\n- 三面：深度技术+项目\n- HR面：薪资谈判\n\n建议：项目经历要能讲出技术深度，不要只说"做了什么"。'),
    (6, '聊聊你们的 Homelab 配置', user_ids.get('Bob',3),
     '看到好多人在搭Homelab，说说我的配置：\n\n**硬件**\n- 主机：N100小主机，12W功耗\n- 硬盘：4T NAS用\n- 交换机：TP-Link 8口全双工\n\n**软件栈**\n- 系统：Proxmox VE\n- NAS：TrueNAS\n- Docker：跑Jellyfin、Vaultwarden等\n\n每月电费不到50块，性价比绝了！'),
]
for cat_id, title, uid, content in posts:
    db.execute("INSERT INTO posts(category_id,title,user_id,content) VALUES(?,?,?,?)",
               (cat_id, title, uid, content))
db.commit()

# 示例回复
post_ids = [r['id'] for r in db.execute("SELECT id FROM posts ORDER BY id").fetchall()]

replies_data = [
    (post_ids[0], user_ids.get('Bob',3), 'Rust 绝对值得学！虽然上手难，但写出来的代码特别有安全感。'),
    (post_ids[0], user_ids.get('Charlie',4), '同意，Python今年因为AI热度更高了。不过Go在后端领域也非常值得推荐。'),
    (post_ids[1], user_ids.get('Eve',6), '+1 GitLens真的好用，我还推荐一个：Todo Tree，管理代码里的TODO注释。'),
    (post_ids[2], user_ids.get('Alice',2), '我用Claude写文档、用GPT写代码，各取所长。'),
    (post_ids[3], user_ids.get('Charlie',4), '24GB显存太重要了，本地推理大模型不用再为显存发愁了。'),
    (post_ids[4], user_ids.get('Dave',5), 'LocalAI用过，配置有点麻烦但效果不错。Coolify也很好用，推荐！'),
    (post_ids[5], user_ids.get('Bob',3), '感谢分享！请问系统设计面试主要考哪些方向？'),
    (post_ids[5], user_ids.get('Alice',2), '主要考：高并发设计、数据库选型、缓存策略、分布式基础这些。'),
    (post_ids[6], user_ids.get('Eve',6), '我也在用N100！功耗低、够用，非常适合24小时运行的服务。'),
]
for pid, uid, content in replies_data:
    if pid and uid:
        db.execute("INSERT INTO replies(post_id,user_id,content) VALUES(?,?,?)", (pid, uid, content))

# 置顶第一篇帖子
if post_ids:
    db.execute("UPDATE posts SET pinned=1 WHERE id=?", (post_ids[0],))

db.commit()
db.close()

print("OK! 初始化完成!")
print("   账号: admin / admin123")
print("   测试用户: Alice/alice123, Bob/bob123 etc")
