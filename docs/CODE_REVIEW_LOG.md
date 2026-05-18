# Hermes 代码评审记录

## 2026-05-18 基线原型评审

范围：

```text
FastAPI MVP
Web 客户端原型
产品开发计划文档
```

结论：

```text
通过，作为后续桌面化开发基线。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
GET /api/health
GET /
GET /static/styles.css
```

风险：

```text
当前尚未初始化 Git 仓库。
桌面壳、系统托盘、本地 token、打包流程还未完成。
```

## 2026-05-18 阶段 1 桌面壳与本地服务评审

范围：

```text
本地 token API 保护
DesktopServiceManager
PySide6 桌面窗口
QtWebEngine 加载本地 UI
系统托盘菜单
桌面数据目录初始化
桌面启动说明
```

结论：

```text
通过，形成可提交点 stage-1-desktop-shell-local-service。
```

已验证：

```text
python -m compileall hermes_app desktop tests
python -m pytest -q
DesktopServiceManager 随机端口启动与关闭
无 token 访问受保护 API 返回 401
带 X-Hermes-Token 访问受保护 API 返回 200
HermesDesktopWindow 非交互式构造成功
QSystemTrayIcon.isSystemTrayAvailable() 返回 True
```

评审结论：

```text
API token 中间件只在 HERMES_LOCAL_TOKEN 存在时启用，不影响普通开发模式。
桌面服务只绑定 127.0.0.1，符合本地应用安全边界。
DesktopServiceManager 会恢复环境变量，避免测试污染。
桌面窗口关闭时默认隐藏到托盘，退出菜单会停止本地服务。
```

遗留事项：

```text
当前全局 Python 环境中的 PySide6 会输出 NumPy 2.x 兼容性警告；requirements-desktop.txt 已固定 numpy<2，正式桌面环境需按该依赖安装。
尚未实现桌面日志滚动文件。
已初始化 Git 仓库并推送 GitHub main 分支。
```

提交记录：

```text
f3e3241 stage 1 desktop shell and local service
```

## 2026-05-18 阶段 1 桌面日志系统评审

范围：

```text
desktop/logging_config.py
DesktopServiceManager 日志接入
HermesDesktopWindow 日志接入
日志单元测试
```

结论：

```text
通过，形成可提交点 stage-1-desktop-logging。
```

已验证：

```text
python -m compileall desktop tests
python -m pytest -q
```

评审结论：

```text
日志写入 %APPDATA%/Hermes/logs/desktop.log 或 HERMES_DESKTOP_HOME/logs/desktop.log。
RotatingFileHandler 单文件 2MB，最多保留 5 份，满足桌面 MVP 的本地诊断需求。
setup_desktop_logging(reset=True) 支持测试隔离，避免重复 handler。
服务启动、服务就绪、服务停止、窗口初始化、托盘初始化、退出路径均已记录。
```

提交记录：

```text
待提交：stage-1-desktop-logging
```
