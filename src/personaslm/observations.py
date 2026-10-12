"""Windows memory observations; unavailable fields are never inferred from config."""
import ctypes
from ctypes import wintypes
import os

from .journal import utc_now


def memory_observation(pid):
    report = {"observed_utc": utc_now(), "pid": pid, "platform": os.name}
    if os.name != "nt":
        return {**report, "status": "unavailable", "reason": "Windows observation only"}
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("length", wintypes.DWORD), ("load_percent", wintypes.DWORD)] + [
            (n, ctypes.c_ulonglong) for n in ("total_physical", "available_physical", "total_pagefile",
                                             "available_pagefile", "total_virtual", "available_virtual", "available_extended")]
    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("page_faults", wintypes.DWORD)] + [
            (n, ctypes.c_size_t) for n in ("peak_working_set", "working_set", "quota_peak_paged_pool",
                "quota_paged_pool", "quota_peak_nonpaged_pool", "quota_nonpaged_pool", "pagefile_usage", "peak_pagefile_usage")]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
    state = MEMORYSTATUSEX()
    state.length = ctypes.sizeof(state)
    if kernel.GlobalMemoryStatusEx(ctypes.byref(state)):
        report["system"] = {n: getattr(state, n) for n, _ in state._fields_ if n != "length"}
    else:
        report["system_error"] = ctypes.get_last_error()
    handle = kernel.OpenProcess(0x0400 | 0x0010, False, pid)
    if handle:
        try:
            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(counters)
            if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                report["process"] = {n: getattr(counters, n) for n, _ in counters._fields_ if n != "cb"}
            else:
                report["process_error"] = ctypes.get_last_error()
        finally:
            kernel.CloseHandle(handle)
    else:
        report["process_error"] = ctypes.get_last_error()
    report["status"] = "observed" if "system" in report and "process" in report else "partial"
    return report
