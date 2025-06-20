import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from cryptography.fernet import Fernet
from hashlib import sha256
import json
import os
import base64

# ========== 路径和文件定义 ==========
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
KEA_DIR = os.path.join(BASE_DIR, 'kea')
DATA_FILE = os.path.join(KEA_DIR, 'secure_data.json')
CONFIG_FILE = os.path.join(KEA_DIR, 'config.json')

DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'admin'

def derive_key(password: str) -> bytes:
    return base64.urlsafe_b64encode(sha256(password.encode()).digest())

class PasswordManager:
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 银行卡密码本 - 登录")
        self.root.geometry("360x280")
        self.root.resizable(False, False)

        self.ensure_kea_dir()
        self.load_config()

        self.login_screen()

    def ensure_kea_dir(self):
        if not os.path.exists(KEA_DIR):
            os.makedirs(KEA_DIR)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def check_file_integrity(self):
        # 简单校验：文件存在且大小大于0
        if not os.path.exists(DATA_FILE) or not os.path.exists(CONFIG_FILE):
            return False
        if os.path.getsize(DATA_FILE) == 0 or os.path.getsize(CONFIG_FILE) == 0:
            return False
        return True

    def login_screen(self):
        self.clear_window()

        # 顶部状态提示区域
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, fill='x')

        if not os.path.exists(DATA_FILE) or not os.path.exists(CONFIG_FILE):
            warning_msg = "⚠️ 重要警告：密码存储目录或文件被删除，所有密码数据将丢失！"
            fg_color = "red"
        else:
            warning_msg = "✔️ 文件检测正常"
            fg_color = "green"

        self.status_label = tk.Label(top_frame, text=warning_msg, fg=fg_color,
                                     font=("Arial", 10, "bold"), wraplength=340)
        self.status_label.pack()

        # 登录输入框区域
        login_frame = tk.Frame(self.root)
        login_frame.pack(pady=10)

        tk.Label(login_frame, text="账号").grid(row=0, column=0, pady=5, sticky="e")
        self.username_entry = tk.Entry(login_frame)
        self.username_entry.grid(row=0, column=1, padx=5)
        self.username_entry.focus_set()

        tk.Label(login_frame, text="密码").grid(row=1, column=0, pady=5, sticky="e")
        self.password_entry = tk.Entry(login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5)

        # 文件校验状态显示区（在登录框下方）
        check_frame = tk.Frame(self.root)
        check_frame.pack(pady=8, fill='x')
        file_check_passed = self.check_file_integrity()
        if file_check_passed:
            file_check_msg = "文件校验通过"
            file_check_color = "green"
        else:
            file_check_msg = "文件异常，请检查数据文件"
            file_check_color = "red"

        self.file_check_label = tk.Label(check_frame, text=file_check_msg, fg=file_check_color,
                                         font=("Arial", 10, "bold"))
        self.file_check_label.pack()

        # 按钮区域
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="登录", width=15, command=self.check_login).pack(pady=5)
        tk.Button(btn_frame, text="忘记主密码？查看提示", width=20, command=self.show_hint).pack()

    def check_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username == DEFAULT_USERNAME and password == DEFAULT_PASSWORD:
            self.input_master_password()
        else:
            messagebox.showerror("登录失败", "账号或密码错误")

    def input_master_password(self):
        if 'master_password_hint' not in self.config:
            self.set_master_password()
        else:
            self.ask_master_password()

    def set_master_password(self):
        self.master_password = simpledialog.askstring("主密码设置", "首次使用，请设置主密码：", show="*")
        if not self.master_password:
            messagebox.showerror("错误", "必须设置主密码")
            self.root.destroy()
            return
        hint = simpledialog.askstring("设置提示", "请设置一个主密码提示（帮助你回忆主密码）:")
        if not hint:
            hint = "无提示"
        self.config['master_password_hint'] = hint
        self.save_config()
        self.fernet = Fernet(derive_key(self.master_password))
        self.data = {}
        self.save_data()
        self.show_main_screen()

    def ask_master_password(self):
        pwd = simpledialog.askstring("主密码", "请输入主密码以解锁数据：", show="*")
        if not pwd:
            messagebox.showerror("错误", "必须输入主密码")
            return
        self.master_password = pwd
        self.fernet = Fernet(derive_key(self.master_password))
        try:
            self.data = self.load_data()
            self.show_main_screen()
        except Exception:
            messagebox.showerror("错误", "主密码错误或数据损坏")
            self.master_password = None

    def show_hint(self):
        hint = self.config.get('master_password_hint', None)
        if hint:
            messagebox.showinfo("主密码提示", f"你的主密码提示是：\n\n{hint}")
        else:
            messagebox.showinfo("提示", "未设置主密码提示")

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {}
        with open(DATA_FILE, 'rb') as f:
            encrypted = f.read()
        decrypted = self.fernet.decrypt(encrypted).decode()
        return json.loads(decrypted)

    def save_data(self):
        encrypted = self.fernet.encrypt(json.dumps(self.data).encode())
        with open(DATA_FILE, 'wb') as f:
            f.write(encrypted)

    def show_main_screen(self):
        self.root.title("🔐 银行卡密码本")
        self.root.geometry("560x460")
        self.clear_window()

        frame = tk.LabelFrame(self.root, text="添加银行卡信息", padx=10, pady=10)
        frame.pack(padx=10, pady=10, fill="x")

        tk.Label(frame, text="名称：").grid(row=0, column=0, sticky="e")
        tk.Label(frame, text="卡号：").grid(row=1, column=0, sticky="e")
        tk.Label(frame, text="密码：").grid(row=2, column=0, sticky="e")

        self.name_entry = tk.Entry(frame, width=40)
        self.card_entry = tk.Entry(frame, width=40)
        self.pin_entry = tk.Entry(frame, show="*", width=40)

        self.name_entry.grid(row=0, column=1, pady=3)
        self.card_entry.grid(row=1, column=1, pady=3)
        self.pin_entry.grid(row=2, column=1, pady=3)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="➕ 添加", width=10, command=self.add_card).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="👁️ 显示密码", width=12, command=self.show_password).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="🗑️ 删除", width=10, command=self.delete_card).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="🔒 退出", width=10, command=self.root.quit).grid(row=0, column=3, padx=5)

        self.tree = ttk.Treeview(self.root, columns=("卡号", "密码"), show="headings", height=12)
        self.tree.heading("卡号", text="卡号")
        self.tree.heading("密码", text="密码")
        self.tree.column("卡号", width=220)
        self.tree.column("密码", width=160)
        self.tree.pack(fill=tk.BOTH, padx=10, pady=10)

        self.refresh_list()

    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        for name, info in self.data.items():
            masked_card = "**** **** **** " + info["card_number"][-4:]
            masked_pin = "*" * len(info["card_pin"])
            self.tree.insert('', tk.END, iid=name, values=(masked_card, masked_pin))

    def add_card(self):
        name = self.name_entry.get().strip()
        card = self.card_entry.get().strip().replace(" ", "")
        pin = self.pin_entry.get().strip()

        if not name or not card or not pin:
            messagebox.showwarning("未填写", "请填写所有字段")
            return

        if name in self.data:
            messagebox.showwarning("重复", "该名称已存在")
            return

        self.data[name] = {"card_number": card, "card_pin": pin}
        self.save_data()
        self.refresh_list()

        self.name_entry.delete(0, tk.END)
        self.card_entry.delete(0, tk.END)
        self.pin_entry.delete(0, tk.END)

        messagebox.showinfo("成功", f"已保存【{name}】的银行卡信息")

    def delete_card(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("未选择", "请选择一条记录")
            return
        name = selected[0]
        confirm = messagebox.askyesno("确认删除", f"确认删除【{name}】的信息？")
        if confirm:
            del self.data[name]
            self.save_data()
            self.refresh_list()

    def show_password(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("未选择", "请选择一条记录")
            return
        name = selected[0]
        pin = self.data[name]["card_pin"]
        messagebox.showinfo("明文密码", f"【{name}】的密码是：\n\n{pin}")

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordManager(root)
    root.mainloop()
