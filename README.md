# 模拟交易系统（报表版）

当前仓库已收敛为“报表功能优先”的最新版本，只保留策略报表、持仓、历史持仓与交易记录相关能力。

## 启动

```bash
python run.py
```

默认地址：

- 首页：`http://127.0.0.1:8899/`
- Swagger：`http://127.0.0.1:8899/docs`

## 核心能力

- 策略列表与策略详情报表
- 当前持仓（`positions`）
- 历史持仓（`position_history`，仅已平仓）
- 交易信号入口（`POST /api/trades`）
- 报表指标与收益曲线（由交易和持仓实时计算）

## 主要接口

- `GET /api/strategies`
- `GET /api/strategies/{id}`
- `GET /api/strategies/{id}/dashboard`
- `POST /api/trades`
- `GET /api/trades`
- `GET /api/trades/stats?strategy_id=...`
- `GET /api/positions?strategy_id=...`
- `GET /api/positions/history?strategy_id=...`
- `GET /api/positions/overview?strategy_id=...`
- `PUT /api/positions/update-prices`
- `PUT /api/positions/manual-adjustments`

## 测试

仅保留最新测试程序：

```bash
python -m pytest tests/test_app.py
```

全流程冒烟脚本（推荐）：

```bash
python full_flow_test.py
```

长周期高波动调试（用于策略评估和收益曲线）：

```bash
python full_flow_test.py --days 240 --volatility 0.08 --min-trades 60
```

如果本地未安装 `fastapi`，可切换为 HTTP 模式（需先启动服务）：

```bash
python full_flow_test.py --mode http --base-url http://127.0.0.1:8899
```
