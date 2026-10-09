"""Native file locking for local development on Unix and Windows.

Unix keeps flock semantics and descriptor inheritance for MLX. Windows uses
LockFileEx shared/exclusive byte-range locks. Training and POSIX
descriptor inheritance are deliberately unsupported on Windows.
"""
import errno
import os
import time

try:
    import fcntl as _unix
except ImportError:
    _unix = None
    import msvcrt as _windows

WINDOWS = _unix is None
LOCK_SH, LOCK_EX, LOCK_NB, LOCK_UN = 1, 2, 4, 8


def _windows_lock_region(fd: int, operation: int) -> None:
    import ctypes
    from ctypes import wintypes
    class Overlapped(ctypes.Structure):
        _fields_ = [("Internal", ctypes.c_size_t), ("InternalHigh", ctypes.c_size_t),
                    ("Offset", wintypes.DWORD), ("OffsetHigh", wintypes.DWORD),
                    ("hEvent", wintypes.HANDLE)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LockFileEx.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(Overlapped)]
    kernel.LockFileEx.restype = wintypes.BOOL
    kernel.UnlockFileEx.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                                    wintypes.DWORD, ctypes.POINTER(Overlapped)]
    kernel.UnlockFileEx.restype = wintypes.BOOL
    handle = wintypes.HANDLE(_windows.get_osfhandle(fd))
    overlap = Overlapped()
    if operation == LOCK_UN:
        ok = kernel.UnlockFileEx(handle, 0, 1, 0, ctypes.byref(overlap))
    else:
        # Always ask non-blockingly; the caller owns retry/timeout policy.
        flags = 1 | (2 if operation & LOCK_EX else 0)
        ok = kernel.LockFileEx(handle, flags, 0, 1, 0, ctypes.byref(overlap))
    if not ok:
        error = ctypes.get_last_error()
        if error == 33:  # ERROR_LOCK_VIOLATION
            raise BlockingIOError(errno.EAGAIN, "File is locked")
        raise ctypes.WinError(error)


def flock(fd: int, operation: int) -> None:
    if not WINDOWS:
        _unix.flock(fd, operation)
        return
    # Match flock's file-object contract before calling the Windows CRT API.
    descriptor = fd if isinstance(fd, int) else fd.fileno()
    while True:
        try:
            _windows_lock_region(descriptor, operation)
            return
        except BlockingIOError:
            if operation == LOCK_UN or operation & LOCK_NB:
                raise
            time.sleep(0.05)


def windows_pid_alive(pid: int) -> bool:
    """Query a Windows process without os.kill (which can terminate on Windows)."""
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
    if not handle:
        return ctypes.get_last_error() == 5  # Access denied: assume still alive.
    try:
        code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            return True  # Fail closed if liveness cannot be established.
        return code.value == 259  # STILL_ACTIVE
    finally:
        kernel.CloseHandle(handle)
