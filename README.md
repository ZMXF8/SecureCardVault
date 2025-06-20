# 🔐 SecureCardVault - 本地加密银行卡密码本

一个图形界面离线运行的密码本程序，用于本地保存银行卡号和密码，数据加密存储、安全可靠。支持打包为 `.exe`，在没有 Python 环境的 Windows 上运行。

## ✨ 功能特色

- ✅ 主密码加密保护（Fernet 对称加密）
- ✅ 图形界面操作，使用简单
- ✅ 支持添加、查看、删除银行卡密码
- ✅ 文件完整性检测，避免数据丢失
- ✅ 可打包为 Windows 独立软件（无需 Python）

## 🧰 环境依赖

- Python 3.8+
- tkinter（Python自带）
- cryptography
## 🚀 启动方式

```bash
python SecureCardVault.py
```

或使用：

```bash
pyinstaller --noconfirm --onefile --windowed main.py
```
