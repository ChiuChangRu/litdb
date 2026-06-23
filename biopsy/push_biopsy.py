#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送 biopsy 知識庫兩個檔到 ChiuChangRu/litdb (branch: main)
  - biopsy/biopsy_patents.json
  - biopsy/index.html

用法（PAT 走環境變數，不寫進檔案、不進對話）:
    export GITHUB_PAT=ghp_xxxxxxxx        # 你的 fine-grained / classic PAT，需 repo contents write
    python3 push_biopsy.py

把本腳本與 biopsy_patents.json、index.html 放同一個資料夾即可。
流程：每個檔先 GET 拿最新 sha → 再 PUT（base64 內容 + sha），避免蓋掉背景變動。
"""
import os, sys, json, base64, urllib.request, urllib.error

OWNER  = "ChiuChangRu"
REPO   = "litdb"
BRANCH = "main"
FILES  = [
    ("biopsy_patents.json", "biopsy/biopsy_patents.json"),
    ("index.html",          "biopsy/index.html"),
]
COMMIT_MSG = "feat(biopsy): 新增 B44 US5511556（專利原圖＋元件符號渲染）+ 清除 B26 公司名 literal"

PAT = os.environ.get("GITHUB_PAT")
if not PAT:
    sys.exit("✗ 請先設定環境變數 GITHUB_PAT")

def api(method, path, body=None):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {PAT}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

def get_sha(path):
    code, body = api("GET", f"{path}?ref={BRANCH}")
    if code == 200:
        return body.get("sha")
    if code == 404:
        return None          # 檔不存在 → 新建
    sys.exit(f"✗ GET {path} 失敗 HTTP {code}: {body.get('message')}")

for local, remote in FILES:
    if not os.path.exists(local):
        sys.exit(f"✗ 找不到本地檔: {local}（請與本腳本放同一資料夾）")
    with open(local, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()
    sha = get_sha(remote)
    payload = {"message": COMMIT_MSG, "content": content_b64, "branch": BRANCH}
    if sha:
        payload["sha"] = sha
    code, body = api("PUT", remote, payload)
    if code in (200, 201):
        commit = body.get("commit", {}).get("sha", "")[:7]
        print(f"✓ {remote}  ({'更新' if sha else '新建'})  commit {commit}")
    else:
        sys.exit(f"✗ PUT {remote} 失敗 HTTP {code}: {body.get('message')}")

print("\n完成。GitHub Pages 數十秒後生效。驗收：文庫點開 B44 → 右側應出現『專利圖（原始圖紙）』區。")
