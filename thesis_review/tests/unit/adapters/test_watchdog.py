"""SessionWatchdog 与 kill_process_group 单元测试（不依赖 UNO/LibreOffice）。

覆盖看门狗超时触发、取消、幂等，以及进程组杀函数的信号序列与异常兜底。
"""
from __future__ import annotations

import signal
import threading
import time

import pytest

from thesis_review.adapters.uno.watchdog import SessionWatchdog, kill_process_group


def _wait_until_fired(wd: SessionWatchdog, timeout: float = 2.0) -> None:
    """轮询等待看门狗触发（避免 stop() 抢先取消极短超时的看门狗）。"""
    deadline = time.monotonic() + timeout
    while not wd.fired() and time.monotonic() < deadline:
        time.sleep(0.005)


# ── SessionWatchdog ────────────────────────────────────────────────────


def test_watchdog_fires_after_timeout():
    """超时后应调用 kill_callback。"""
    called = threading.Event()

    wd = SessionWatchdog(lambda: called.set(), timeout_seconds=0.1)
    wd.start()
    try:
        assert called.wait(timeout=2), "看门狗应在超时后触发回调"
    finally:
        wd.stop()

    assert wd.fired()


def test_watchdog_stop_cancels_before_timeout():
    """stop() 在超时前调用，则回调不应被触发。"""
    called = threading.Event()

    wd = SessionWatchdog(lambda: called.set(), timeout_seconds=1.0)
    wd.start()
    time.sleep(0.05)
    wd.stop()

    # 等待超过原定超时时间，确认未触发
    time.sleep(0.2)
    assert not called.is_set()
    assert not wd.fired()


def test_watchdog_does_not_fire_early():
    """超时前回调不应被调用。"""
    called = threading.Event()

    wd = SessionWatchdog(lambda: called.set(), timeout_seconds=0.3)
    wd.start()
    try:
        time.sleep(0.1)
        assert not called.is_set()
        assert not wd.fired()
    finally:
        wd.stop()


def test_watchdog_invalid_timeout_raises():
    """非正超时值应拒绝。"""
    with pytest.raises(ValueError):
        SessionWatchdog(lambda: None, timeout_seconds=0)
    with pytest.raises(ValueError):
        SessionWatchdog(lambda: None, timeout_seconds=-1)


def test_watchdog_callback_exception_does_not_propagate():
    """kill_callback 抛异常时看门狗线程不应崩溃（仅记日志）。"""
    def boom() -> None:
        raise RuntimeError("boom")

    wd = SessionWatchdog(boom, timeout_seconds=0.05)
    wd.start()
    _wait_until_fired(wd)
    wd.stop()
    # 线程应已正常退出（join 成功），而非崩溃
    assert wd.fired()


def test_watchdog_fire_is_idempotent():
    """多次 start 不应创建多个线程；触发仅一次。"""
    call_count = 0
    lock = threading.Lock()

    def cb() -> None:
        nonlocal call_count
        with lock:
            call_count += 1

    wd = SessionWatchdog(cb, timeout_seconds=0.05)
    wd.start()
    wd.start()  # 重复 start 应被忽略
    _wait_until_fired(wd)
    wd.stop()
    assert call_count == 1


# ── kill_process_group ─────────────────────────────────────────────────


def test_kill_process_group_sends_sigterm_then_sigkill(monkeypatch):
    """进程仍存活时，先 SIGTERM 再 SIGKILL。"""
    # 模拟进程始终存活（getpgid 不抛 ProcessLookupError）
    monkeypatch.setattr("os.getpgid", lambda pid: pid)
    monkeypatch.setattr("time.sleep", lambda _s: None)

    sent: list[tuple[int, int]] = []
    monkeypatch.setattr(
        "os.killpg", lambda pgid, sig: sent.append((pgid, sig))
    )

    kill_process_group(4242)

    assert sent == [(4242, signal.SIGTERM), (4242, signal.SIGKILL)]


def test_kill_process_group_exits_after_sigterm(monkeypatch):
    """SIGTERM 后进程退出，则不再发 SIGKILL。"""
    alive = {"yes": True}

    def fake_getpgid(pid):  # noqa: ANN001
        if alive["yes"]:
            return pid
        raise ProcessLookupError

    sent: list[int] = []
    def fake_killpg(pgid, sig):  # noqa: ANN001
        sent.append(sig)
        # SIGTERM 发出后进程退出
        if sig == signal.SIGTERM:
            alive["yes"] = False

    monkeypatch.setattr("os.getpgid", fake_getpgid)
    monkeypatch.setattr("os.killpg", fake_killpg)
    monkeypatch.setattr("time.sleep", lambda _s: None)

    kill_process_group(9999)

    assert sent == [signal.SIGTERM]


def test_kill_process_group_no_process(monkeypatch):
    """进程已不存在（getpgid 抛 ProcessLookupError），应直接返回。"""
    monkeypatch.setattr("os.getpgid", lambda pid: (_ for _ in ()).throw(ProcessLookupError))
    monkeypatch.setattr("os.killpg", lambda pgid, sig: pytest.fail("不应调用 killpg"))

    kill_process_group(1234)  # 不应抛异常


def test_kill_process_group_permission_logs(monkeypatch, caplog):
    """无权限杀进程组时记 ERROR 但不抛异常。"""
    monkeypatch.setattr("os.getpgid", lambda pid: pid)
    monkeypatch.setattr("time.sleep", lambda _s: None)

    def fake_killpg(pgid, sig):  # noqa: ANN001
        if sig == signal.SIGTERM:
            raise PermissionError("denied")
        pytest.fail("SIGTERM 已失败，不应再发 SIGKILL")

    monkeypatch.setattr("os.killpg", fake_killpg)

    with caplog.at_level("ERROR"):
        kill_process_group(5555)
    assert any("无权限" in r.message for r in caplog.records)
