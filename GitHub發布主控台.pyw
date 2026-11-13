# -*- coding: utf-8 -*-
"""TimeScheduleAutomation GitHub release publisher (requires GitHub CLI)."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from urllib.parse import quote
import zipfile

REPOSITORY = "mathersky/TimeScheduleAutomation"


class PublisherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("TimeScheduleAutomation｜GitHub發布主控台")
        root.geometry("860x700")
        root.minsize(760, 600)
        self.repo_var = tk.StringVar(value=REPOSITORY)
        self.tag_var = tk.StringVar(value="v3.4.32")
        self.title_var = tk.StringVar(value="TimeScheduleAutomation v3.4.32")
        self.zip_var = tk.StringVar()
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
            text="建立 GitHub Release、上傳 ZIP 與 SHA-256，並同步更新程式的自動更新清單。",
        ).pack(anchor="w", pady=(3, 14))

        form = ttk.Frame(outer)
        form.pack(fill="x")
        ttk.Label(form, text="Repository").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.repo_var).grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        ttk.Label(form, text="版本標籤").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.tag_var, width=24).grid(row=1, column=1, sticky="w", pady=5)
        ttk.Label(form, text="Release 標題").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.title_var).grid(row=2, column=1, columnspan=2, sticky="ew", pady=5)
        ttk.Label(form, text="安裝 ZIP").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.zip_var).grid(row=3, column=1, sticky="ew", pady=5)
        ttk.Button(form, text="選擇檔案…", command=self._choose_zip).grid(row=3, column=2, padx=(8, 0), pady=5)
        form.columnconfigure(1, weight=1)

        ttk.Label(outer, text="更新說明").pack(anchor="w", pady=(12, 4))
        self.notes = tk.Text(outer, height=7, wrap="word", undo=True)
        self.notes.pack(fill="x")
        self.notes.insert("1.0", "- 更新 TimeScheduleAutomation 軟體內容\n- 請確認 ZIP 與 SHA-256 檔案後再發布。")

        row = ttk.Frame(outer)
        row.pack(fill="x", pady=10)
        self.publish_button = ttk.Button(row, text="檢查並發布 Release", command=self._publish)
        self.publish_button.pack(side="left")
        ttk.Button(row, text="開啟 Repository", command=self._open_repo).pack(side="left", padx=8)
        ttk.Label(row, text="需要 GitHub CLI，並先完成 gh auth login。", foreground="#52657A").pack(side="left", padx=8)

        ttk.Label(outer, text="發布紀錄").pack(anchor="w", pady=(4, 4))
        self.log = tk.Text(outer, height=14, wrap="word", state="disabled", bg="#F7F9FC")
        self.log.pack(fill="both", expand=True)
        self._write("準備就緒。帳號驗證沿用 GitHub CLI，不會將 Token 儲存在本程式。")

    def _choose_zip(self):
        path = filedialog.askopenfilename(
            title="選擇 TimeScheduleAutomation 安裝 ZIP",
            filetypes=(("ZIP 檔案", "*.zip"), ("所有檔案", "*.*")),
        )
        if path:
            self.zip_var.set(path)
            stem = Path(path).stem
            m = re.search(r"v?(\d+\.\d+\.\d+)", stem)
            if m:
                version = "v" + m.group(1)
                self.tag_var.set(version)
                self.title_var.set(f"TimeScheduleAutomation {version}")

    def _open_repo(self):
        import webbrowser
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
                self._write(value)
                if kind == "done":
                    if self.publish_button:
                        self.publish_button.configure(state="normal")
                    messagebox.showinfo("發布完成", value)
                elif kind == "error":
                    if self.publish_button:
                        self.publish_button.configure(state="normal")
                    messagebox.showerror("發布失敗", value)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    @staticmethod
    def _run(command: list[str], *, check=True) -> subprocess.CompletedProcess:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if check and result.returncode != 0:
            detail = (result.stderr or result.stdout or "命令執行失敗").strip()
            raise RuntimeError(detail)
        return result

    def _publish(self):
        gh = shutil.which("gh")
        if not gh:
            messagebox.showerror(
                "找不到 GitHub CLI",
                "請先安裝 GitHub CLI（gh），再開啟命令提示字元執行 gh auth login。\n\n安裝完成後重新啟動本主控台。",
            )
            return
        repo = self.repo_var.get().strip()
        tag = self.tag_var.get().strip()
        title = self.title_var.get().strip()
        zip_path = Path(self.zip_var.get().strip().strip('"'))
        notes = self.notes.get("1.0", "end-1c").strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            messagebox.showerror("Repository 格式", "請輸入 owner/repository，例如 mathersky/TimeScheduleAutomation。")
            return
        if not re.fullmatch(r"v\d+\.\d+\.\d+(?:[-A-Za-z0-9_.]+)?", tag):
            messagebox.showerror("版本標籤格式", "版本標籤請使用 v主版號.次版號.修補版號，例如 v3.4.32。")
            return
        if not zip_path.is_file():
            messagebox.showerror("找不到 ZIP", "請先選擇有效的安裝 ZIP。")
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
            f"即將發布到 {repo}\n\n標籤：{tag}\nZIP：{zip_path.name}\n\n發布後會更新自動更新清單。是否繼續？",
        ):
            return
        if self.publish_button:
            self.publish_button.configure(state="disabled")
        self.events.put(("log", f"開始檢查 GitHub 登入與 ZIP：{zip_path.name}"))
        threading.Thread(
            target=self._publish_worker,
            args=(gh, repo, tag, title, zip_path, notes),
            daemon=True,
        ).start()

    def _publish_worker(self, gh: str, repo: str, tag: str, title: str, zip_path: Path, notes: str):
        try:
            status = self._run([gh, "auth", "status", "--hostname", "github.com"], check=False)
            if status.returncode != 0:
                raise RuntimeError("GitHub CLI 尚未登入。請開啟命令提示字元執行 gh auth login，完成後再發布。")
            self.events.put(("log", "GitHub CLI 登入有效。"))
            view = self._run([gh, "repo", "view", repo, "--json", "nameWithOwner"], check=False)
            if view.returncode != 0:
                raise RuntimeError("無法存取 Repository，請確認帳號具有寫入權限：" + (view.stderr or view.stdout).strip())

            digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
            sha_path = zip_path.parent / f"{zip_path.stem}_SHA256SUMS.txt"
            sha_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
            self.events.put(("log", f"SHA-256：{digest}"))

            self._run([
                gh, "release", "create", tag, str(zip_path), str(sha_path),
                "--repo", repo, "--title", title, "--notes", notes,
            ])
            self.events.put(("log", "Release 已建立，ZIP 與 SHA-256 已上傳。"))

            version = tag[1:] if tag.lower().startswith("v") else tag
            download_url = f"https://github.com/{repo}/releases/download/{tag}/{quote(zip_path.name, safe='')}"
            manifest = {
                "product": "TimeScheduleAutomation",
                "channel": "stable",
                "version": version,
                "asset": zip_path.name,
                "sha256": digest,
                "download_url": download_url,
            }
            manifest_b64 = base64.b64encode(
                json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
            ).decode("ascii")
            endpoint = f"repos/{repo}/contents/updates/manifest.json"
            current = self._run([gh, "api", endpoint, "--jq", ".sha"], check=False)
            if current.returncode == 0:
                content_args = ["-f", "sha=" + current.stdout.strip()]
            elif "404" in (current.stderr or "") or "Not Found" in (current.stderr or ""):
                content_args = []
            else:
                raise RuntimeError("Release 已發布，但讀取既有更新清單失敗：" + (current.stderr or current.stdout).strip())
            self._run([
                gh, "api", endpoint, "-X", "PUT",
                "-f", f"message=Publish {tag} update manifest",
                "-f", f"content={manifest_b64}",
                *content_args,
            ])
            release = self._run([gh, "release", "view", tag, "--repo", repo, "--json", "url", "--jq", ".url"])
            self.events.put(("done", "發布成功：" + release.stdout.strip() + "\n更新清單已同步。"))
        except Exception as exc:
            self.events.put(("error", str(exc)))


def main():
    root = tk.Tk()
    PublisherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
