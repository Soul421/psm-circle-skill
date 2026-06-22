#!/usr/bin/env python3
"""
娜姐朋友圈 - 数据读取模块

双层数据架构：
- 本地数据（data/members.json）：脱敏花名册，无需Token，安装即可用
- 远程数据（GitHub私有仓库）：完整信息（含邮箱），需要Token

使用方式：
- 安装Skill后即可使用：查看成员列表、成员详情、需求匹配
- 配置PSM_GITHUB_TOKEN后解锁：查看成员邮箱、发起建联
"""

import json
import base64
import urllib.request
import urllib.error
import sys
import os

# GitHub配置（可选，用于读取邮箱等敏感信息）
GITHUB_TOKEN = os.getenv("PSM_GITHUB_TOKEN")
GITHUB_REPO = "Soul421/psm-circle"
GITHUB_API = "https://api.github.com"

# 本地数据路径（Skill自带，无需Token）
LOCAL_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "members.json")


def load_local_members():
    """从本地data/members.json加载脱敏花名册（无需Token）"""
    if not os.path.exists(LOCAL_DATA_PATH):
        print(f"本地数据文件不存在: {LOCAL_DATA_PATH}")
        return []
    
    try:
        with open(LOCAL_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("members", [])
    except Exception as e:
        print(f"读取本地数据失败: {e}")
        return []


def get_remote_file(path):
    """从GitHub私有仓库读取文件（需要Token）"""
    if not GITHUB_TOKEN:
        return None
    
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8")
            return None
    except Exception as e:
        return None


def get_member_emails():
    """从私有仓库获取成员邮箱（需要Token）"""
    if not GITHUB_TOKEN:
        return None
    
    content = get_remote_file("members.json")
    if not content:
        return None
    
    try:
        members = json.loads(content)
        return {m["id"]: m.get("email", "") for m in members}
    except:
        return None


def find_member(name_or_id):
    """根据姓名或ID查找成员"""
    members = load_local_members()
    for m in members:
        if m.get("id") == name_or_id or m.get("name") == name_or_id:
            return m
        # 模糊匹配
        if name_or_id in m.get("name", ""):
            return m
    return None


def match_needs(current_member_id):
    """匹配需求：找到与当前成员互补的其他成员"""
    members = load_local_members()
    current = None
    for m in members:
        if m.get("id") == current_member_id:
            current = m
            break
    
    if not current:
        return []
    
    current_has = set(current.get("has", []))
    current_needs = set(current.get("needs", []))
    
    matches = []
    for member in members:
        if member.get("id") == current_member_id:
            continue
        
        other_has = set(member.get("has", []))
        other_needs = set(member.get("needs", []))
        
        # 他有我需要的，或我有他需要的
        match_reasons = []
        if current_needs & other_has:
            match_reasons.append(f"他有你需要: {', '.join(current_needs & other_has)}")
        if current_has & other_needs:
            match_reasons.append(f"你有他需要: {', '.join(current_has & other_needs)}")
        
        if match_reasons:
            matches.append({
                "member": member,
                "reasons": match_reasons
            })
    
    return matches


def list_members():
    """列出所有成员（无需Token）"""
    members = load_local_members()
    if not members:
        print("暂无成员数据")
        return
    
    print(f"\n当前圈子共 {len(members)} 位成员：\n")
    for i, m in enumerate(members, 1):
        name = m.get("name", "未知")
        title = m.get("title", "")
        company = m.get("company", "")
        tags = m.get("tags", [])
        has = m.get("has", [])
        needs = m.get("needs", [])
        intro = m.get("intro", "")
        
        print(f"{i}. {name} | {title}")
        if company:
            print(f"   🏢 {company}")
        if tags:
            print(f"   🏷️  {'，'.join(tags)}")
        if has:
            print(f"   ✅ 拥有: {', '.join(has[:2])}{'...' if len(has) > 2 else ''}")
        if needs:
            print(f"   🎯 在找: {', '.join(needs)}")
        if intro:
            print(f"   📝 {intro[:50]}{'...' if len(intro) > 50 else ''}")
        print()
    
    if not GITHUB_TOKEN:
        print("💡 提示: 配置 PSM_GITHUB_TOKEN 后可查看成员邮箱并发起建联")


def show_detail(name_or_id):
    """显示成员详情（无需Token）"""
    member = find_member(name_or_id)
    if not member:
        print(f"未找到成员: {name_or_id}")
        return
    
    print(f"\n{'='*50}")
    print(f"成员详情: {member.get('name')}")
    print(f"{'='*50}\n")
    
    print(f"🏢 {member.get('company', '')} | {member.get('title', '')}")
    print(f"🏭 行业: {member.get('industry', '')}")
    
    tags = member.get("tags", [])
    if tags:
        print(f"🏷️ 标签: {', '.join(tags)}")
    
    print(f"\n📝 简介:")
    print(f"   {member.get('intro', '')}")
    
    has = member.get("has", [])
    if has:
        print(f"\n✅ 我有什么:")
        for item in has:
            print(f"   • {item}")
    
    needs = member.get("needs", [])
    if needs:
        print(f"\n🎯 我需要什么:")
        for item in needs:
            print(f"   • {item}")
    
    # 尝试获取邮箱（需要Token）
    if GITHUB_TOKEN:
        emails = get_member_emails()
        if emails and member.get("id") in emails:
            email = emails[member["id"]]
            if email:
                print(f"\n📧 联系方式: {email}")
    else:
        print(f"\n💡 配置 PSM_GITHUB_TOKEN 后可查看联系方式并发起建联")


def show_match(current_member_id):
    """显示需求匹配结果（无需Token）"""
    member = find_member(current_member_id)
    if not member:
        print(f"未找到成员: {current_member_id}")
        return
    
    matches = match_needs(member.get("id"))
    
    if not matches:
        print("暂时没有找到匹配的成员")
        return
    
    print(f"\n💡 需求匹配分析\n")
    print(f"当前成员: {member.get('name')} | {member.get('title', '')}")
    
    has = member.get("has", [])
    needs = member.get("needs", [])
    if has:
        print(f"你的资源: {', '.join(has)}")
    if needs:
        print(f"你在找: {', '.join(needs)}")
    
    print(f"\n找到 {len(matches)} 位可能互补的成员：\n")
    
    for i, match in enumerate(matches, 1):
        m = match["member"]
        print(f"{i}. {m.get('name')} | {m.get('title', '')} | {m.get('company', '')}")
        for reason in match["reasons"]:
            print(f"   → {reason}")
        print()
    
    if GITHUB_TOKEN:
        print("💡 需要建联？告诉我你想联系谁")
    else:
        print("💡 配置 PSM_GITHUB_TOKEN 后可发起建联")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 github_reader.py list          - 列出所有成员")
        print("  python3 github_reader.py detail <姓名>  - 查看成员详情")
        print("  python3 github_reader.py match <ID>    - 匹配需求")
        print()
        print("💡 安装即可用，无需配置Token")
        print("💡 配置 PSM_GITHUB_TOKEN 后解锁邮箱和建联功能")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "list":
        list_members()
    elif command == "detail" and len(sys.argv) >= 3:
        show_detail(sys.argv[2])
    elif command == "match" and len(sys.argv) >= 3:
        show_match(sys.argv[2])
    else:
        print(f"未知命令: {command}")
        sys.exit(1)
