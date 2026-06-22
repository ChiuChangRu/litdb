#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在你自己電腦上跑這支腳本，PAT 只存在於你的終端機環境變數裡，
不會寫進任何檔案、不會出現在跟 Claude 的對話裡。

用法：
    1. 把這支腳本和要上傳的檔案放在同一個資料夾
    2. 終端機執行：

       macOS / Linux:
         GITHUB_PAT=ghp_xxxxx python3 push_to_github.py biopsy_patents.json biopsy/biopsy_patents.json
         GITHUB_PAT=ghp_xxxxx python3 push_to_github.py index.html biopsy/index.html

       Windows (PowerShell):
         $env:GITHUB_PAT="ghp_xxxxx"; python push_to_github.py biopsy_patents.json biopsy/biopsy_patents.json

    參數說明：
       第1個參數 = 你電腦上的本機檔案路徑
       第2個參數 = repo 裡的目標路徑

PAT 權限需求：對 ChiuChangRu/litdb 有 Contents: write
（classic token 勾 repo 即可；fine-grained 則對該 repo 給 Contents: Read and write）
"""
import json, base64, os, sys, urllib.request, urllib.error

REPO   = "ChiuChangRu/litdb"
BRANCH = "main"

def main():
    if len(sys.argv) != 3:
        sys.exit("用法: python3 push_to_github.py <本機檔案路徑> <repo內路徑>\n"
                  "例如: python3 push_to_github.py biopsy_patents.json biopsy/biopsy_patents.json")

    local_path, gh_path = sys.argv[1], sys.argv[2]

    pat = os.environ.get("GITHUB_PAT")
    if not pat:
        sys.exit("✗ 找不到環境變數 GITHUB_PAT。\n"
                  "  請用： GITHUB_PAT=你的token python3 push_to_github.py ...")
    if not os.path.exists(local_path):
        sys.exit(f"✗ 找不到本機檔案：{local_path}")

    api = f"https://api.github.com/repos/{REPO}/contents/{gh_path}"
    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "litdb-pusher",
    }

    def call(url, method="GET", body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode() or "{}")

    # 步驟1：抓目前 sha（檔案不存在則回 None，視為新建）
    st, info = call(f"{api}?ref={BRANCH}")
    sha = info.get("sha") if st == 200 else None
    print(f"  目標：{REPO}/{gh_path}")
    print(f"  目前 sha: {sha[:12] + '…' if sha else '（檔案不存在，將新建）'}")

    # 若是 JSON 檔，先做基本合法性檢查，避免上傳壞檔
    if local_path.endswith(".json"):
        try:
            with open(local_path, encoding="utf-8") as f:
                d = json.load(f)
            print(f"  本機檔案驗證：合法 JSON（{len(d.get('papers', []))} 筆 papers，若有此欄位）")
        except Exception as e:
            sys.exit(f"✗ 本機檔案不是合法 JSON，停止上傳：{e}")

    # 步驟2：PUT 推送
    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()

    payload = {
        "message": f"update {os.path.basename(gh_path)} via push_to_github.py",
        "content": content_b64,
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha

    st, resp = call(api, method="PUT", body=payload)
    print(f"  PUT 狀態碼: {st}")

    if st in (200, 201):
        print(f"✓ 成功！new sha: {resp['content']['sha'][:12]}…")
        print(f"  commit: {resp['commit']['html_url']}")
    else:
        print(f"✗ 失敗：{json.dumps(resp, ensure_ascii=False)[:600]}")
        if st == 409:
            print("  （409 = 遠端檔案在你抓 sha 之後又被改了，重跑一次即可抓最新 sha）")
        if st == 401:
            print("  （401 = PAT 無效或已過期，請確認 token 正確且未過期）")
        if st == 403:
            print("  （403 = PAT 沒有此 repo 的寫入權限，請確認 token 權限範圍）")
        sys.exit(1)

if __name__ == "__main__":
    main()
