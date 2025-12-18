"""剪切板自动同步去重（跨重启持久化）。

目标：
- 仅用于“剪切板自动识别/自动同步”链路（避免重复同步）。
- 支持设置去重窗口（默认 48 小时）。
- 去重缓存写入磁盘，重启后仍生效。
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional

from loguru import logger


_SPACE_RE = re.compile(r"[ \t]+")
_MANY_NEWLINES_RE = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    """对文本做温和归一化，尽量把“看起来一样”的内容变成同一指纹。"""
    if text is None:
        return ""
    t = str(text)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = t.strip()
    # 合并连续空格/制表
    t = _SPACE_RE.sub(" ", t)
    # 合并过多空行（避免拷贝来源带很多空白导致指纹不同）
    t = _MANY_NEWLINES_RE.sub("\n\n", t)
    return t


def fingerprint_text(text: str) -> str:
    n = normalize_text(text)
    return hashlib.sha1(n.encode("utf-8")).hexdigest()


@dataclass
class DedupeDecision:
    is_duplicate: bool
    fingerprint: str
    age_seconds: Optional[int] = None


class ClipboardDedupeStore:
    """剪切板去重存储（线程安全 + 磁盘持久化）。"""

    def __init__(self, path: Path, ttl_seconds: int = 48 * 3600, enabled: bool = True):
        self.path = Path(path)
        self.ttl_seconds = int(ttl_seconds)
        self.enabled = bool(enabled)
        self._lock = threading.RLock()
        self._items: Dict[str, float] = {}
        self._load()

    def _load(self) -> None:
        with self._lock:
            try:
                if not self.path.exists():
                    return
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f) or {}
                items = data.get("items", {})
                if not isinstance(items, dict):
                    return
                now = time.time()
                kept = 0
                for fp, ts in items.items():
                    try:
                        tsf = float(ts)
                    except Exception:
                        continue
                    if now - tsf <= self.ttl_seconds:
                        self._items[str(fp)] = tsf
                        kept += 1
                if kept and len(items) != kept:
                    # 清理旧数据后回写一次，避免文件长期膨胀
                    self._save_locked()
                logger.info(f"剪切板去重缓存已加载: {kept} 条, TTL={self.ttl_seconds}s")
            except Exception as e:
                logger.warning(f"加载剪切板去重缓存失败，将忽略去重文件: {e}")

    def _save_locked(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        data = {
            "version": 1,
            "ttl_seconds": self.ttl_seconds,
            "items": self._items,
        }
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        tmp.replace(self.path)

    def _prune_locked(self) -> int:
        now = time.time()
        to_delete = [fp for fp, ts in self._items.items() if now - ts > self.ttl_seconds]
        for fp in to_delete:
            self._items.pop(fp, None)
        return len(to_delete)

    def check(self, text: str) -> DedupeDecision:
        """检查是否为去重窗口内的重复内容。

        返回 fingerprint，供成功同步后 mark 使用（避免重复计算）。
        """
        fp = fingerprint_text(text)
        if not self.enabled:
            return DedupeDecision(is_duplicate=False, fingerprint=fp, age_seconds=None)

        with self._lock:
            ts = self._items.get(fp)
            if not ts:
                return DedupeDecision(is_duplicate=False, fingerprint=fp, age_seconds=None)
            age = int(time.time() - ts)
            if age > self.ttl_seconds:
                # 过期，视为非重复并顺便清掉
                self._items.pop(fp, None)
                return DedupeDecision(is_duplicate=False, fingerprint=fp, age_seconds=age)
            return DedupeDecision(is_duplicate=True, fingerprint=fp, age_seconds=age)

    def mark_fingerprint(self, fingerprint: str) -> None:
        """记录某 fingerprint 已经成功同步过。"""
        if not self.enabled:
            return
        with self._lock:
            self._items[str(fingerprint)] = time.time()
            pruned = self._prune_locked()
            try:
                self._save_locked()
            except Exception as e:
                logger.warning(f"保存剪切板去重缓存失败: {e}")
            if pruned:
                logger.debug(f"剪切板去重缓存已清理过期项: {pruned} 条")


