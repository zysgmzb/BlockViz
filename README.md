# BlockViz

BlockViz 是一个使用 PySide6 (Qt6) 构建的桌面级区块链数据浏览器，致力于把链上指标、区块/交易流、账户洞察等信息带到原生应用体验中。所有视图都直接消费真实的 Ethereum JSON-RPC 数据，让你能够把本地节点或第三方服务（Infura、Alchemy、自建 RPC 等）作为“数据后端”来观察网络状态。

> BlockViz is a modern Qt-based blockchain explorer for the desktop. It focuses on fast feedback from any Ethereum-compatible RPC endpoint, pairing real-time metrics with an opinionated dark UI theme.

## ✨ Features

- **Live dashboard**：最近区块时间线、平均出块时间、Gas 价格与累计交易量，每 20s 自动刷新。
- **全局搜索**：Dashboard 顶部搜索栏能自动识别区块高度 / Tx Hash / Address，并一键跳转到对应视图。
- **Blocks 视图**：展示区块元数据、Gas 利用率、完整交易列表并推断交易类型（Transfer / Call / Contract Creation）。
- **Transactions 视图**：查看交易状态、Gas 详情、Nonce 以及原始 Input Data（带一键复制）。
- **Address 视图**：显示余额、交易计数、EOA/合约类型，并可复制合约 Bytecode。
- **可配置 RPC**：左侧 SideBar 内联设置 RPC，或通过 `BLOCKVIZ_RPC_URL` 环境变量预先定义默认节点。
- **原子化 UI 组件**：Info Cards、Detail Sections、SearchBar 等组件可复用，方便后续扩展更多视图。

## 🚀 Getting Started

### 1. 直接下载（推荐）
如果你只是想使用 BlockViz，建议直接前往 [GitHub Releases](https://github.com/zysgmzb/BlockViz/releases) 下载对应平台的单文件可执行程序。

- **Windows**：下载 `BlockViz-windows-x64.exe` 后双击运行
- **macOS**：下载 `BlockViz-macos` 后，如有需要先执行 `chmod +x BlockViz-macos`
- **Linux**：下载 `BlockViz-linux-x64` 后，如有需要先执行 `chmod +x BlockViz-linux-x64`

### 2. 从源码运行（开发者）
如果你想参与开发，或希望直接从源码启动：

```bash
git clone https://github.com/zysgmzb/BlockViz.git
cd BlockViz
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .                   # 或 pip install -e "[dev]" 以同时安装 ruff / pytest
python -m blockviz
```

安装为命令行入口后，也可以直接运行：

```bash
blockviz
```

### 3. 首次启动
第一次启动会提示输入 RPC URL。你可以在侧栏填入任意兼容 Ethereum JSON-RPC 的 Endpoint，并点击 **Apply RPC**。

常见示例：
- 本地节点：`http://127.0.0.1:8545`
- Infura：`https://mainnet.infura.io/v3/<key>`
- Alchemy：`https://eth-mainnet.g.alchemy.com/v2/<key>`

连接成功后，Dashboard、Blocks、Transactions 和 Address 视图都会自动使用当前 RPC 数据源。

## ⚙️ RPC 配置

| 方式 | 说明 |
| --- | --- |
| 侧栏输入 | 在应用内部输入完整 URL（例如 `https://mainnet.infura.io/v3/<key>`）；连接成功后会广播给所有视图。 |
| 环境变量 | `export BLOCKVIZ_RPC_URL=https://...`，当应用启动时自动生效，可作为默认值。 |
| 本地节点 | 例如 `http://127.0.0.1:8545`（geth、erigon、anvil 等）；默认值就是本地端口。 |

连接失败会在状态栏提示错误信息（HTTP/JSON-RPC code），UI 会保持空状态以避免展示过期数据。

## 🗂️ Project Layout

```
BlockViz/
├── pyproject.toml          # 项目信息 & entry point
└── src/blockviz
    ├── __main__.py         # `python -m blockviz` 入口
    ├── app.py              # QApplication 启动、主题和窗口管理
    ├── core/config.py      # RPC 配置 & 环境变量解析
    ├── services/rpc_client.py
    │   └── Ethereum JSON-RPC 封装（blocks / tx / account helpers）
    └── ui/
        ├── main_window.py  # 主窗口 + Sidebar + 状态同步
        ├── dashboard.py    # Dashboard 视图，实时刷新
        ├── blocks.py       # Blocks 详情视图
        ├── transactions.py # Transactions 详情视图
        ├── address.py      # Address 详情视图
        └── widgets/        # InfoCard、SearchBar、Sidebar 等基础组件
```

## 🧱 Architecture Notes
- **PySide6 + Qt Fusion 主题**：自定义 `QPalette` + QSS（见 `ui/styles.py`）打造统一深色主题，并启用 HiDPI 支持。
- **RPC 层**：`services.rpc_client.RpcClient` 聚合常用的 `eth_*` 调用（最新区块、交易详情、账户余额等），对网络错误提供统一 `RpcError`。
- **视图间通信**：Dashboard 的搜索跳转通过回调触发 Blocks / Transactions / Address 视图的公开方法，实现“全局搜索 → 明细视图”流。
- **配置状态**：`core.config.AppConfig` 负责保存/同步当前 RPC URL，可扩展为持久化或集中状态管理。

## 🧪 Development

```bash
pip install -e ".[dev]"
ruff check src                     # 代码规范
pytest                             # （若添加单元测试）
```

开发体验建议：
- 将 `BLOCKVIZ_RPC_URL` 指向测试网或本地节点，避免在主网调试时被限速。
- Qt Designer / Qt Creator 可用于快速迭代 UI，再在 `ui/` 内实现逻辑。
- 若要打包桌面应用，可尝试 PyInstaller、cx_Freeze 或 Briefcase。

### Releases

项目会通过 GitHub Releases 分发单文件可执行程序。

如果你是使用者，直接前往仓库的 Releases 页面下载对应平台版本即可。


## 🗺️ Roadmap / Ideas
- 批量 RPC 请求与缓存，降低刷新延迟。
- 节点/验证者视图：质押信息、提案人统计、Gas 费用曲线等。
- 地址画像：交易历史时间线、标签系统、合约 ABI 解析。
- 搜索联想与历史记录，减少重复输入。
- 多网络预设与网络状态提示（主网/测试网/私链）。

## ✅ TODO
- 连接钱包功能，完成钱包授权流程与签名操作的 UI/交互。
- 提供合约反编译功能，并结合 AI 分析返回的字节码 / ABI，辅助理解合约行为。
- 合约实时交互：在 UI 中发起读写调用、展示结果并跟踪状态变化。

## 🤝 Contributing
Issues、Feature Requests、UI Mock、PR 都欢迎。提 PR 前请运行 `ruff` 与（如有）`pytest`，并在描述里说明：
1. 做了什么；
2. 为什么这样做；
3. 如何验证；
4. 有无其他 TODO。

## 📄 License
本项目以 MIT License 授权发布，详情参见根目录的 `LICENSE` 文件。
