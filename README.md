# 模拟交易系统

基于 `FastAPI + SQLAlchemy + MySQL` 的轻量模拟交易系统，当前提供三类主要页面：

- 策略管理台：查看每个策略的累计收益、年化收益、今日收益、最大回撤
- 策略详情页：查看当前持仓、历史持仓变化、最近成交和收益曲线
- 下单测试台：通过按钮直接买入、卖出和更新现价，实时观察统计信息变化

## 快速启动

```bash
python run.py
```

启动后访问：

- 首页：[http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- 下单测试台：[http://127.0.0.1:8000/trade-tester](http://127.0.0.1:8000/trade-tester)
- Swagger：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 数据库配置

默认已经适配以下 MySQL 配置：

```yaml
mysql:
  user: root
  password: 7842zc
  host: localhost
  database: trade_system_db
  port: 3306
```

也可以通过环境变量覆盖：

```powershell
$env:MYSQL_USER='root'
$env:MYSQL_PASSWORD='7842zc'
$env:MYSQL_HOST='localhost'
$env:MYSQL_PORT='3306'
$env:MYSQL_DATABASE='trade_system_db'
```

## 新增评估字段

策略评估接口已扩展以下核心字段：

- `strategy_return_pct`
- `strategy_annualized_return_pct`
- `benchmark_return_pct`
- `excess_return_pct`
- `alpha`
- `beta`
- `sharpe_ratio`
- `sortino_ratio`
- `information_ratio`
- `win_rate`
- `profit_loss_ratio`
- `daily_win_rate`
- `profit_trade_count`
- `loss_trade_count`
- `strategy_volatility_pct`
- `benchmark_volatility_pct`
- `max_drawdown_period`

说明：当前 benchmark 使用年化基准收益假设值进行生成，默认 `3%`，可在策略参数或评估请求中通过 `benchmark_annual_return` 覆盖。

## 演示数据

可执行以下命令向当前 MySQL 数据库追加一批演示策略和随机买卖单，并同时做接口烟雾测试：

```bash
python seed_demo_data.py
```

## HTTP 回测模板

项目已将模板脚本压缩为一个更适合复制复用的最小版本：[examples/http_backtest_template.py](examples/http_backtest_template.py)。

特点：

- 单文件，当前为 200 行以内
- 使用 `requests` 直连 HTTP 接口
- 只封装 3 个常用接口：`buy`、`sell`、`get_positions`
- 策略逻辑只有一个极简均线示例，方便直接替换
- 默认假设 `strategy_id` 已存在，避免把脚本写得过重

运行前先启动服务，并准备一个激活状态的策略 ID：

```bash
python examples/http_backtest_template.py --strategy-id 3 --symbol 300308.SZ --start-date 20250101 --end-date 20251230
```

如果不希望回测结束时自动平仓：

```bash
python examples/http_backtest_template.py --strategy-id 3 --symbol 300308.SZ --keep-position
```

说明：

- 常用复用点只需要改 `SimpleMaStrategy.run()` 里的买卖条件。
- 如果别人只关心下单模板，可以直接拿 `TradeApi` 这个类。
- 这个模板不再依赖策略注册、统计概况等额外 HTTP 接口。

## 主要接口

- `GET /api/strategies`
- `GET /api/strategies/{id}`
- `GET /api/strategies/{id}/dashboard`
- `POST /api/trades/buy`
- `POST /api/trades/sell`
- `GET /api/trades`
- `GET /api/trades/stats?strategy_id=...`
- `GET /api/positions?strategy_id=...`
- `GET /api/positions/overview?strategy_id=...`
- `PUT /api/positions/update-prices`
- `POST /api/evaluations`

## 测试

```bash
python run_tests.py
```

## 目录结构

```text
app/            后端代码
examples/       示例脚本
static/         静态资源
templates/      页面模板
tests/          自动化测试
run.py          启动入口
run_tests.py    测试入口
seed_demo_data.py 演示数据和接口烟雾测试脚本
.vendor/        本地依赖目录
```
