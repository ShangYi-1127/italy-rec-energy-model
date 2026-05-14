# 🚀 快速启动指南 (QUICKSTART)

**5分钟快速上手**

---

## 📦 环境要求

- Python 3.9+
- pip 或 conda

---

## ⚡ 快速启动步骤

### 1️⃣ 下载/克隆项目

```bash
# 进入项目目录
cd single\ building\ electrical\ energy\ sitimulation-demo
```

### 2️⃣ 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

如果速度慢，可以尝试使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tsinghua.edu.cn/simple
```

### 4️⃣ 启动应用

```bash
streamlit run app.py
```

### 5️⃣ 打开浏览器

应用会自动打开，或手动访问：

```
http://localhost:8501
```

---

## 🎮 使用步骤

### 第一次使用

1. **侧边栏参数配置**
   - 📍 选择意大利地区(默认Piemonte)
   - 📅 选择建筑年代(默认1961-1970)
   - 🏢 选择建筑类型(默认住宅)
   - 📐 调整建筑面积(默认100 m²)
   - ☀️ 设置PV装机容量(默认10 kW)

2. **点击 "🔄 更新计算" 按钮**

3. **查看三个TAB的结果**
   - ⚡ TAB 1: 建筑耗电量分解
   - ☀️ TAB 2: 光伏发电特性
   - 📊 TAB 3: 电量供需匹配

### 对比测试

试试这些对比看看数据如何变化：

**对比1：地区差异**

- 固定：1991-2005年代，住宅
- 变化：Piemonte → Lazio → Sicilia
- 观察：能耗、发电、覆盖率的变化

**对比2：年代演变**

- 固定：Piemonte，住宅
- 变化：<1919 → 1946-1960 → 1991-2005 → >2005
- 观察：U值从1.8降至0.18，能耗大幅下降

**对比3：PV系统容量**

- 固定：Sicilia，住宅
- 变化：PV容量 5 → 10 → 20 → 50 kW
- 观察：覆盖率如何随PV增加而提升

---

## 🔍 关键输出理解

### TAB 1 - 耗电量

| 指标       | 含义                   | 单位     |
| ---------- | ---------------------- | -------- |
| U值        | 建筑保温性能，越低越好 | W/(m²·K) |
| 年总耗电量 | 整年消耗电能           | MWh      |
| HVAC占比   | 供暖/制冷占总能耗      | %        |
| 峰值       | 最高小时耗电           | kW       |

**💡 提示**：冬季HVAC占比>70%是正常的！

### TAB 2 - 生产量

| 指标       | 含义               | 单位 |
| ---------- | ------------------ | ---- |
| 年总发电量 | 整年生成电能       | MWh  |
| 利用小时数 | 等效满功率运行时长 | h    |
| 系统效率   | PV转换效率         | %    |

**💡 提示**：利用小时数 = 年发电量 / 装机容量

### TAB 3 - 匹配分析

| 指标   | 含义          | 范围    |
| ------ | ------------- | ------- |
| 覆盖率 | PV能供应多少% | 0-100%+ |
| 缺电   | 需要从网购入  | MWh     |
| 余电   | 可出售/储存   | MWh     |

**💡 提示**：覆盖率>100%表示年度有余电！

---

## 🐛 常见问题

### Q: 运行报错："找不到模块..."

```
A: 确保虚拟环境已激活，依赖已安装
   pip install -r requirements.txt
```

### Q: 数据为什么都是模拟的？

```
A: 当前版本使用模拟气象数据便于演示
   后续可接入PVGIS API获取真实气象
```

### Q: 为什么冬季能耗那么高？

```
A: 北方冬季供暖需求大
   E_hvac = Q_demand / COP
   Q_demand ∝ (T_int - T_out)
   T_out冬季低导致Q_demand大
```

### Q: 如何部署到云上？

```
A: 参见 README.md 中的 "Streamlit Cloud 云部署" 部分
   需要：GitHub账号 + 项目仓库
```

---

## 📚 进阶操作

### 修改建筑参数

编辑 `backend/archetype_data.py` 中的 `ARCHETYPE_PARAMS` 字典

### 导入真实气象数据

在 `backend/load_model.py` 中添加PVGIS API调用

### 自定义经济评估

修改 `backend/economic_model.py` 中的补贴参数

---

## 🎓 学习资源

- **公式推导**：查看 `PROJECT_SPECIFICATION.md` 的"计算公式体系"章节
- **代码注释**：所有模块都有详细的docstring说明
- **参考标准**：
  - BS EN 16798-1:2019 (室内环境设计)
  - ISO 52016-1:2017 (能耗计算)
  - Pvlib官方文档

---

## 💬 需要帮助？

1. 查看 README.md 详细文档
2. 检查 PROJECT_SPECIFICATION.md 的FAQ部分
3. 在GitHub上提Issue

---

**祝您使用愉快！** 🌞
