import sys
import os
import pkg_resources
import subprocess
from p115 import P115Client, P115FileSystem
from sqlite3 import connect
import getopt
import time
import random

def read_file_ids(file_path):
    """从文件中读取文件 ID"""
    with open(file_path, 'r') as f:
        return [int(line.strip()) for line in f.readlines() if line.strip().isdigit()]


def get_path_by_id(con, file_id):
    """根据文件 ID 获取文件的完整路径"""
    def build_path(file_id):
        sql = "SELECT id, parent_id, name FROM data WHERE id = ?"
        cursor = con.execute(sql, (file_id,))
        result = cursor.fetchone()

        if result:
            file_id, parent_id, name = result
            if parent_id == 0:
                return name
            else:
                parent_path = build_path(parent_id)
                return f"{parent_path}/{name}"
        return None

    path = build_path(file_id)
    if path:
        return f"/{path}"
    return None


def get_paths_by_ids(dbfile, file_ids):
    """根据多个文件 ID 获取路径"""
    with connect(dbfile) as con:
        paths = {}
        for file_id in file_ids:
            path = get_path_by_id(con, file_id)
            paths[file_id] = path
        return paths


def write_paths_to_file(output_file, paths):
    """将文件 ID 和路径写入文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for file_id, path in paths.items():
            f.write(f"File ID: {file_id}, Path: {path}\n")


def parse_args():
    """解析命令行参数"""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "")
        if len(args) != 1:
            raise ValueError("请提供文件 ID 列表文件路径作为参数")
        return args[0]
    except getopt.GetoptError as err:
        print(f"参数错误: {err}")
        sys.exit(1)


def read_cookies_from_file(cookies_file):
    """从文件中读取 cookies"""
    with open(cookies_file, 'r', encoding='utf-8') as f:
        return f.read().strip()


def change_extension_to_mkv(path):
    """将文件路径的后缀改为 .mkv"""
    base, ext = os.path.splitext(path)
    if ext.lower() != ".mkv":
        return f"{base}.mkv"
    return path


def main():
    """主函数"""
    # 获取文件 ID 列表
    file_ids_file = parse_args()
    dbfile = "115-115104115.db"
    output_file = "file_paths.txt"  # 输出的路径文件

    # 从文件中读取文件 ID
    file_ids = read_file_ids(file_ids_file)

    # 获取多个文件的路径
    paths = get_paths_by_ids(dbfile, file_ids)

    # 将文件路径写入文件
    write_paths_to_file(output_file, paths)

    print(f"路径信息已写入文件: {output_file}")
    print("准备开始逐个修改文件后缀为 .mkv ...")

    # 创建P115客户端对象
    cookies_file = "115-cookies.txt"  # 设置你的 cookies 文件路径
    cookie = read_cookies_from_file(cookies_file)  # 读取 cookies
    client = P115Client(cookie)
    fs = client.fs  # 获取文件系统对象

    # 执行逐个修改操作，带延迟与重试
    for file_id, old_path in paths.items():
        new_path = change_extension_to_mkv(old_path)
        if new_path == old_path:
            print(f"文件已是 .mkv 无需修改: {old_path}")
            continue

        print(f"开始修改: {old_path} -> {new_path}")
        attempts = 0
        success = False

        while attempts < 3 and not success:
            try:
                fs.rename(old_path, new_path)
                print(f"✅ 修改成功: {old_path} -> {new_path}")
                success = True
            except Exception as e:
                attempts += 1
                wait = random.uniform(5, 10)
                print(f"⚠️ 第 {attempts} 次重试失败: {e}，等待 {wait:.1f}s 后重试...")
                time.sleep(wait)

        if success:
            delay = random.uniform(1.5, 3.0)
            print(f"🕒 等待 {delay:.1f}s 后继续下一个")
            time.sleep(delay)
        else:
            print(f"❌ 放弃修改: {old_path} -> {new_path} after 3 attempts")

    print("🎉 所有文件处理完毕！")
    
if __name__ == "__main__":
    main() 