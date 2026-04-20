# CSV 导出功能调试指南

## 📍 导出入口位置

### 前端页面
策略详情页面：`/strategies/{strategy_id}`

### 导出按钮位置
1. **当前持仓** → "当前持仓" tab 页 → 右上角 "导出 CSV" 按钮
2. **成交记录** → "成交记录" tab 页 → 右上角 "导出 CSV" 按钮
3. **历史持仓** → "历史持仓" tab 页 → 右上角 "导出 CSV" 按钮

---

## 🐛 使用 Chrome DevTools 调试

### 方法 1: 使用浏览器界面（推荐）

1. **打开策略详情页面**
   ```
   http://101.132.136.153:8899/strategies/1
   ```

2. **打开 DevTools**
   - 按 `F12` 或 `Ctrl+Shift+I` (Windows)
   - 或右键 → "检查"

3. **切换到 Console 标签**
   - 在 Console 中直接调用导出函数：
   ```javascript
   // 导出当前持仓
   exportCurrentPositions()

   // 导出成交记录
   exportTrades()

   // 导出历史持仓
   exportPositionHistory()
   ```

### 方法 2: 使用 Network 面板监控请求

1. **打开 DevTools → Network 标签**
   - 勾选 "Preserve log" 保留日志
   - 筛选 "Doc" 或 "All"

2. **点击页面上的导出按钮**
   - 在 Network 面板会看到以下请求：
     - `/api/positions?strategy_id=1` (当前持仓)
     - `/api/trades?export=csv&strategy_id=1` (成交记录)
     - `/api/positions/history?strategy_id=1` (历史持仓)

3. **分析请求详情**
   - 点击请求查看：
     - **Headers**: 请求和响应头
     - **Response**: API 返回的数据
     - **Preview**: 格式化预览

### 方法 3: Console 完整测试脚本

在 Console 中粘贴以下脚本进行完整测试：

```javascript
// ==========================================
// CSV 导出测试脚本
// ==========================================

const BASE_URL = "http://101.132.136.153:8899";
const STRATEGY_ID = 1; // 修改为你的策略ID

// 测试所有导出功能
async function testAllExports() {
  console.log('🚀 开始测试 CSV 导出功能...\n');

  // 1. 测试当前持仓导出
  console.log('📊 测试 1/3: 导出当前持仓');
  try {
    const response = await fetch(`${BASE_URL}/api/positions?strategy_id=${STRATEGY_ID}`);
    const data = await response.json();
    console.log(`✅ 当前持仓数据:`, data);
    console.log(`   - 持仓数量: ${data.length}`);
  } catch (error) {
    console.error(`❌ 失败:`, error);
  }

  // 2. 测试成交记录导出
  console.log('\n📋 测试 2/3: 导出成交记录');
  try {
    const response = await fetch(`${BASE_URL}/api/trades?export=csv&strategy_id=${STRATEGY_ID}`);
    const csv = await response.text();
    console.log(`✅ 成交记录 CSV (${csv.length} 字符)`);
    console.log(`   - 前 200 字符:`, csv.substring(0, 200));
  } catch (error) {
    console.error(`❌ 失败:`, error);
  }

  // 3. 测试历史持仓导出
  console.log('\n📜 测试 3/3: 导出历史持仓');
  try {
    const response = await fetch(`${BASE_URL}/api/positions/history?strategy_id=${STRATEGY_ID}`);
    const data = await response.json();
    console.log(`✅ 历史持仓数据:`, data);
    console.log(`   - 历史记录数: ${data.length}`);
  } catch (error) {
    console.error(`❌ 失败:`, error);
  }

  console.log('\n✨ 测试完成！');
  console.log('\n💡 手动调用导出函数:');
  console.log('   - exportCurrentPositions()');
  console.log('   - exportTrades()');
  console.log('   - exportPositionHistory()');
}

// 执行测试
testAllExports();

// 导出函数供手动调用
window.testAllExports = testAllExports;
```

---

## 🔍 常见问题排查

### 问题 1: 点击导出按钮无反应

**检查方法：**
1. 打开 DevTools → Console，查看是否有错误信息
2. 检查导出函数是否正确定义：
   ```javascript
   console.log(typeof exportCurrentPositions); // 应该输出 "function"
   ```

**可能原因：**
- JavaScript 文件未正确加载
- 函数名拼写错误

