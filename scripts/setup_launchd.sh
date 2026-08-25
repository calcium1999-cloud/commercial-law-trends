#!/bin/bash
# setup_launchd.sh — 安装/卸载 launchd 自动调度
# 使用:
#   bash setup_launchd.sh install    # 安装调度
#   bash setup_launchd.sh uninstall  # 卸载调度
#   bash setup_launchd.sh status     # 查看状态

PLIST_NAME="com.endofmay.commercial-law-weekly"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="${PROJECT_DIR}/scripts/${PLIST_NAME}.plist"
PLIST_DST="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

case "$1" in
    install)
        mkdir -p "$HOME/Library/LaunchAgents"
        cp "$PLIST_SRC" "$PLIST_DST"
        launchctl unload "$PLIST_DST" 2>/dev/null
        launchctl load "$PLIST_DST"
        echo "调度已安装: $PLIST_NAME"
        echo "运行时间: 每周一/三/五 09:00"
        echo "日志: ${PROJECT_DIR}/logs/"
        ;;
    uninstall)
        launchctl unload "$PLIST_DST" 2>/dev/null
        rm -f "$PLIST_DST"
        echo "调度已卸载: $PLIST_NAME"
        ;;
    status)
        launchctl list "$PLIST_NAME" 2>/dev/null && echo "状态: 运行中" || echo "状态: 未安装"
        ;;
    *)
        echo "用法: bash $0 {install|uninstall|status}"
        exit 1
        ;;
esac
