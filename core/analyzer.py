# ======================================================================
# 功能模块：脚本分析器 (Script Analyzer)
# ======================================================================
# V3.4: 增强 argparse 识别，智能分析 Python 脚本
# ======================================================================

import re
import os
import hashlib

def analyze_script(file_path: str) -> dict:
    """
    分析 Python 脚本，返回其特性和推荐模式

    :param file_path: str, 脚本文件路径
    :return: dict, 包含以下键：
        - has_args: bool, 是否需要命令行参数
        - is_interactive: bool, 是否为交互式脚本
        - recommended_mode: str, 推荐模式 ('gooey', 'lite_console', 'pyw')
        - confidence: float, 推荐置信度 0.0-1.0
        - detected_features: list, 检测到的特性列表
    """
    result = {
        'has_args': False,
        'is_interactive': False,
        'recommended_mode': 'pyw',
        'confidence': 0.5,
        'detected_features': []
    }

    if not os.path.exists(file_path):
        result['detected_features'].append('file_not_found')
        return result

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(2000)
    except Exception:
        result['detected_features'].append('read_error')
        return result

    content_lower = content.lower()

    # V3.4: 增强 argparse 检测
    if 'import argparse' in content_lower or 'argparse.ArgumentParser' in content:
        result['has_args'] = True
        result['detected_features'].append('argparse')

    # 检测 GooeyParser
    if 'gooeyparser' in content_lower or 'gooeyparser' in content:
        result['has_args'] = True
        result['detected_features'].append('gooeyparser')

    # 检测 Click
    if 'click' in content_lower and ('@click' in content or 'click.command' in content):
        result['has_args'] = True
        result['detected_features'].append('click')

    # 检测 sys.argv 直接使用
    if 'sys.argv' in content:
        result['has_args'] = True
        result['detected_features'].append('sys.argv')

    # 检测 input() 函数（交互式输入）
    if re.search(r'\binput\s*\(', content):
        result['is_interactive'] = True
        result['detected_features'].append('input_function')

    # 检测 sys.stdin.read（管道交互）
    if 'sys.stdin.read' in content:
        result['is_interactive'] = True
        result['detected_features'].append('stdin_read')

    # 综合推荐模式
    if result['is_interactive'] and not result['has_args']:
        result['recommended_mode'] = 'lite_console'
        result['confidence'] = 0.9
    elif result['has_args'] and not result['is_interactive']:
        result['recommended_mode'] = 'gooey'
        result['confidence'] = 0.85
    elif result['has_args'] and result['is_interactive']:
        result['recommended_mode'] = 'lite_console'
        result['confidence'] = 0.7
    else:
        result['recommended_mode'] = 'pyw'
        result['confidence'] = 0.5

    return result


def extract_arg_names(file_path: str) -> list:
    """
    从脚本中提取参数名称列表（用于 Lite-Terminal 默认参数）

    :param file_path: str, 脚本文件路径
    :return: list, 参数名称列表
    """
    arg_names = []

    if not os.path.exists(file_path):
        return arg_names

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return arg_names

    patterns = [
        r'add_argument\([\'"](--[\w-]+)[\'"]',
        r'add_argument\([\'"](-[\w])[\'"]',
        r'@click\.option\([\'"](--[\w-]+)',
        r'@click\.argument\([\'"]([\w-]+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content)
        arg_names.extend(matches)

    return list(set(arg_names))


def get_script_hash(file_path: str) -> str:
    """
    计算脚本文件的 MD5 哈希值（仅读取前 1MB，优化大文件性能）

    :param file_path: str, 文件路径
    :return: str, 32位十六进制哈希值，失败返回空字符串
    """
    if not os.path.exists(file_path):
        return ""

    try:
        with open(file_path, 'rb') as f:
            content = f.read(1024 * 1024)
            return hashlib.md5(content).hexdigest()
    except Exception:
        return ""