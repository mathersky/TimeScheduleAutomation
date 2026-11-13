# -*- coding: utf-8 -*-
"""TimeScheduleAutomation GitHub Release publisher. Token is memory-only."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import queue
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import webbrowser
import zipfile

REPOSITORY = "mathersky/TimeScheduleAutomation"
API_ROOT = "https://api.github.com"


class PublisherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("TimeScheduleAutomation｜GitHub發布主控台")
        root.geometry("900x760")
        root.minsize(780, 660)
        self.repo_var = tk.StringVar(value=REPOSITORY)
        self.token_var = tk.StringVar()
        self.tag_var = tk.StringVar(value="v3.4.32")
        self.title_var = tk.StringVar(value="TimeScheduleAutomation v3.4.32")
        self.zip_var = tk.StringVar()
        self.show_token_var = tk.BooleanVar(value=False)
        self.events: queue.Queue[tuple[str, str]] = queue.Queue()
        self.publish_button: ttk.Button | None = None
        self._build()
        self.root.after(100, self._poll)

    def _build(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="GitHub 發布主控台", font=("Microsoft JhengHei UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="建立 GitHub Release、上傳 ZIP 與 SHA-256，並同步更新程式自動更新清單。",
        ).pack(anchor="w", pady=(3, 12))

        form = ttk.Frame(outer)
        form.pack(fill="x")
        ttk.Label(form, text="Repository").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.repo_var).grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        ttk.Label(form, text="GitHub Token").grid(row=1, column=0, sticky="w", pady=5)
        self.token_entry = ttk.Entry(form, textvariable=self.token_var, show="*")
        self.token_entry.grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Checkbutton(
            form, text="顯示", variable=self.show_token_var,
            command=lambda: self.token_entry.configure(show="" if self.show_token_var.get() else "*"),
        ).grid(row=1, column=2, sticky="w", padx=(8, 0), pady=5)
        ttk.Label(
            form,
            text="Fine-grained Token：只授權此 Repository，Contents 設為 Read and write。Token 不會寫入檔案。",
            foreground="#52657A",
        ).grid(row=2, column=1, columnspan=2, sticky="w", pady=(0, 5))
        ttk.Button(form, text="開啟 Token 設定頁", command=lambda: webbrowser.open_new_tab(
            "https://github.com/settings/personal-access-tokens/new"
        )).grid(row=2, column=0, sticky="w", pady=(0, 5))

        ttk.Label(form, text="版本標籤").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.tag_var, width=24).grid(row=3, column=1, sticky="w", pady=5)
        ttk.Label(form, text="Release 標題").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.title_var).grid(row=4, column=1, columnspan=2, sticky="ew", pady=5)
        ttk.Label(form, text="安裝 ZIP").grid(row=5, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.zip_var).grid(row=5, column=1, sticky="ew", pady=5)
        ttk.Button(form, text="選擇檔案…", command=self._choose_zip).grid(row=5, column=2, padx=(8, 0), pady=5)
        form.columnconfigure(1, weight=1)

        ttk.Label(outer, text="更新說明").pack(anchor="w", pady=(10, 4))
        self.notes = tk.Text(outer, height=7, wrap="word", undo=True)
        self.notes.pack(fill="x")
        self.notes.insert("1.0", "- 更新 TimeScheduleAutomation 軟體內容\n- 請確認 ZIP 與 SHA-256 檔案後再發布。")

        row = ttk.Frame(outer)
        row.pack(fill="x", pady=10)
        self.publish_button = ttk.Button(row, text="檢查並發布 Release", command=self._publish)
        self.publish_button.pack(side="left")
        ttk.Button(row, text="開啟 Repository", command=self._open_repo).pack(side="left", padx=8)
        ttk.Label(row, text="需有此 Repository 的寫入權限。Token 僅在本次執行期間使用。", foreground="#52657A").pack(side="left", padx=8)

        ttk.Label(outer, text="發布紀錄").pack(anchor="w", pady=(4, 4))
        self.log = tk.Text(outer, height=13, wrap="word", state="disabled", bg="#F7F9FC")
        self.log.pack(fill="both", expand=True)
        self._write("準備就緒。請貼上 Fine-grained Token；本主控台不會儲存或記錄 Token。")

    def _choose_zip(self):
        path = filedialog.askopenfilename(
            title="選擇 TimeScheduleAutomation 安裝 ZIP",
            filetypes=(("ZIP 檔案", "*.zip"), ("所有檔案", "*.*")),
        )
        if path:
            self.zip_var.set(path)
            m = re.search(r"v?(\d+\.\d+\.\d+)", Path(path).stem)
            if m:
                version = "v" + m.group(1)
                self.tag_var.set(version)
                self.title_var.set(f"TimeScheduleAutomation {version}")

    def _open_repo(self):
        repo = self.repo_var.get().strip() or REPOSITORY
        webbrowser.open_new_tab("https://github.com/" + repo)

    def _write(self, line: str):
        self.log.configure(state="normal")
        self.log.insert("end", line.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "log":
                    self._write(value)
                elif kind in ("done", "error"):
                    self._write(value)
                    self.token_var.set("")
                    if self.publish_button:
                        self.publish_button.configure(state="normal")
                    if kind == "done":
                        messagebox.showinfo("發布完成", value)
                    else:
                        messagebox.showerror("發布失敗", value)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    @staticmethod
    def _api(token: str, method: str, path: str, body=None, *, binary=None, content_type=None, allow_404=False):
        url = path if path.startswith("https://") else API_ROOT + path
        data = binary if binary is not None else (
            json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        )
        headers = {
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "TimeScheduleAutomation-Publisher/1.1",
        }
        if data is not None:
            headers["Content-Type"] = content_type or "application/json; charset=utf-8"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=90) as response:
                raw = response.read()
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if allow_404 and exc.code == 404:
                return None
            if exc.code == 401:
                raise RuntimeError("Token 無效或已過期。請重新建立 Token 後再試。") from None
            if exc.code == 403:
                raise RuntimeError("GitHub 拒絕此操作。請確認 Token 有此 Repository 的 Contents: Read and write 權限。") from None
            if exc.code == 422:
                raise RuntimeError("GitHub 拒絕發布：版本標籤可能已存在，請使用新的版本標籤。") from None
            try:
                message = json.loads(detail).get("message", detail)
            except Exception:
                message = detail
            raise RuntimeError(f"GitHub API HTTP {exc.code}：{message}") from None
        except URLError as exc:
            raise RuntimeError(f"連線 GitHub 失敗：{exc.reason}") from None

    def _publish(self):
        repo = self.repo_var.get().strip()
        token = self.token_var.get().strip()
        tag = self.tag_var.get().strip()
        title = self.title_var.get().strip()
        zip_path = Path(self.zip_var.get().strip().strip('"'))
        notes = self.notes.get("1.0", "end-1c").strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            messagebox.showerror("Repository 格式", "請輸入 owner/repository，例如 mathersky/TimeScheduleAutomation。")
            return
        if not token:
            messagebox.showerror("缺少 Token", "請在 GitHub Token 欄貼上 Fine-grained Token。")
            self.token_entry.focus_set()
            return
        if not re.fullmatch(r"v\d+\.\d+\.\d+(?:[-A-Za-z0-9_.]+)?", tag):
            messagebox.showerror("版本標籤格式", "請使用 v主版號.次版號.修補版號，例如 v3.4.33。")
            return
        if not zip_path.is_file():
            messagebox.showerror("找不到 ZIP", "請先選擇有效的安裝 ZIP。")
            return
        if zip_path.stat().st_size > 100 * 1024 * 1024:
            messagebox.showerror("ZIP 過大", "ZIP 不可超過 100 MB，否則用戶端更新器無法下載。")
            return
        if not title or not notes:
            messagebox.showerror("資料不足", "請填寫 Release 標題與更新說明。")
            return
        try:
            with zipfile.ZipFile(zip_path) as archive:
                bad = archive.testzip()
                roots = {name.replace("\\", "/").split("/")[0] for name in archive.namelist() if name}
                expected = f"TimeScheduleAutomation_{tag[1:]}_Python版"
                if bad:
                    raise RuntimeError(f"ZIP 完整性檢查失敗：{bad}")
                if roots != {expected}:
                    raise RuntimeError(f"ZIP 根目錄需為『{expected}』，目前為：{', '.join(sorted(roots))}")
        except Exception as exc:
            messagebox.showerror("ZIP 檢查失敗", str(exc))
            return
        if not messagebox.askyesno(
            "確認發布",
            f"即將發布到 {repo}\n\n標籤：{tag}\nZIP：{zip_path.name}\n\n將建立 Release、上傳 ZIP 與 SHA-256，並更新自動更新清單。是否繼續？",
        ):
            return
        if self.publish_button:
            self.publish_button.configure(state="disabled")
        self.events.put(("log", f"開始發布 {tag}。Token 不會寫入發布紀錄。"))
        threading.Thread(
            target=self._publish_worker,
            args=(repo, token, tag, title, zip_path, notes),
            daemon=True,
        ).start()

    def _publish_worker(self, repo: str, token: str, tag: str, title: str, zip_path: Path, notes: str):
        release_url = ""
        try:
            self.events.put(("log", "確認 Token 可存取 Repository…"))
            self._api(token, "GET", "/repos/" + repo)
            digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
            sha_path = zip_path.parent / f"{zip_path.stem}_SHA256SUMS.txt"
            sha_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
            self.events.put(("log", f"ZIP 已通過結構檢查。SHA-256：{digest}"))

            release = self._api(token, "POST", "/repos/" + repo + "/releases", {
                "tag_name": tag,
                "name": title,
                "body": notes,
                "draft": False,
                "prerelease": False,
            })
            release_url = release.get("html_url", "")
            upload_root = release.get("upload_url", "").split("{", 1)[0]
            if not upload_root.startswith("https://uploads.github.com/"):
                raise RuntimeError("GitHub 未回傳有效的 Release 上傳網址。" + ("\nRelease：" + release_url if release_url else ""))
            self.events.put(("log", "Release 已建立。開始上傳 ZIP 與 SHA-256…"))

            for asset_path, mime_type in ((zip_path, "application/zip"), (sha_path, "text/plain; charset=utf-8")):
                upload_url = upload_root + "?name=" + quote(asset_path.name, safe="")
                self._api(
                    token, "POST", upload_url, binary=asset_path.read_bytes(),
                    content_type=mime_type,
                )
                self.events.put(("log", f"已上傳：{asset_path.name}"))

            version = tag[1:] if tag.lower().startswith("v") else tag
            manifest = {
                "product": "TimeScheduleAutomation",
                "channel": "stable",
                "version": version,
                "asset": zip_path.name,
                "sha256": digest,
                "download_url": f"https://github.com/{repo}/releases/download/{quote(tag, safe='')}/{quote(zip_path.name, safe='')}",
            }
            path = "/repos/" + repo + "/contents/updates/manifest.json"
            existing = self._api(token, "GET", path, allow_404=True)
            content_b64 = base64.b64encode(json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")).decode("ascii")
            payload = {"message": f"Publish {tag} update manifest", "content": content_b64}
            if existing and existing.get("sha"):
                payload["sha"] = existing["sha"]
            self._api(token, "PUT", path, payload)
            self.events.put(("done", f"發布完成。\nRelease：{release_url}\n\n更新清單已同步。"))
        except Exception as exc:
            detail = str(exc)
            if release_url:
                detail = "Release 已建立：" + release_url + "\n後續上傳或更新清單發生錯誤：\n" + detail
            self.events.put(("error", detail))


def main():
    root = tk.Tk()
    PublisherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
