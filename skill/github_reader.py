#!/usr/bin/env python3
"""
娜姐朋友圈 - 数据读取模块
从GitHub私有仓库读取成员数据

Token通过环境变量注入，不内置在代码中
"""

import json
import base64
import urllib.request
import urllib.error
import sys
import os

# GitHub配置
GITHUB_TOKEN = os.getenv("PSM_GITHUB_TOKEN")
GITHUB_REPO = "Soul421/psm-circle"
GITHUB_API = "https://api.github.com"

if not GITHUB_TOKEN:
    print("错误：未配置GitHub Token，请通过Skill凭证系统配置")
    sys.exit(1)


def get_file_content(path):
    """从GitHub仓库读取文件内容"""
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{path}"
    
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
            return None
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("认证失败：GitHub Token无效或已过期")
        elif e.code == 403:
            print("权限不足：无权访问私有仓库")
        else:
            print(f"读取文件失败 {path}: HTTP {e.code}")
        return None
    except Exception as e:
        print(f"读取文件失败 {path}: {e}")
        return None


def get_members():
    """获取所有成员信息"""
    content = get_file_content("members.json")
    if not content:
        return []
    
    try:
        members = json.loads(content)
        return members
    except json.JSONDecodeError:
        return []


def get_member_detail(member_id):
    """获取单个成员的详细信息"""
    contact = get_file_content(f"contacts/{member_id}.md")
    resource = get_file_content(f"resources/{member_id}.md")
    
    return {
        "id": member_id,
        "contact": contact,
        "resources": resource
    }


def get_all_resources():
    """获取所有成员的资源信息"""
    members = get_members()
    resources = {}
    
    for member in members:
        member_id = member.get("id")
        if member_id:
            resource_content = get_file_content(f"resources/{member_id}.md")
            if resource_content:
                resources[member_id] = {
                    "name": member.get("name"),
                    "content": resource_content
                }
    
    return resources


def find_member_by_name(name):
    """根据姓名查找成员"""
    members = get_members()
    for member in members:
        if member.get("name") == name or member.get("name", "").startswith(name):
            return member
    return None


def match_needs(current_member_id):
    """匹配需求：找到与当前成员互补的其他成员"""
    members = get_members()
    current_resource = get_file_content(f"resources/{current_member_id}.md")
    
    if not current_resource:
        return []
    
    matches = []
    
    for member in members:
        other_id = member.get("id")
        if other_id == current_member_id:
            continue
        
        other_resource = get_file_content(f"resources/{other_id}.md")
        if not other_resource:
            continue
        
        matches.append({
            "member": member,
            "resource": other_resource,
            "match_reason": "资源互补"
        })
    
    return matches


def list_members():
    """列出所有成员"""
    members = get_members()
    if not members:
        print("暂无成员数据")
        return
    
    print(f"\n当前圈子共 {len(members)} 位成员：\n")
    for i, m in enumerate(members, 1):
        name = m.get("name", "未知")
        position = m.get("position", "")
        tags = m.get("tags", [])
        intent = m.get("intent", "")
        email = m.get("email", "")
        
        print(f"{i}. {name} | {position}")
        if tags:
            print(f"   能力标签：{', '.join(tags)}")
        if intent:
            print(f"   → 在找：{intent}")
        if email:
            print(f"   📧 {email}")
        print()


def show_detail(member_id):
    """显示成员详情"""
    detail = get_member_detail(member_id)
    
    if not detail.get("contact") and not detail.get("resources"):
        print(f"未找到成员 {member_id} 的详细信息")
        return
    
    print(f"\n{'='*50}")
    print(f"成员详情: {member_id}")
    print(f"{'='*50}\n")
    
    if detail.get("contact"):
        print("【公开简介】")
        print(detail["contact"])
        print()
    
    if detail.get("resources"):
        print("【供需资源】")
        print(detail["resources"])


def show_match(member_id):
    """显示需求匹配结果"""
    matches = match_needs(member_id)
    
    if not matches:
        print("暂时没有找到匹配的成员")
        return
    
    print(f"\n💡 需求匹配分析\n")
    print(f"找到 {len(matches)} 位可能互补的成员：\n")
    
    for i, match in enumerate(matches, 1):
        member = match["member"]
        print(f"{i}. {member.get('name')} | {member.get('position')}")
        print(f"   匹配原因：{match['match_reason']}")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 github_reader.py list          - 列出所有成员")
        print("  python3 github_reader.py detail <id>   - 查看成员详情")
        print("  python3 github_reader.py match <id>    - 匹配需求")
        sys.exit(1)
    
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
