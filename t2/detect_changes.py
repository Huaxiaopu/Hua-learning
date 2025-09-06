import os
import filecmp


class ChangeDetector:
    """检测修改"""
    def __init__(self, base_path):
        # 初始化路径（三个文件夹的绝对路径）
        self.base_path = base_path
        self.master_path = os.path.join(base_path, "master")
        self.branch_a_path = os.path.join(base_path, "branch_a")
        self.branch_b_path = os.path.join(base_path, "branch_b")

        # 验证路径是否存在
        self._validate_paths()

    def _validate_paths(self):
        """验证三个文件夹是否存在"""
        for path in [self.master_path, self.branch_a_path, self.branch_b_path]:
            if not os.path.exists(path) or not os.path.isdir(path):
                raise FileNotFoundError(f"文件夹不存在: {path}")

    @staticmethod
    def _get_all_files(root_dir):
        """获取指定目录下所有文件的相对路径列表"""
        file_list = []
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                # 计算相对路径（相对于root_dir）
                # 显式转换为str，确保类型匹配
                file_path: str = str(os.path.join(dirpath, filename))
                rel_path = os.path.relpath(file_path, root_dir)  # 此时两个参数都是str，类型匹配
                file_list.append(rel_path)
        return file_list

    @staticmethod
    def _is_file_modified(master_file, branch_file):
        """判断分支文件相对于master文件是否被修改"""
        # 检查文件是否存在
        if not os.path.exists(master_file):
            return True  # master中不存在，属于新增文件
        if not os.path.exists(branch_file):
            return False  # 分支中不存在该文件

        # 比较文件内容
        return not filecmp.cmp(master_file, branch_file, shallow=False)

    def detect_changes(self, branch_name):
        """
        检测指定分支相对于master的变化
        branch_name: 分支名称，"branch_a" 或 "branch_b"
        返回: (新增文件列表, 修改文件列表)
        """
        # 确定分支路径
        branch_path = self.branch_a_path if branch_name == "branch_a" else self.branch_b_path

        # 获取master和分支中的所有文件
        master_files = ChangeDetector._get_all_files(self.master_path)
        branch_files = ChangeDetector._get_all_files(branch_path)

        # 新增文件：分支有，master没有
        new_files = [f for f in branch_files if f not in master_files]

        # 修改文件：两边都有，但内容不同
        modified_files = []
        for file in branch_files:
            if file in master_files:
                master_file = os.path.join(self.master_path, file)
                branch_file = os.path.join(branch_path, file)
                if self._is_file_modified(master_file, branch_file):
                    modified_files.append(file)

        return new_files, modified_files

    def send_changes(self):
        """返回change检测结果以供后续使用"""
        # 检测branch_a的变化
        a_new, a_modified = self.detect_changes("branch_a")
        # 检测branch_b的变化
        b_new, b_modified = self.detect_changes("branch_b")
        return {
            "branch_a": {"new": a_new, "modified": a_modified},
            "branch_b": {"new": b_new, "modified": b_modified}
        }

    def print_changes(self):
        """仅负责打印结果：调用send_changes获取字典，再解析字典打印"""
        # 关键步骤：调用self.send_changes()获取返回的字典
        changes_dict = self.send_changes()  # changes_dict就是send_changes返回的那套字典

        # 从字典中提取branch_a的新增/修改文件（按字典的键逐层获取）
        a_new = changes_dict["branch_a"]["new"]
        a_modified = changes_dict["branch_a"]["modified"]

        # 从字典中提取branch_b的新增/修改文件
        b_new = changes_dict["branch_b"]["new"]
        b_modified = changes_dict["branch_b"]["modified"]

        # 后续打印逻辑和之前完全一样，只是数据来源从“重复调用detect_changes”变成了“解析字典”
        print(f"=== 分支差异检测结果 ===")
        print(f"基准目录: {self.base_path}")

        print("\n[branch_a 相对于 master 的变化]")
        print(f"  新增文件: {len(a_new)}个")
        for file in a_new:
            print(f"    - {file}")
        print(f"  修改文件: {len(a_modified)}个")
        for file in a_modified:
            print(f"    - {file}")

        print("\n[branch_b 相对于 master 的变化]")
        print(f"  新增文件: {len(b_new)}个")
        for file in b_new:
            print(f"    - {file}")
        print(f"  修改文件: {len(b_modified)}个")
        for file in b_modified:
            print(f"    - {file}")
