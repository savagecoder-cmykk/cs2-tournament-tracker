# CS2 赛事追踪系统

一个基于Flask的CS2比赛数据分析和可视化系统，支持比赛数据导入、选手统计分析和多种排行榜展示。

## 功能特性

### 📊 数据管理
- 支持Excel文件格式的比赛数据导入
- SQLite数据库存储比赛和选手数据
- 实时数据同步和更新

### 🏆 12个专业排行榜
1. **MVP榜单** - 按平均Rating+排名
2. **爆头榜** - 爆头率专业排行榜  
3. **助攻王** - 平均助攻数排行榜
4. **生存榜** - 综合生存能力排名
5. **突破刺客榜** - 突破效率分析
6. **团队粘合剂榜** - 团队配合指数
7. **狙神天梯榜** - 狙击手技能排名
8. **稳定如狗榜** - 发挥稳定性评估
9. **躺赢绝缘体榜** - 绝对实力认证
10. **击杀效率榜** - KES效率分析
11. **辅助王** - 支援能力排行
12. **首杀王** - 首开能力评估

### 📈 选手数据统计
- 11项关键指标展示：比赛场次、平均击杀、平均死亡、平均助攻、平均K/D、平均Rating+、平均爆头率、平均首杀数、平均ADR、平均RWS、平均KAST
- 实时计算平均值和综合评估
- 选手匹配数量统计

## 技术架构

### 后端技术栈
- **Python 3.8+** - 主要编程语言
- **Flask** - Web框架
- **SQLAlchemy** - ORM数据库操作
- **SQLite** - 轻量级数据库
- **Pandas** - 数据处理和分析
- **OpenPyXL** - Excel文件处理

### 前端技术栈
- **HTML5/CSS3** - 界面设计
- **JavaScript (ES6+)** - 前端交互
- **Fetch API** - 数据请求
- **响应式设计** - 移动端适配

### 特色功能
- **特殊效果标签系统** - 每个排行榜都有独特的标签分类
- **智能计算公式** - 针对CS2游戏机制的专业算法
- **实时数据更新** - 数据变更即时反映在界面上
- **导出功能** - 支持比赛数据Excel导入

## 安装和使用

### 环境要求
- Python 3.8+
- pip包管理器

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/savagecoder-cmykk/cs2-tournament-tracker.git
cd cs2-tournament-tracker
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **初始化数据库**
```bash
python init_db.py
```

4. **启动服务器**
```bash
python app.py
```

5. **访问系统**
打开浏览器访问：`http://localhost:5002`

### 数据导入格式
系统支持Excel格式的比赛数据导入，需要包含以下字段：
- 比赛名称、地图、队伍名称、比分
- 选手个人数据：击杀、死亡、助攻、爆头数、首杀数、首死数、ADR、RWS、KAST、Rating+、Sniper kills等

## 项目结构
```
├── app.py              # 主应用文件
├── models.py           # 数据模型定义
├── init_db.py          # 数据库初始化
├── requirements.txt    # Python依赖
├── static/             # 静态文件
│   ├── css/
│   └── js/
├── templates/          # HTML模板
├── uploads/            # 上传文件目录
└── instance/           # 数据库文件
```

## 贡献指南

欢迎提交Issue和Pull Request来改进项目！

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 作者

savagecoder-cmykk

## 更新日志

### v1.0.0 (2025-12-30)
- 初始版本发布
- 实现12个专业排行榜
- 支持Excel数据导入
- 完整的选手统计分析功能