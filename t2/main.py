
if __name__ == "__main__":
    """导入三个类"""
    from detect_changes import ChangeDetector
    from conflict_detector import ConflictDetector
    from master_merge import MasterMerger
    # 你的文件夹路径
    base_directory = r"C:\Users\花小譜\Desktop\test\t2"

    try:
        """第一阶段===检测修改"""
        ch_detector = ChangeDetector(base_directory)
        # 执行检测并获取结果（结果可用于后续步骤）
        changes_data = ch_detector.send_changes()
        ch_detector.print_changes()

        """第二阶段===检测冲突"""
        co_detector = ConflictDetector(base_directory, changes_data)
        co_detector.detect_all_conflicts()
        co_detector.print_conflict_report()

        """第三阶段===执行合并"""
        merge = MasterMerger(base_directory, co_detector.conflicts, co_detector.merge_data)
        merge.merge()
        merge.print_merge_report()
    except Exception as e:
        print(f"错误: {str(e)}")
