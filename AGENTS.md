# AGENTS.md — 给 AI 编程助手的安装指南

本文件面向 CodeBuddy / Claude Code / Cursor / Copilot 等 AI 编程助手。
当用户要求"帮我把这个工具装好并跑起来"时，按以下步骤执行。

## 目标

在用户 macOS 菜单栏常驻显示 CodeBuddy / WorkBuddy 积分余量，并每日自动签到。

## 前置条件检查

- macOS（`sw_vers` 确认）
- Python 3.9+（`python3 --version`），缺失时提示用户安装
- 用户已有 CodeBuddy / WorkBuddy 账号（两者同一账号体系）

## 安装步骤

```bash
git clone https://github.com/stevencmy/codebuddy-menubar.git
cd codebuddy-menubar
./setup.sh --autostart   # 装依赖 + 复制文件 + 配置 LaunchAgent 开机自启并启动
```

装好后配置凭证（见下一节），然后让用户点菜单栏图标里的"重新载入配置"，
或执行 `launchctl kickstart -k gui/$(id -u)/com.codebuddy.menubar` 重启。

## 凭证配置（需要用户配合，Agent 无法代办）

凭证写入 `~/.codebuddy-menubar.json`，必填两个键：

- `cookie`：从 workbuddy.cn 登录态请求复制的 Cookie
- `user_agent`：与 Cookie **同一个请求**里的 User-Agent

引导用户抓取（约 30 秒）：

1. 用 Chrome 打开 https://www.workbuddy.cn/profile/plans-usage 并登录
2. `Option + Cmd + I` → Network 面板 → 刷新页面 → 筛选 `get-user-resource`
3. 点开请求 → Request Headers → 分别右键复制 `cookie:` 和 `user-agent:` 的值

写入示例（若配置文件已存在，只更新这两个键，保留其余用户配置）：

```json
{
  "cookie": "<用户提供的值>",
  "user_agent": "<用户提供的值>"
}
```

## 验证安装

1. `launchctl list | grep codebuddy.menubar` 输出中有 PID
2. 菜单栏右上角在约 5 秒内出现 `</> 数字 · 百分比`（如 `</> 2087 · 99.4%`）
3. 若显示 `?`，点开菜单第一行查看错误原因：
   - `Cookie 已失效` → 会话过期（约 7 天）或官网退出过登录，重新抓取凭证
   - `HTTP xxx` / 超时 → 网络问题，等待下次自动刷新或点"立即刷新"
4. 运行日志：`/tmp/codebuddy-menubar.log`

## 安全注意

- Cookie 等同于用户登录凭证：只写入 `~/.codebuddy-menubar.json`，
  **不要**回显到终端输出、写进任何 git 提交或日志
- 不要主动把凭证内容复述给用户以外的任何渠道
- `.gitignore` 已排除本地配置，无需额外处理
