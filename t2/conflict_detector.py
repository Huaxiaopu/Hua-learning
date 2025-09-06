import os


class ConflictDetector:
    """检测冲突"""

    def __init__(self, base_path, changes):
        """
        初始化冲突检测器
        :param base_path: 根目录路径（包含master、branch_a、branch_b）
        :param changes: 第一步检测到的变化结果（来自ChangeDetector）
        """
        self.base_path = base_path
        self.master_path = os.path.join(base_path, "master")
        self.branch_a_path = os.path.join(base_path, "branch_a")
        self.branch_b_path = os.path.join(base_path, "branch_b")
        self.changes = changes  # 包含两个分支的新增和修改文件信息

        # 存储冲突信息
        self.conflicts = {
            "new_files_conflict": [],  # 新增同名文件冲突
            "modified_files_conflict": []  # 修改内容冲突
        }

        # 存储可合并内容
        self.merge_data = {
            "new_files": [],  # 可直接合并的新增文件
            "modified_files": {}  # 可直接合并的修改文件（路径: 内容）
        }

    @staticmethod
    def _read_file_lines(file_path):
        """读取文件内容为行列表（不存在则返回空列表）"""
        if not os.path.exists(file_path):
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()

    def _check_new_files_conflict(self):
        """检查新增文件是否有冲突（ab新增同名文件）"""
        a_new = set(self.changes["branch_a"]["new"])
        b_new = set(self.changes["branch_b"]["new"])

        # 找出ab都新增的同名文件（冲突）
        new_conflict_files = a_new & b_new  # 集合交集
        self.conflicts["new_files_conflict"] = list(new_conflict_files)

        # 找出ab新增的不同名文件（可直接合并）
        a_unique_new = a_new - new_conflict_files
        b_unique_new = b_new - new_conflict_files

        # 记录可合并的新增文件（(文件路径, 来源分支)）
        for file in a_unique_new:
            self.merge_data["new_files"].append((file, "branch_a"))
        for file in b_unique_new:
            self.merge_data["new_files"].append((file, "branch_b"))

    def _check_modified_files_conflict(self):
        """检查修改文件是否有冲突（同一文件同一位置修改内容不同）"""
        # 找出ab都修改过的文件
        a_modified = set(self.changes["branch_a"]["modified"])
        b_modified = set(self.changes["branch_b"]["modified"])
        common_modified = a_modified & b_modified  # 双方都修改的文件

        # 处理只被一个分支修改的文件（可直接合并）
        a_unique_modified = a_modified - common_modified
        b_unique_modified = b_modified - common_modified

        for file in a_unique_modified:
            file_path = os.path.join(self.branch_a_path, file)
            self.merge_data["modified_files"][file] = self._read_file_lines(file_path)

        for file in b_unique_modified:
            file_path = os.path.join(self.branch_b_path, file)
            self.merge_data["modified_files"][file] = self._read_file_lines(file_path)

        # 检查双方都修改的文件是否有内容冲突
        for file in common_modified:
            # 读取三个版本的文件内容
            master_lines = self._read_file_lines(os.path.join(self.master_path, file))
            a_lines = self._read_file_lines(os.path.join(self.branch_a_path, file))
            b_lines = self._read_file_lines(os.path.join(self.branch_b_path, file))

            # 检测行级冲突
            has_conflict, merged_lines = self._detect_line_conflict(master_lines, a_lines, b_lines)

            if has_conflict:
                # 有冲突，记录冲突文件和内容
                self.conflicts["modified_files_conflict"].append(file)
                # 存储带有冲突标记的内容，后续写入master
                self.merge_data["modified_files"][file] = merged_lines
            else:
                # 无冲突，直接使用合并后的内容
                self.merge_data["modified_files"][file] = merged_lines

    @staticmethod
    def _detect_line_conflict(master_lines, a_lines, b_lines):
        """
        检测同一文件的行级冲突
        :param master_lines: master中的文件内容（行列表）
        :param a_lines: branch_a中的文件内容（行列表）
        :param b_lines: branch_b中的文件内容（行列表）
        :return: (是否有冲突, 合并后的行列表)
        """
        max_length = max(len(master_lines), len(a_lines), len(b_lines))
        merged = []
        has_conflict = False

        for i in range(max_length):
            # 获取当前行（处理索引超出范围的情况）
            master_line = master_lines[i].rstrip('\n') if i < len(master_lines) else None
            a_line = a_lines[i].rstrip('\n') if i < len(a_lines) else None
            b_line = b_lines[i].rstrip('\n') if i < len(b_lines) else None

            # 情况1: 都和master相同，直接用master内容
            if a_line == master_line and b_line == master_line:
                merged.append(master_line + '\n' if master_line is not None else '')

            # 情况2: a修改，b未修改，用a的内容
            elif a_line != master_line and b_line == master_line:
                merged.append(a_line + '\n' if a_line is not None else '')

            # 情况3: b修改，a未修改，用b的内容
            elif a_line == master_line and b_line != master_line:
                merged.append(b_line + '\n' if b_line is not None else '')

            # 情况4: 两者都修改但内容相同，用修改后的内容
            elif a_line == b_line and a_line != master_line:
                merged.append(a_line + '\n' if a_line is not None else '')

            # 情况5: 两者都修改且内容不同，标记冲突
            else:
                has_conflict = True
                merged.append("<<<<<<< branch_a\n")
                merged.append(a_line + '\n' if a_line is not None else '')
                merged.append("=======\n")
                merged.append(b_line + '\n' if b_line is not None else '')
                merged.append(">>>>>>> branch_b\n")

        return has_conflict, merged

    def detect_all_conflicts(self):
        """检测所有类型的冲突"""
        # 检查新增文件冲突
        self._check_new_files_conflict()
        # 检查修改文件冲突
        self._check_modified_files_conflict()

        return self.conflicts, self.merge_data

    def print_conflict_report(self):
        """打印冲突报告"""
        print("\n=== 冲突检测报告 ===")

        # 新增文件冲突
        if self.conflicts["new_files_conflict"]:
            print(f"\n新增文件冲突 ({len(self.conflicts['new_files_conflict'])}个):")
            for file in self.conflicts["new_files_conflict"]:
                print(f"  - {file}: branch_a和branch_b都新增了同名文件")

        # 修改文件冲突
        if self.conflicts["modified_files_conflict"]:
            print(f"\n修改内容冲突 ({len(self.conflicts['modified_files_conflict'])}个):")
            for file in self.conflicts["modified_files_conflict"]:
                print(f"  - {file}: 同一位置修改内容不同")

        # 无冲突情况
        if not any(self.conflicts.values()):
            print("\n未检测到任何冲突，可以安全合并")

        # 可合并内容统计
        print(f"\n可合并内容:")
        print(f"  新增文件: {len(self.merge_data['new_files'])}个")
        print(f"  修改文件: {len(self.merge_data['modified_files'])}个")
