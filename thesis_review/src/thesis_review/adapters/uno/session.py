"""管理 headless soffice 进程与 UNO 连接：单实例串行。

启动 headless soffice，通过本地 socket 连接 UNO bridge，
提供"打开文档 → 拿到 UNO 文档组件 → 用完关闭"的上下文管理器。

soffice 路径通过 SOFFICE_BIN 环境变量覆盖，默认探测常见路径。

会话级超时：LibreOffice 处理个别 docx 时可能无限空转 CPU（UNO 同步
调用卡死）。通过 ``SessionWatchdog`` 在独立 daemon 线程计时，超时则
杀掉整个 soffice 进程组，使被阻塞的 UNO 调用抛异常解除阻塞，避免
worker 线程与 soffice 进程泄漏。超时由 ``UNO_SESSION_TIMEOUT_SECONDS``
环境变量配置，默认 240s（需小于 backend 的 300s 超时）。
"""
from __future__ import annotations

import contextlib
import logging
import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue

from thesis_review.adapters.uno.watchdog import SessionWatchdog, kill_process_group

log = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 240.0

_DEFAULT_SOFFICE = [
    "/usr/bin/soffice",                                       # Linux / Docker
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",  # macOS
    "soffice",                                                # PATH
]


def _find_soffice() -> str:
    """按 SOFFICE_BIN 环境变量或默认路径探测 soffice 可执行文件。"""
    env = os.environ.get("SOFFICE_BIN")
    if env:
        return env
    for cand in _DEFAULT_SOFFICE:
        if cand == "soffice" or Path(cand).exists():
            return cand
    raise RuntimeError("找不到 soffice，可设 SOFFICE_BIN 环境变量指定路径")


def path_to_url(path: str) -> str:
    """将本地文件路径转换为 UNO 的 file URL。"""
    return uno.systemPathToFileUrl(str(Path(path).resolve()))


def _resolve_timeout_seconds() -> float:
    """从 UNO_SESSION_TIMEOUT_SECONDS 环境变量读取会话超时，默认 240s。"""
    raw = os.environ.get("UNO_SESSION_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return _DEFAULT_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        log.warning("UNO_SESSION_TIMEOUT_SECONDS=%r 非法，回退默认 %ss", raw, _DEFAULT_TIMEOUT_SECONDS)
        return _DEFAULT_TIMEOUT_SECONDS
    if value <= 0:
        log.warning("UNO_SESSION_TIMEOUT_SECONDS=%r 非正，回退默认 %ss", raw, _DEFAULT_TIMEOUT_SECONDS)
        return _DEFAULT_TIMEOUT_SECONDS
    return value


def _find_free_port() -> int:
    """获取本机临时空闲端口，降低并行测试/运行的端口冲突概率。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class UnoSession:
    """单实例串行 UNO 会话。

    用法：:

        with UnoSession() as session:
            with session.open("input.docx") as doc:
                # doc 是 com.sun.star.text.XTextDocument
                ...
    """

    def __init__(self, port: int | None = None, timeout_seconds: float | None = None) -> None:
        self._proc: subprocess.Popen | None = None
        self._desktop = None
        self._port = port if port is not None else _find_free_port()
        self._profile_dir: tempfile.TemporaryDirectory | None = None
        self._timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else _resolve_timeout_seconds()
        )
        self._watchdog: SessionWatchdog | None = None
        self._current_path: str | None = None

    # ── context manager ──────────────────────────────────────────────

    def __enter__(self) -> "UnoSession":
        self._start()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ── lifecycle ────────────────────────────────────────────────────

    def _start(self) -> None:
        soffice = _find_soffice()
        accept = f"--accept=socket,host=127.0.0.1,port={self._port};urp;"
        self._profile_dir = tempfile.TemporaryDirectory(prefix="thesis-review-lo-")
        user_installation = f"-env:UserInstallation={path_to_url(self._profile_dir.name)}"
        log.info("启动 soffice: %s", soffice)
        try:
            self._proc = subprocess.Popen(
                [
                    soffice,
                    "--headless",
                    "--norestore",
                    "--invisible",
                    "--nodefault",
                    "--nologo",
                    user_installation,
                    accept,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            # 等 soffice 就绪（最多 30 秒）
            last_err: Exception | None = None
            for _i in range(60):
                try:
                    self._connect()
                    break
                except Exception as e:
                    last_err = e
                    time.sleep(0.5)
            else:
                raise RuntimeError(f"无法连接 soffice UNO bridge：{last_err}")
        except Exception:
            self.close()
            raise
        # 连接成功后启动看门狗：超时杀进程组，防止 UNO 调用卡死泄漏
        self._watchdog = SessionWatchdog(self._kill_process_group, self._timeout_seconds)
        self._watchdog.start()

    def _connect(self) -> None:
        ctx_local = uno.getComponentContext()
        resolver = ctx_local.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", ctx_local
        )
        connect_url = (
            f"uno:socket,host=127.0.0.1,port={self._port};urp;"
            "StarOffice.ComponentContext"
        )
        ctx = resolver.resolve(connect_url)
        smgr = ctx.ServiceManager
        self._desktop = smgr.createInstanceWithContext(
            "com.sun.star.frame.Desktop", ctx
        )

    def is_ready(self) -> bool:
        """健康检查：UNO 连接是否可用。"""
        return self._desktop is not None

    @contextlib.contextmanager
    def open(self, path: str):
        """打开一个 .docx 文档，返回 UNO 文档组件。

        作为上下文管理器使用，退出时自动关闭文档。
        """
        self._current_path = path
        props = (PropertyValue(Name="Hidden", Value=True),)
        url = path_to_url(path)
        doc = self._desktop.loadComponentFromURL(url, "_blank", 0, props)
        try:
            yield doc
        finally:
            with contextlib.suppress(Exception):
                doc.close(False)
            self._current_path = None

    def close(self) -> None:
        """关闭 UNO 连接并终止 soffice 进程组。

        先停看门狗避免与正常关闭竞争；再尝试 UNO 优雅退出；最后兜底杀
        整个进程组（含 soffice.bin 子进程），防止孤儿进程泄漏。
        """
        if self._watchdog is not None:
            self._watchdog.stop()
            self._watchdog = None
        if self._desktop is not None:
            with contextlib.suppress(Exception):
                self._desktop.terminate()
            self._desktop = None
        if self._proc is not None:
            self._kill_process_group()
            self._proc = None
        if self._profile_dir is not None:
            self._profile_dir.cleanup()
            self._profile_dir = None

    def _kill_process_group(self) -> None:
        """杀掉 soffice 所在进程组（oosplash + soffice.bin 等）并回收子进程。

        先 SIGTERM/SIGKILL 整组，再 ``proc.wait()`` 回收 oosplash 直接子进程，
        避免僵尸进程残留。即使进程已被看门狗杀死，wait 仍会回收僵尸。
        """
        proc = self._proc
        if proc is None:
            return
        if proc.poll() is None:
            log.info(
                "终止 soffice 进程组 pid=%s doc=%s",
                proc.pid,
                self._current_path or "?",
            )
            kill_process_group(proc.pid)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            log.warning("soffice 进程组 pid=%s 回收超时", proc.pid)
