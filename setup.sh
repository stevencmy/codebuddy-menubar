#!/bin/bash
# CodeBuddy Menubar 一键安装/卸载脚本
#   ./setup.sh              安装依赖 + 复制文件（手动启动）
#   ./setup.sh --autostart  安装 + 配置 LaunchAgent 开机自启并立即启动
#   ./setup.sh --uninstall  停止自启 + 删除程序文件
set -euo pipefail

LABEL="com.codebuddy.menubar"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$HOME/Library/Application Support/codebuddy-menubar"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PYTHON="${PYTHON:-python3}"

install_app() {
  echo "==> [1/3] 安装依赖 (rumps / requests)"
  "$PYTHON" -m pip install --user -q -r "$SRC_DIR/requirements.txt"

  echo "==> [2/3] 复制文件到 $APP_DIR"
  mkdir -p "$APP_DIR"
  cp "$SRC_DIR/codebuddy_menubar.py" "$APP_DIR/"
  cp "$SRC_DIR/bar_icon.png" "$APP_DIR/"

  if [ "${1:-}" = "--autostart" ]; then
    echo "==> [3/3] 配置开机自启 (LaunchAgent)"
    mkdir -p "$HOME/Library/LaunchAgents"
    cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$("$PYTHON" -c 'import sys; print(sys.executable)')</string>
        <string>$APP_DIR/codebuddy_menubar.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>ProcessType</key>
    <string>Interactive</string>
    <key>StandardOutPath</key>
    <string>/tmp/codebuddy-menubar.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/codebuddy-menubar.log</string>
</dict>
</plist>
PLIST
    launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null \
      || launchctl kickstart -k "gui/$(id -u)/$LABEL"
    echo "==> 已启动！看看菜单栏右上角。"
    echo "    首次使用请编辑 ~/.codebuddy-menubar.json 填入 cookie / user_agent,"
    echo "    然后点菜单里的「重新载入配置」。"
  else
    echo "==> [3/3] 完成！手动启动："
    echo "    \"$PYTHON\" \"$APP_DIR/codebuddy_menubar.py\""
    echo "    （需要开机自启请运行: ./setup.sh --autostart）"
  fi
}

uninstall_app() {
  echo "==> 停止并移除开机自启"
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "==> 删除程序文件"
  rm -rf "$APP_DIR"
  echo "==> 完成。凭证配置保留在 ~/.codebuddy-menubar.json"
  echo "    如需彻底删除请执行: rm ~/.codebuddy-menubar.json"
}

case "${1:-}" in
  --autostart) install_app --autostart ;;
  --uninstall) uninstall_app ;;
  -h|--help)
    sed -n '2,6p' "$0" ;;
  *) install_app ;;
esac
