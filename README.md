# frontier_papers

独立期刊追踪仓库，包含两个页面：

- 政策主题追踪页：`https://j-gezelligheid.github.io/frontier_papers/`
- 经济学扩展追踪页：`https://j-gezelligheid.github.io/frontier_papers/econ-frontier.html`

## 数据模块

- 政策期刊追踪
  - 脚本：`standalone-policy-journal-tracker/scripts/update_policy_tracker.py`
  - 数据：`standalone-policy-journal-tracker/data/policy_tracker.json`
- 经济学扩展追踪
  - 脚本：`standalone-econ-frontier-tracker/scripts/update_econ_tracker.py`
  - 数据：`standalone-econ-frontier-tracker/data/econ_tracker.json`

## 自动更新频率

GitHub Actions 工作流：

- `.github/workflows/update_policy_tracker.yml`
- `.github/workflows/update_econ_tracker.yml`

两个工作流都改为**每周更新一次**（UTC 周日凌晨）。

## 翻译配置

如果要启用中文翻译，请在仓库 Secrets 添加：

- `KIMI_API_KEY`

经济学扩展工作流不再因为翻译不可用而整条失败；没有可用密钥时会继续更新英文数据。

## 本地运行

```powershell
python standalone-policy-journal-tracker/scripts/update_policy_tracker.py
python standalone-econ-frontier-tracker/scripts/update_econ_tracker.py
```

本地预览前端请使用 HTTP 服务（不要直接双击 `index.html`）：

```powershell
python -m http.server 8000
```

然后打开：

- `http://localhost:8000/`
- `http://localhost:8000/econ-frontier.html`
