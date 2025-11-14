import ctypes
import os
import sys

from typing import List
from flask import Flask, render_template, request, jsonify


def is_already_running():
    mutex_name = "touch-fish-reader"

    # 使用CreateMutexA函数创建互斥锁
    handle = ctypes.windll.kernel32.CreateMutexA(None, False, mutex_name)

    # 检查错误代码，如果已经存在，则返回ERROR_ALREADY_EXISTS
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == 183:  # ERROR_ALREADY_EXISTS
        return True
    else:
        return False


# 获取 base 路径
if getattr(sys, 'frozen', False):
    # exe 打包后，临时解压目录
    base_path = sys._MEIPASS
else:
    # 脚本运行
    base_path = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(base_path, 'templates'),
    static_folder=os.path.join(base_path, 'static')
)

# 默认页大小
PAGE_SIZE = 5
BOOK_PATH = "D:\\project\\demo1\\xg.txt"
CONFIG_MAP = {}
MARK_LINE_BREAK = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/spring")
def spring():
    return render_template("spring.html")


@app.route("/r")
def read_file_endpoint():
    try:
        page_number = request.args.get("pn", type=int)
        if page_number is None:
            return jsonify({"error": "缺少参数pn"}), 400

        result = read_file_by_page(page_number, PAGE_SIZE, BOOK_PATH)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def read_file_by_page(page_number: int, page_size: int, file_path: str) -> List[str]:
    result = []

    # 参数校验
    if page_number < 1 or page_size < 1:
        raise ValueError("页数和页大小必须大于0")

    if file_path is None or file_path.strip() == "":
        raise ValueError("文件路径不能为空")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 计算起始行和结束行
    start_line = (page_number - 1) * page_size
    end_line = start_line + page_size - 1
    current_line = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.rstrip('\n')  # 移除行尾换行符

                if not line.strip():

                    if MARK_LINE_BREAK and len(result) != 0:
                        result[len(result) - 1] = result[len(result) - 1] + "  n"
                    continue

                if start_line <= current_line <= end_line:
                    result.append(line)

                if current_line > end_line:
                    break

                current_line += 1

    except IOError as e:
        raise RuntimeError(f"读取文件时发生错误: {str(e)}") from e

    return result


def load_cfg():
    exe_path = ""
    if getattr(sys, 'frozen', False):
        exe_path = os.path.dirname(sys.executable)

    txt_file_path = os.path.join(exe_path, 'cfg.txt')

    try:
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):  # 跳过空行或注释
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)  # 只分割第一个 '='
                    CONFIG_MAP[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"文件不存在：{txt_file_path}")


def string_to_bool(s):
    s = s.lower()  # 将字符串转换为小写，以避免大小写问题
    return s in ("true", "1", "yes")


def init():
    load_cfg()

    global BOOK_PATH, PAGE_SIZE, MARK_LINE_BREAK
    BOOK_PATH = CONFIG_MAP.get("path")
    PAGE_SIZE = CONFIG_MAP.get("size")
    MARK_LINE_BREAK = CONFIG_MAP.get("mark")
    port = CONFIG_MAP.get("port")
    hide = CONFIG_MAP.get("hide")
    if BOOK_PATH is None or BOOK_PATH == "":
        print("请配置书籍绝对地址，在exe文件同级创建cfg.txt 添加一行内容为\n path=D:\\xxx\\xxx\\xx.txt ")
        return

    if PAGE_SIZE is None:
        PAGE_SIZE = 5
    else:
        PAGE_SIZE = int(PAGE_SIZE)

    if port is None:
        port = 8996
    else:
        port = int(port)

    if MARK_LINE_BREAK is None:
        MARK_LINE_BREAK = False
    else:
        MARK_LINE_BREAK = string_to_bool(MARK_LINE_BREAK)

    if hide is None:
        hide = False
    else:
        hide = string_to_bool(hide)

    if hide:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    app.run(port=port)


if __name__ == "__main__":
    if is_already_running():
        ctypes.windll.user32.MessageBoxW(0, "程序已经在运行中", "提示", 0x40 | 0x0)
        sys.exit(1)
    try:
        init()
    except Exception as e:
        print("程序出错：", e)
    input("按回车退出...")  # 等待用户输入
