"""UNO 会话看门狗：超时强制杀死 soffice 进程组。

LibreOffice 处理个别 docx 时可能无限空转 CPU（loadComponentFromURL /
storeToURL 等 UNO 调用卡死），且这些调用是同步阻塞的，无法从同一线程
中断。本模块提供一个独立 daemon 线程计时：会话开始时启动，到达 deadline
后通过回调杀掉 soffice 进程组，使被阻塞的 UNO 调用因 socket 对端死亡而
抛出异常并解除阻塞。

本模块刻意不 import uno，便于脱离 LibreOffice 环境进行单元测试。
"""
from __future__ import annotations

import logging
import os
import signal
import threading
import time
from collections.abc import Callable

log = logging.getLogger(__name__)


class SessionWatchdog:
    """会话级总超时看门狗。

    用法::

        wd = SessionWatchdog(kill_callback, timeout_seconds=240)
        wd.start()
        try:
            ...  # 同步 UNO 调用，可能卡死
        finally:
            wd.stop()  # 正常结束时取消计时，避免误杀

    超时后调用 ``kill_callback``（通常是杀进程组）。``kill_callback`` 必须
    幂等：正常关闭路径也会调用同一函数杀进程组作为兜底。
    """

    def __init__(
        self,
        kill_callback: Callable[[], None],
        timeout_seconds: float,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds 必须为正数")
        self._kill_callback = kill_callback
        self._timeout = timeout_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._fired = False

    def start(self) -> None:
        """启动看门狗线程。"""
        if self._thread is not None:
            return
        deadline = time.monotonic() + self._timeout
        self._stop_event.clear()
        self._fired = False
        self._thread = threading.Thread(
            target=self._run,
            args=(deadline,),
            name="uno-session-watchdog",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """取消计时并等待看门狗线程退出。

        若看门狗已触发，本方法不阻塞已执行的 kill。线程退出后才返回，
        避免与正常关闭路径竞争杀进程组。
        """
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def fired(self) -> bool:
        """看门狗是否已触发超时 kill。"""
        return self._fired

    def _run(self, deadline: float) -> None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            self._trigger()
            return
        if self._stop_event.wait(remaining):
            return
        if time.monotonic() >= deadline:
            self._trigger()

    def _trigger(self) -> None:
        if self._fired:
            return
        self._fired = True
        log.error(
            "UNO 会话超时（%ss），强制杀死 soffice 进程组", self._timeout
        )
        try:
            self._kill_callback()
        except Exception:  # noqa: BLE001 — 看门狗绝不能抛出
            log.exception("看门狗 kill_callback 执行失败")


def kill_process_group(pid: int) -> None:
    """杀掉指定 PID 所属进程组（SIGTERM 兜底 SIGKILL）。

    配合 ``subprocess.Popen(start_new_session=True)`` 使用，确保 soffice
    及其子进程（soffice.bin / oosplash）被一并清理，避免孤儿进程泄漏。
    """
    try:
        pgid = os.getpgid(pid)
    except ProcessLookupError:
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            return
        except PermissionError:
            log.error("无权限杀进程组 %s", pgid)
            return
        # SIGTERM 后给进程一点时间退出；SIGKILL 后无需等待
        if sig == signal.SIGTERM:
            _wait_for_exit(pid, timeout=3)
            try:
                os.getpgid(pid)
            except ProcessLookupError:
                return


def _wait_for_exit(pid: int, timeout: float) -> None:
    """轮询等待进程组 leader 退出（最多 timeout 秒）。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.getpgid(pid)
        except ProcessLookupError:
            return
        time.sleep(0.1)
