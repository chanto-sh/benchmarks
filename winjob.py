"""Measuring a process and everything it starts, on Windows.

Windows has no wait4, so the agent runs in a job object instead. The job's
accounting adds up the CPU of every process that was ever in it, exited ones
included, as wait4 does on Unix for the children an agent reaped. The agent is
created suspended and resumed only once it's in the job, so nothing it starts
can slip out first. Peak memory comes from sampling the working set (Windows'
resident set) of each process in the job, as cputurn.py samples `ps` on Unix.
"""
import ctypes
import subprocess
from ctypes import wintypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
ntdll = ctypes.WinDLL("ntdll")

CREATE_SUSPENDED = 0x00000004
JOB_ACCOUNTING = 1  # JobObjectBasicAccountingInformation
JOB_PROCESS_IDS = 3  # JobObjectBasicProcessIdList
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010


class Accounting(ctypes.Structure):
    _fields_ = [("TotalUserTime", ctypes.c_int64), ("TotalKernelTime", ctypes.c_int64),
                ("ThisPeriodTotalUserTime", ctypes.c_int64), ("ThisPeriodTotalKernelTime", ctypes.c_int64),
                ("TotalPageFaultCount", wintypes.DWORD), ("TotalProcesses", wintypes.DWORD),
                ("ActiveProcesses", wintypes.DWORD), ("TotalTerminatedProcesses", wintypes.DWORD)]


class MemoryCounters(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


class ProcessIds(ctypes.Structure):
    _fields_ = [("NumberOfAssignedProcesses", wintypes.DWORD), ("NumberOfProcessIdsInList", wintypes.DWORD),
                ("ProcessIdList", ctypes.c_size_t * 1024)]


kernel32.CreateJobObjectW.restype = wintypes.HANDLE
kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
kernel32.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                               wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(ctypes.c_int64)] * 4
kernel32.K32GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(MemoryCounters), wintypes.DWORD]
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]


def check(ok, what):
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error(), what)


class Job:
    def __init__(self):
        self.handle = kernel32.CreateJobObjectW(None, None)
        check(self.handle, "CreateJobObject")

    def start(self, cmd, **popen):
        """Popen(cmd) inside the job."""
        flags = popen.pop("creationflags", 0) | CREATE_SUSPENDED
        p = subprocess.Popen(cmd, creationflags=flags, **popen)
        try:
            check(kernel32.AssignProcessToJobObject(self.handle, int(p._handle)), "AssignProcessToJobObject")
        except OSError:
            p.kill()
            raise
        ntdll.NtResumeProcess(int(p._handle))
        return p

    def cpu_seconds(self):
        """User and kernel CPU of every process ever in the job."""
        info = Accounting()
        check(kernel32.QueryInformationJobObject(self.handle, JOB_ACCOUNTING, ctypes.byref(info),
                                                 ctypes.sizeof(info), None), "QueryInformationJobObject")
        return (info.TotalUserTime + info.TotalKernelTime) / 1e7  # 100 ns units

    def pids(self):
        """The processes in the job now."""
        ids = ProcessIds()
        if not kernel32.QueryInformationJobObject(self.handle, JOB_PROCESS_IDS, ctypes.byref(ids),
                                                  ctypes.sizeof(ids), None):
            return []
        return list(ids.ProcessIdList[:ids.NumberOfProcessIdsInList])

    def sample(self, seen):
        """Record each live process's cumulative CPU seconds in `seen` (keeping
        the max, as cputurn.sample_tree_cpu does) and return their total working
        set in KB."""
        total = 0
        for pid in self.pids():
            h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, False, pid)
            if not h:
                continue
            try:
                times = [ctypes.c_int64() for _ in range(4)]
                if kernel32.GetProcessTimes(h, *[ctypes.byref(t) for t in times]):
                    cpu = (times[2].value + times[3].value) / 1e7
                    seen[pid] = max(seen.get(pid, 0.0), cpu)
                mem = MemoryCounters()
                mem.cb = ctypes.sizeof(mem)
                if kernel32.K32GetProcessMemoryInfo(h, ctypes.byref(mem), mem.cb):
                    total += mem.WorkingSetSize // 1024
            finally:
                kernel32.CloseHandle(h)
        return total

    def wait(self, p, timeout):
        """Wait for `p` (killing the whole job after `timeout` seconds, and
        still measuring it), then return the job's CPU seconds."""
        try:
            p.wait(timeout)
        except subprocess.TimeoutExpired:
            kernel32.TerminateJobObject(self.handle, 1)
            p.wait()
        return self.cpu_seconds()

    def close(self):
        # Ends whatever the agent left running, as a Unix run's process group would.
        kernel32.TerminateJobObject(self.handle, 0)
        kernel32.CloseHandle(self.handle)
