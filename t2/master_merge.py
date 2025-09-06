import os
import shutil


class MasterMerger:
    def __init__(self, base_path, conflicts, merge_data):
        """
        初始化合并器
        :param base_path: 根目录路径
        :param conflicts: 第二阶段检测到的冲突信息
        :param merge_data: 第二阶段准备的可合并数据
        """
        self.base_path = base_path
        self.master_path = os.path.join(base_path, "master")
        self.branch_a_path = os.path.join(base_path, "branch_a")
        self.branch_b_path = os.path.join(base_path, "branch_b")
        self.conflicts = conflicts
        self.merge_data = merge_data

        # 记录合并结果
        self.merge_result = {
            "success_new": [],  # 成功合并的新增文件
            "success_modified": [],  # 成功合并的修改文件
            "conflict_files": []  # 存在冲突的文件（需手动处理）
        }

    def _copy_new_file(self, file_path, source_branch):
        """复制新增文件到master"""
        # 确定源文件路径
        if source_branch == "branch_a":
            source_path = os.path.join(self.branch_a_path, file_path)
        else:
            source_path = os.path.join(self.branch_b_path, file_path)

        # 确定目标文件路径
        target_path = os.path.join(self.master_path, file_path)

        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # 复制文件
        shutil.copy2(source_path, target_path)
        return target_path

    def _write_modified_file(self, file_path, content_lines):
        """将修改后的内容写入master文件"""
        target_path = os.path.join(self.master_path, file_path)

        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # 写入内容
        with open(target_path, 'w', encoding='utf-8') as f:
            f.writelines(content_lines)
        return target_path

    def merge(self):
        """执行合并操作"""
        # 1. 处理新增文件
        for file_path, source_branch in self.merge_data["new_files"]:
            try:
                self._copy_new_file(file_path, source_branch)
                self.merge_result["success_new"].append(file_path)
            except Exception as e:
                print(f"警告：新增文件 {file_path} 合并失败 - {str(e)}")

        # 2. 处理修改文件
        for file_path, content_lines in self.merge_data["modified_files"].items():
            try:
                self._write_modified_file(file_path, content_lines)
                self.merge_result["success_modified"].append(file_path)
            except Exception as e:
                print(f"警告：修改文件 {file_path} 合并失败 - {str(e)}")

        # 3. 收集所有冲突文件
        self.merge_result["conflict_files"] = (
                self.conflicts["new_files_conflict"] +
                self.conflicts["modified_files_conflict"]
        )

        return self.merge_result

    def print_merge_report(self):
        """打印合并报告"""
        print("\n=== 合并到master结果报告 ===")

        # 成功合并的新增文件
        print(f"\n成功合并新增文件: {len(self.merge_result['success_new'])}个")
        for file in self.merge_result["success_new"]:
            print(f"  + {file}")

        # 成功合并的修改文件
        print(f"\n成功合并修改文件: {len(self.merge_result['success_modified'])}个")
        for file in self.merge_result["success_modified"]:
            # 检查是否是冲突文件
            is_conflict = file in self.conflicts["modified_files_conflict"]
            status = "(含冲突标记)" if is_conflict else ""
            print(f"  * {file} {status}")

        # 冲突文件提示
        if self.merge_result["conflict_files"]:
            print(f"\n需手动处理的冲突文件: {len(self.merge_result['conflict_files'])}个")
            for file in self.merge_result["conflict_files"]:
                if file in self.conflicts["new_files_conflict"]:
                    print(f"  ! {file}: 两个分支都新增了同名文件，请手动选择保留哪个版本")
                else:
                    print(f"  ! {file}: 存在内容冲突，请打开master中的文件解决冲突标记")

        print("\n合并操作已完成！")
