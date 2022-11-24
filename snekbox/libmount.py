from __future__ import annotations

import ctypes
import os
from ctypes.util import find_library
from enum import IntEnum
from pathlib import Path

__all__ = ("mount", "unmount", "Size", "UnmountFlags")

libc = ctypes.CDLL(find_library("c"), use_errno=True)
libc.mount.argtypes = (
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_ulong,
    ctypes.c_char_p,
)
libc.umount2.argtypes = (ctypes.c_char_p, ctypes.c_int)


class Size(int):
    """Size in bytes."""

    @classmethod
    def from_mb(cls, mb: int) -> Size:
        """Create a Size from mebibytes."""
        return cls(mb * 1024 * 1024)


class UnmountFlags(IntEnum):
    """Flags for umount2."""

    MNT_FORCE = 1
    MNT_DETACH = 2
    MNT_EXPIRE = 4
    UMOUNT_NOFOLLOW = 8


def mount(source: Path | str, target: Path | str, fs: str, **options: str | int) -> None:
    """
    Mount a filesystem.

    https://man7.org/linux/man-pages/man8/mount.8.html

    Args:
        source: Source directory or device.
        target: Target directory.
        fs: Filesystem type.
        **options: Mount options.
    """
    kwargs = " ".join(f"{key}={value}" for key, value in options.items())

    result: int = libc.mount(
        str(source).encode(), str(target).encode(), fs.encode(), 0, kwargs.encode()
    )
    if result < 0:
        errno = ctypes.get_errno()
        raise OSError(errno, f"Error mounting {target}: {os.strerror(errno)}")


def unmount(target: Path | str, flags: UnmountFlags | int = UnmountFlags.MNT_DETACH) -> None:
    """
    Unmount a filesystem.

    https://man7.org/linux/man-pages/man2/umount.2.html

    Args:
        target: Target directory.
        flags: Unmount flags.
    """
    result: int = libc.umount2(str(target).encode(), int(flags))
    if result < 0:
        errno = ctypes.get_errno()
        raise OSError(errno, f"Error unmounting {target}: {os.strerror(errno)}")
