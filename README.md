# frontier_papers

独立期刊追踪仓库，聚焦：

- 房地产
- 城市治理
- 公共政策

## 在线页面

启用 GitHub Pages 后，页面入口为：

- `https://j-gezelligheid.github.io/frontier_papers/`

页面会读取：

- `standalone-policy-journal-tracker/data/policy_tracker.json`

## 自动更新数据

已提供 GitHub Actions 工作流：

- `.github/workflows/update_policy_tracker.yml`

更新策略：

- 每 6 小时自动运行一次
- 支持手动触发（Actions -> Update Policy Tracker Data -> Run workflow）

如果你希望自动中文翻译，在仓库 Secrets 里添加：

- `KIMI_API_KEY`

## 本地运行

```powershell
python standalone-policy-journal-tracker/scripts/update_policy_tracker.py
```

本地预览前端页面时，不要直接双击 `index.html`（`file://` 会拦截 fetch）。请用：

```powershell
python -m http.server 8000
```

然后打开：

- `http://localhost:8000/`
