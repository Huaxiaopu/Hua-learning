import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import Toplevel, Label, Button

# 文件分类规则
file_types = {
    "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "文档": [".pdf", ".docx", ".txt", ".md"],
    "压缩包": [".zip", ".rar", ".7z"],
    "音频": [".mp3", ".wav", ".flac", ".m4a"],
    "视频": [".mp4", ".avi", ".mov"],
    "代码": [".py", ".js", ".html"],
    "应用程序": [".exe", ".msi", ".apk"],
    "设计": [".psd", ".ai", ".fig"],
    "电子书": [".epub", ".mobi"],
    "配置": [".json", ".yaml", ".env"]
}


def select_target_folder():
    """弹出对话框让用户选择目标文件夹"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    folder = filedialog.askdirectory(
        title="请选择要整理的文件夹",
        initialdir=os.path.expanduser("~")  # 默认打开用户目录
    )
    root.destroy()  # 关闭临时窗口
    return folder if folder else None  # 如果用户取消选择，返回 None


def ask_overwrite(filename):
    """自定义弹窗，按钮显示为：覆盖/跳过/重命名/终止"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    root.attributes('-topmost', True)  # 置顶

    # 创建自定义弹窗
    dialog = Toplevel(root)
    dialog.title("文件冲突")
    dialog.attributes('-topmost', True)  # 确保弹窗置顶

    # 弹窗内容
    Label(dialog, text=f"文件 '{filename}' 已存在，如何处理？").pack(padx=20, pady=10)

    # 存储用户的选择
    user_choice = None

    def on_click(choice):
        nonlocal user_choice
        user_choice = choice
        dialog.destroy()

    # 自定义按钮
    Button(dialog, text="覆盖", command=lambda: on_click("overwrite")).pack(side="left", padx=5, pady=10)
    Button(dialog, text="跳过", command=lambda: on_click("skip")).pack(side="left", padx=5, pady=10)
    Button(dialog, text="重命名", command=lambda: on_click("rename")).pack(side="left", padx=5, pady=10)
    Button(dialog, text="终止", command=lambda: on_click(None)).pack(side="left", padx=5, pady=10)

    # 等待用户选择
    dialog.wait_window(dialog)
    root.destroy()  # 关闭临时窗口
    return user_choice


def safe_move(src, dst):
    """安全备份文件（递归检测重命名冲突）"""
    if not os.path.exists(dst):  # 目标文件不存在，直接复制
        shutil.copy2(src, dst)
        print(f"[备份] {os.path.basename(src)} -> {os.path.dirname(dst)}")
        return True

    filename = os.path.basename(dst)
    choice = ask_overwrite(filename)  # 调用弹窗函数

    if choice is None:  # 用户点击"终止"
        raise InterruptedError("用户终止操作")
    elif choice == "skip":  # 用户点击"跳过"
        print(f"[跳过] 已保留原文件: {dst}")
        return False
    elif choice == "overwrite":  # 用户点击"覆盖"
        shutil.copy2(src, dst)
        print(f"[覆盖] 已更新文件: {dst}")
        return True
    elif choice == "rename":  # 用户点击"重命名"
        base, ext = os.path.splitext(filename)
        dirname = os.path.dirname(dst)

        while True:  # 循环直到命名成功或用户取消
            # 弹出输入框让用户输入新文件名
            new_name = simpledialog.askstring(
                "重命名文件",
                f"文件 '{base}{ext}' 已存在，请输入新名称（不含扩展名 {ext}）:",
                initialvalue=base
            )

            if not new_name:  # 用户点击"取消"
                print(f"[取消重命名] 跳过文件: {filename}")
                return False

            new_dst = os.path.join(dirname, f"{new_name}{ext}")

            if not os.path.exists(new_dst):  # 新名称无冲突
                shutil.copy2(src, new_dst)
                print(f"[重命名] 文件已备份为: {new_name}{ext}")
                return True
            else:  # 新名称仍然冲突，继续循环
                base = new_name  # 下次弹窗默认显示用户刚输入的名字
                print(f"[冲突] 名称 '{new_name}{ext}' 仍已存在，请重新输入")


def get_file_category(ext):
    """根据扩展名获取文件分类"""
    ext = ext.lower()
    for category, extensions in file_types.items():
        if ext in extensions:
            return category
    return None


def check_existing_folders(target_folder):
    """检查已分类文件夹中的文件是否正确"""
    for category in file_types.keys():
        category_dir = os.path.join(target_folder, category)
        if os.path.exists(category_dir):
            for filename in os.listdir(category_dir):
                filepath = os.path.join(category_dir, filename)
                if os.path.isfile(filepath):
                    _, ext = os.path.splitext(filename)
                    correct_category = get_file_category(ext)
                    if correct_category != category:
                        # 移动到正确的分类
                        correct_dir = os.path.join(target_folder,
                                                   correct_category) if correct_category else os.path.join(
                            target_folder, "垃圾桶")
                        os.makedirs(correct_dir, exist_ok=True)
                        dst_path = os.path.join(correct_dir, filename)
                        try:
                            safe_move(filepath, dst_path)
                        except InterruptedError:
                            print("操作被用户取消")
                            break  # 终止整个分类流程
                        print(
                            f"[纠正] {filename} 从 {category} 移动到 {correct_category if correct_category else '垃圾桶'}")


def organize_files():
    """整理文件（动态获取目标文件夹）"""
    # 让用户选择文件夹
    target_folder = select_target_folder()
    if not target_folder:
        print("[取消] 未选择文件夹")
        return

    # 检查文件夹是否存在
    if not os.path.exists(target_folder):
        messagebox.showerror("错误", f"文件夹不存在: {target_folder}")
        return

    print(f"=== 开始整理: {target_folder} ===")

    # 先检查已有分类文件夹中的文件是否正确
    check_existing_folders(target_folder)

    # 创建垃圾桶文件夹
    trash_dir = os.path.join(target_folder, "垃圾桶")
    os.makedirs(trash_dir, exist_ok=True)

    # 递归处理所有文件和子文件夹
    for root, dirs, files in os.walk(target_folder):
        # 跳过已经分类的文件夹和垃圾桶
        if os.path.basename(root) in file_types.keys() or os.path.basename(root) == "垃圾桶":
            continue

        for filename in files:
            filepath = os.path.join(root, filename)

            # 获取文件扩展名
            _, ext = os.path.splitext(filename)
            category = get_file_category(ext)

            if category:
                # 创建分类文件夹
                dest_dir = os.path.join(target_folder, category)
                os.makedirs(dest_dir, exist_ok=True)

                # 复制文件到分类文件夹
                dst_path = os.path.join(dest_dir, filename)
                try:
                    if safe_move(filepath, dst_path):  # 调用安全移动函数
                        print(f"[备份] {filename} -> {category}")
                except Exception as e:
                    print(f"[错误] 无法备份 {filename}: {str(e)}")
            else:
                # 移动到垃圾桶
                try:
                    shutil.move(filepath, os.path.join(trash_dir, filename))
                    print(f"[清理] {filename} -> 垃圾桶")
                except Exception as e:
                    print(f"[错误] 无法移动 {filename} 到垃圾桶: {str(e)}")

    print("=== 整理完成 ===")


if __name__ == "__main__":
    print("=== 文件整理开始 ===")
    organize_files()
    print("=== 整理完成 ===")