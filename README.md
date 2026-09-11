# CodeBuddy Menubar

> **📊 实时监控积分余量 ｜ ✅ 每日自动签到领积分 ｜ 🔔 低余额自动提醒**

**macOS 菜单栏常驻的 [腾讯云 CodeBuddy / WorkBuddy](https://www.codebuddy.ai) 积分监控 + 自动签到工具。**

两大核心功能：

- **📊 监控**：余量、百分比、各套餐明细与到期时间常驻菜单栏，低于阈值自动弹窗提醒
- **✅ 自动领积分**：每天自动签到，绝不错过任何一个免费积分

不打开网页、不装 IDE 插件，抬头就能看到积分余量：

```
</> 2087 · 99.4%
```

> [!NOTE]
> 本项目的用量接口与鉴权方案参考自 [wwenc6621/CodeBuddy-Usage](https://github.com/wwenc6621/CodeBuddy-Usage)（MIT License），感谢原作者对接口协议的逆向与分享。本项目为个人工具，与腾讯 CodeBuddy 官方无关。

![screenshot](https://raw.githubusercontent.com/stevencmy/codebuddy-menubar/main/docs/screenshot.png?v=2)

## 功能

- 🧾 菜单栏常驻显示积分余量与百分比（单色 template 图标，自动适配深/浅色菜单栏）
- 🔢 消耗顺序可视化：下拉按官方扣减规则排序展示各积分包（套餐 / 加量包 / 裂变包），①②③ 编号即扣减先后，▶ 消耗中 / ▷ 排队中，到期时间显示倒计时（如「明天 01:03 到期」）；箭头、序号、名称、用量、到期时间五列按菜单字体实测渲染宽度竖向对齐（像素级，残差 < 0.5px）
- 🔄 定时自动刷新（默认 30 分钟，可配置），支持手动立即刷新
- ✅ 每日自动签到领积分（可关闭），签到成功弹系统通知
- 🔔 低余额提醒（阈值可配置，越过阈值只提醒一次）
- 🍪 凭证本地保存（`~/.codebuddy-menubar.json`），不上传任何服务器
- 🧩 如果已安装 VS Code 插件 [CodeBuddy-Usage](https://github.com/wwenc6621/CodeBuddy-Usage) 并配置过凭证，首次启动会自动导入，无需重复抓取

## 准备工作：获取 Cookie 和 User-Agent

工具通过官网登录态查询用量，需要你手动抓一次凭证（约 30 秒）：

1. 用 Chrome 登录 [workbuddy.cn 用量页](https://www.workbuddy.cn/profile/plans-usage)（CodeBuddy 与 WorkBuddy 同一账号体系）
2. 按 `Option + Cmd + I` 打开开发者工具 → **Network（网络）** 面板
3. 刷新页面，在筛选框输入 `get-user-resource`，点开该请求
4. 在 **Request Headers（请求标头）** 中：
   - 右键 `cookie:` 一行 → **Copy value**（复制值）
   - 右键 `user-agent:` 一行 → **Copy value**（复制值）

> ⚠️ **Cookie 与 User-Agent 必须来自同一个请求**，否则服务端校验 UA 不匹配会返回 401。
> Cookie 等同于登录凭证，请妥善保管，不要分享给任何人；在官网退出登录即可使其立即失效。

## 安装

### 方式一：一键脚本（推荐）

```bash
git clone https://github.com/stevencmy/codebuddy-menubar.git
cd codebuddy-menubar

# 仅安装并手动启动
./setup.sh

# 安装并配置开机自启（LaunchAgent，崩溃自动拉起）
./setup.sh --autostart
```

然后编辑 `~/.codebuddy-menubar.json`，填入上一步复制的 `cookie` 和 `user_agent`，再点菜单栏里的“重新载入配置”（或重启应用）。

### 方式二：手动运行

```bash
python3 -m pip install --user -r requirements.txt
python3 codebuddy_menubar.py
```

首次运行会自动生成 `~/.codebuddy-menubar.json`，填入凭证后点菜单里的“重新载入配置”。

### 方式三：让 AI Agent 一句话装好 🤖

如果你在用 CodeBuddy / Claude Code / Cursor 等 AI 编程助手，把下面这句直接发给它：

```text
帮我装好 https://github.com/stevencmy/codebuddy-menubar 这个 macOS 菜单栏工具并跑起来，
按仓库里的 AGENTS.md 执行，需要我抓 Cookie 时再叫我。
```

Agent 会自动完成：克隆仓库 → 运行安装脚本 → 引导你抓取凭证 → 写入配置 →
重启并验证菜单栏显示。只有"从浏览器复制 Cookie"这一步需要你亲手操作
（登录态在浏览器里，Agent 拿不到），其余全部自动。

> 要求：macOS + Python 3.9+。菜单栏图标为 SF Symbols 渲染的模板图（`bar_icon.png` 已随仓库提供）。

## 配置参考

配置文件：`~/.codebuddy-menubar.json`（完整示例见 [config.example.json](config.example.json)）

| 键 | 默认值 | 说明 |
|---|---|---|
| `cookie` | （必填） | 官网登录态 Cookie |
| `user_agent` | （必填） | 与 Cookie 同一请求的 User-Agent |
| `api_base` | `https://www.workbuddy.cn` | 国际站改为 `https://www.workbuddy.ai` |
| `refresh_minutes` | `30` | 自动刷新间隔（分钟，最小 1） |
| `auto_checkin` | `true` | 每日自动签到 |
| `low_balance` | `100` | 低余额提醒阈值，`0` 关闭 |
| `show_percent` | `true` | 状态栏是否显示百分比（截断保留一位小数，不四舍五入） |
| `bar_icon` | `🐱` | 图标文件缺失时的 emoji 回退 |
| `verify_ssl` | `true` | 代理/TLS 中间层导致证书报错时程序会自动回退为不校验 |
| `package_codes` | 内置 7 个 | 用量接口的套餐筛选码，一般无需修改 |

修改配置后点菜单里的“重新载入配置”即可生效，无需重启。

## 常见问题

**状态栏显示 `?` 是怎么回事？**
点开菜单第一行看错误原因：
- `Cookie 已失效`：官网退出过登录或会话过期（实测 session 有效期约 7 天），重新抓一次凭证即可
- `未配置 Cookie`：编辑 `~/.codebuddy-menubar.json` 填入凭证
- `HTTP xxx` / 其他：网络问题，点“立即刷新”重试

**和 VS Code 的 CodeBuddy-Usage 插件冲突吗？**
不冲突。两者共用同一套接口，签到接口是幂等的（已签到返回 `code=10001`），重复触发也不会重复加分。

**证书报错 / 公司网络下无法请求？**
部分代理软件会对 HTTPS 做中间人解密，程序检测到证书错误后会自动回退为不校验并继续工作。

**会消耗我的积分吗？**
不会。查询用量和签到的接口本身不计费。

**消耗顺序是怎么算的？**
按官方计费规则：**先到期先消耗**（套餐配额、加量包、裂变包等所有积分包放在一起比较到期时间）；到期时间相同时**先扣基础用量、再扣加赠用量**。菜单行首箭头在序号之前：▶ 为接口返回的当前正在扣减的包，▷ 为排队中的包；①②③ 编号即实际扣减先后。基础/加赠的判断依据接口的 `SubProductCode`（含 `bonus_pack` 为加赠类）与套餐名称中的「裂变/赠送/加赠」字样。

**菜单里的各列是怎么对齐的？菜单不是比例字体吗？**
程序通过 PyObjC（rumps 的依赖）以系统菜单字体（`NSFont` + `NSAttributedString`）实测每个单元格的渲染宽度，再按普通空格 → U+2009 细空格 → U+200A 窄空格逐级补齐到目标列宽，对齐残差 < 0.5px；无 PyObjC 测量环境时退化为 CJK=2 的近似对齐。

## 卸载

```bash
./setup.sh --uninstall        # 停止自启 + 删除程序文件
rm ~/.codebuddy-menubar.json  # 如需连同凭证一起删除
```

## License

[MIT](LICENSE)