### 问题 2: 下载的 CSV 文件为空

**检查方法：**
1. 打开 DevTools → Network
2. 点击导出按钮，找到对应的 API 请求
3. 查看 Response，检查是否有数据

**可能原因：**
- 策略 ID 不存在
- 该策略没有数据

### 问题 3: CSV 文件乱码

**解决方案：**
已添加 UTF-8 BOM (`\uFEFF`)，应该可以正常在 Excel 中打开。
如果仍有问题，尝试：
1. 用记事本打开，另存为 UTF-8 格式
2. 在 Excel 中使用 "数据 → 从文本/CSV 导入" 功能

### 问题 4: Network 面板看不到请求

**检查方法：**
1. 确保勾选了 "Preserve log"
2. 刷新页面后重试
3. 检查 Network 面板的筛选条件

---

## 📊 API 端点说明

### 1. 当前持仓 API
```http
GET /api/positions?strategy_id=1
```
**响应格式：** JSON
```json
[
  {
    "position_id": 1,
    "strategy_id": 1,
    "symbol": "600519.XSHG",
    "quantity": 100.000000,
    "avg_cost": 1800.500000,
    "current_price": 1850.000000,
    "market_value": 185000.00,
    "unrealized_pnl": 5000.00,
    "open_time": "2026-04-01T09:30:00",
    "updated_at": "2026-04-16T15:00:00"
  }
]
```

### 2. 成交记录 API（CSV 导出）
```http
GET /api/trades?export=csv&strategy_id=1
```
**响应格式：** CSV (text/csv)
```csv
trade_id,strategy_id,symbol,direction,quantity,price,amount,commission,realized_pnl,trade_time,remark,exec_status
1,1,600519.XSHG,BUY,100.000000,1800.500000,180050.00,5.0000,,2026-04-01 09:30:00,,
```

### 3. 历史持仓 API
```http
GET /api/positions/history?strategy_id=1
```
**响应格式：** JSON
```json
[
  {
    "history_id": 1,
    "strategy_id": 1,
    "symbol": "600519.XSHG",
    "open_time": "2026-04-01T09:30:00",
    "close_time": "2026-04-15T14:30:00",
    "entry_quantity": 100.000000,
    "exit_quantity": 100.000000,
    "avg_cost": 1800.500000,
    "close_price": 1850.000000,
    "realized_pnl": 5000.00,
    "total_commission": 10.0000,
    "close_trade_id": 2,
    "created_at": "2026-04-15T14:30:00"
  }
]
```

---

## 🎯 快速测试步骤

1. **访问策略详情页面**
   ```
   http://101.132.136.153:8899/strategies/1
   ```

2. **打开 DevTools（F12）**

3. **切换到 Console 标签**

4. **复制粘贴以下代码并执行：**
   ```javascript
   // 快速测试
   exportCurrentPositions();
   ```

5. **检查浏览器下载文件夹**
   - 应该会下载 `positions_1_2026-04-16.csv` 文件

6. **用 Excel 或文本编辑器打开 CSV 文件**
   - 检查数据是否正确

---

## 📝 导出文件命名规则

- **当前持仓**: `positions_{strategy_id}_{YYYY-MM-DD}.csv`
- **成交记录**: `trades_{strategy_id}_{YYYY-MM-DD}.csv`
- **历史持仓**: `position_history_{strategy_id}_{YYYY-MM-DD}.csv`

---

## 🔧 手动调用导出函数

在 Console 中可以直接调用：

```javascript
// 获取当前策略ID
const strategyId = document.body.dataset.strategyId;
console.log('当前策略ID:', strategyId);

// 调用导出函数
exportCurrentPositions();  // 导出当前持仓
exportTrades();            // 导出成交记录
exportPositionHistory();   // 导出历史持仓
```

---

## ✨ 功能特性

✅ **三个导出功能**：当前持仓、成交记录、历史持仓
✅ **CSV 格式**：兼容 Excel 和文本编辑器
✅ **UTF-8 编码**：支持中文，添加 BOM 头
✅ **一键导出**：点击按钮即可下载
✅ **自动命名**：包含策略ID和日期
✅ **完整数据**：导出所有字段信息

---

## 📞 技术支持

如有问题，请：
1. 检查浏览器 Console 是否有错误
2. 使用 Network 面板检查 API 请求
3. 确认策略 ID 是否正确
4. 检查服务器是否正常运行