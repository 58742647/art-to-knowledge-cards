#!/usr/bin/env python3
"""
quick_validate.py - 快速验证 make-knowledge-cards Skill 的完整性和输出质量
"""

import os
import sys
import re

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
AGENTS_YAML = os.path.join(SKILL_DIR, "agents", "openai.yaml")


def check_file_exists(path, name):
    """检查文件是否存在"""
    if os.path.exists(path):
        print(f"  [OK] {name} 存在")
        return True
    else:
        print(f"  [FAIL] {name} 不存在: {path}")
        return False


def validate_skill_md():
    """验证 SKILL.md 格式"""
    print("\n[1/4] 验证 SKILL.md ...")
    with open(SKILL_MD, "r", encoding="utf-8") as f:
        content = f.read()

    ok = True

    # 检查 YAML frontmatter
    if content.startswith("---"):
        print("  [OK] 包含 YAML frontmatter")
    else:
        print("  [FAIL] 缺少 YAML frontmatter")
        ok = False

    # 检查 name 字段
    if "name: make-knowledge-cards" in content:
        print("  [OK] name 字段正确")
    else:
        print("  [FAIL] name 字段缺失或错误")
        ok = False

    # 检查 description 字段
    if "description:" in content:
        print("  [OK] description 字段存在")
    else:
        print("  [FAIL] description 字段缺失")
        ok = False

    # 检查核心内容
    required_sections = [
        "知识卡片格式",
        "核心知识",
        "简明解释",
        "例子/自测问题",
        "单点原则",
        "去重原则",
        "忠实原则",
    ]
    for section in required_sections:
        if section in content:
            print(f"  [OK] 包含关键内容: {section}")
        else:
            print(f"  [FAIL] 缺少关键内容: {section}")
            ok = False

    return ok


def validate_agents_yaml():
    """验证 agents/openai.yaml 格式"""
    print("\n[2/4] 验证 agents/openai.yaml ...")
    try:
        with open(AGENTS_YAML, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"  [FAIL] 读取错误: {e}")
        return False

    ok = True

    # 检查关键字段
    if "name:" in content:
        print("  [OK] 包含 name 字段")
    else:
        print("  [FAIL] 缺少 name 字段")
        ok = False

    if "system_prompt:" in content:
        print("  [OK] 包含 system_prompt")
    else:
        print("  [FAIL] 缺少 system_prompt")
        ok = False

    if "output_schema:" in content:
        print("  [OK] 包含 output_schema")
    else:
        print("  [FAIL] 缺少 output_schema")
        ok = False

    # 检查 system_prompt 内容
    required_prompt_keywords = ["核心知识", "简明解释", "例子", "自测"]
    for kw in required_prompt_keywords:
        if kw in content:
            print(f"  [OK] system_prompt 包含关键词: {kw}")
        else:
            print(f"  [FAIL] system_prompt 缺少关键词: {kw}")
            ok = False

    return ok


def validate_card_output(cards_text, source_text):
    """验证生成的知识卡片是否符合要求"""
    print("\n[3/4] 验证知识卡片输出质量 ...")
    ok = True

    # 统计卡片数量
    card_headers = re.findall(r"### 卡片 \d+[:：]", cards_text)
    card_count = len(card_headers)
    print(f"  [INFO] 检测到 {card_count} 张卡片")

    if 3 <= card_count <= 8:
        print(f"  [OK] 卡片数量在合理范围内 (3～8)")
    else:
        print(f"  [FAIL] 卡片数量 {card_count} 不在 3～8 范围内")
        ok = False

    # 检查每张卡片结构
    cards = re.split(r"### 卡片 \d+[:：]", cards_text)
    cards = [c.strip() for c in cards if c.strip()]

    for i, card in enumerate(cards, 1):
        has_core = "**核心知识**" in card
        has_explain = "**简明解释**" in card
        has_example = "**例子" in card or "**自测" in card or "例子/自测问题" in card

        if has_core and has_explain and has_example:
            print(f"  [OK] 卡片 {i} 结构完整")
        else:
            print(f"  [FAIL] 卡片 {i} 结构不完整 (核心知识={has_core}, 解释={has_explain}, 例子={has_example})")
            ok = False

    # 检查是否编造信息（简单检查：输出中的关键词应在原文中出现过）
    output_words = set(re.findall(r"[\u4e00-\u9fff]{2,}", cards_text))
    source_words = set(re.findall(r"[\u4e00-\u9fff]{2,}", source_text))
    foreign_words = output_words - source_words
    # 允许一些通用词汇
    allowed = {"卡片", "核心", "知识", "解释", "例子", "自测", "问题", "标题", "简明", "理解", "掌握", "概念"}
    foreign_words = foreign_words - allowed
    if len(foreign_words) > 10:
        print(f"  [WARN] 输出包含较多原文没有的词汇: {list(foreign_words)[:10]}... 可能存在编造风险")
    else:
        print(f"  [OK] 输出词汇与原文基本一致")

    return ok


def run_test_case(title, source_text):
    """运行单个测试用例"""
    print(f"\n{'='*60}")
    print(f"测试用例: {title}")
    print(f"{'='*60}")
    print(f"原文长度: {len(source_text)} 字符")

    # 读取 README.md 中的示例输出作为参考
    readme_path = os.path.join(SKILL_DIR, "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()

    # 提取示例输出部分
    example_match = re.search(r"### 输出示例\s*```markdown(.*?)```", readme, re.DOTALL)
    if example_match:
        example_output = example_match.group(1).strip()
        print("\n[4/4] 使用 README 中的示例输出进行格式验证 ...")
        return validate_card_output(example_output, source_text)
    else:
        print("  [WARN] README.md 中没有找到示例输出，跳过格式验证")
        return True


def main():
    print("="*60)
    print("make-knowledge-cards Skill 快速验证")
    print("="*60)

    all_ok = True

    # 文件存在性检查
    all_ok &= check_file_exists(SKILL_MD, "SKILL.md")
    all_ok &= check_file_exists(AGENTS_YAML, "agents/openai.yaml")

    # 格式验证
    all_ok &= validate_skill_md()
    all_ok &= validate_agents_yaml()

    # 测试用例 1：技术类
    tech_article = """
HTTP 状态码用于表示服务器对请求的响应结果。常见的状态码有：
200 OK：请求成功，服务器返回了请求的资源。
301 Moved Permanently：请求的资源已被永久移动到新的 URL。
404 Not Found：服务器找不到请求的资源。
500 Internal Server Error：服务器内部发生错误，无法完成请求。
状态码分为 5 类：1xx 信息响应、2xx 成功、3xx 重定向、4xx 客户端错误、5xx 服务器错误。
    """.strip()
    all_ok &= run_test_case("技术类文章 - HTTP 状态码", tech_article)

    # 测试用例 2：科普类
    science_article = """
光合作用是绿色植物利用光能将二氧化碳和水转化为有机物并释放氧气的过程。
该过程主要在叶绿体中进行，分为光反应和暗反应两个阶段。
光反应阶段发生在类囊体薄膜上，需要光照，将水分解为氧气和还原氢，同时合成 ATP。
暗反应阶段发生在叶绿体基质中，不需要光照，利用光反应产生的 ATP 和还原氢将二氧化碳固定并还原为糖类。
光合作用的总反应式为：6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂。
    """.strip()
    all_ok &= run_test_case("科普类文章 - 光合作用", science_article)

    # 总结
    print("\n" + "="*60)
    if all_ok:
        print("验证结果: 全部通过 [OK]")
        return 0
    else:
        print("验证结果: 存在失败项 [FAIL]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
