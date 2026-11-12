"""Read-only Windows owner-private HELD root candidate for ORIGINAL #168/#174.

Never creates directories, writes files, decrypts data, modifies ACLs,
or enables capture. A successful observation is COOPERATIVE and NONATOMIC:
it is not proof of safe handle-relative writes, trusted independent Fable,
crash-safe durability, denial of other principals, or human authorization.
No entry point in the active capture/inspector path calls this candidate.
"""

from __future__ import annotations

import hashlib
import os
import re
import uuid

from ._windows_held_privacy import _trusted_current_token_sid

_MAX_PATH = 1024
_SYSTEM_SID = "S-1-5-18"
_FULL_ACCESS = 0x001F01FF
_GENERIC_ALL = 0x10000000


class HeldWindowsRootError(RuntimeError):
    """Redacted provisional Windows private-root refusal."""


def _local_drive_components(path: str) -> tuple[str, ...]:
    """Syntactically restrict paths before any operating-system API access.

    Reject UNC/device/extended paths, ADS, traversal, DOS device aliases,
    trailing dot/space and noncanonical separators. This is NOT an OS
    normalization or filesystem-confinement proof.
    """
    if (type(path) is not str or not 3 <= len(path) <= _MAX_PATH
            or re.fullmatch(r"[A-Za-z]:\\(?:[^\\]+(?:\\[^\\]+)*)?", path) is None):
        raise HeldWindowsRootError("Windows root path refused")
    names = path[3:].split("\\") if len(path) > 3 else []
    if len(names) > 28:
        raise HeldWindowsRootError("Windows root path refused")
    reserved = {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(10)),
        *(f"LPT{i}" for i in range(10)),
        # Windows also reserves ISO-8859-1 superscript COM/LPT digits.
        *(f"{prefix}{digit}" for prefix in ("COM", "LPT")
          for digit in "¹²³"),
    }
    for name in names:
        if (not name or len(name) > 120 or name in {".", ".."}
                or name[-1] in {".", " "}
                or any(ord(c) < 32 or ord(c) == 127 or c in '/:*?"<>|'
                       for c in name)
                or name.split(".", 1)[0].upper() in reserved):
            raise HeldWindowsRootError("Windows root path refused")
    return (path[:2].upper(), *names)


def _trusted_local_appdata() -> str:
    """Request LOCALAPPDATA from the Windows shell rather than environment."""
    if os.name != "nt":
        raise HeldWindowsRootError("Windows trusted folder unavailable")
    try:
        import ctypes
        from ctypes import wintypes

        class Guid(ctypes.Structure):
            _fields_ = [
                ("data1", wintypes.DWORD), ("data2", wintypes.WORD),
                ("data3", wintypes.WORD), ("data4", ctypes.c_ubyte * 8),
            ]

        local_appdata = Guid.from_buffer_copy(
            uuid.UUID("F1B32785-6FBA-4FCF-9D55-7B8E7F157091").bytes_le)
        shell = ctypes.WinDLL("shell32", use_last_error=True)
        ole = ctypes.WinDLL("ole32", use_last_error=True)
        shell.SHGetKnownFolderPath.argtypes = [
            ctypes.POINTER(Guid), wintypes.DWORD, wintypes.HANDLE,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        shell.SHGetKnownFolderPath.restype = ctypes.c_long
        ole.CoTaskMemFree.argtypes = [ctypes.c_void_p]
        ole.CoTaskMemFree.restype = None
        returned = ctypes.c_void_p()
        code = shell.SHGetKnownFolderPath(
            ctypes.byref(local_appdata), 0, None, ctypes.byref(returned))
        try:
            if code != 0 or not returned.value:
                raise HeldWindowsRootError("Windows trusted folder refused")
            folder = ctypes.wstring_at(returned.value)
        finally:
            if returned.value:
                ole.CoTaskMemFree(returned)
        _local_drive_components(folder)
        return folder
    except (OSError, ValueError, OverflowError, AttributeError, TypeError):
        raise HeldWindowsRootError("Windows trusted folder refused") from None


def _windows_handle_chain(
    path: str, current_user_sid: str, *, inspect_private_dacl: bool,
) -> tuple[tuple[object, ...], ...]:
    """Inspect one path component at a time, refusing reparse/hardlink aliases.

    Each CreateFileW opens its current component separately, not relative to
    an already pinned parent. The resulting evidence is NEVER atomic. File
    identity and descriptor checks must be independently reproven on Windows.
    """
    if os.name != "nt":
        raise HeldWindowsRootError("Windows handle inspection unavailable")
    parts = _local_drive_components(path)
    try:
        import ctypes
        from ctypes import wintypes

        class FileInfo(ctypes.Structure):
            _fields_ = [
                ("attributes", wintypes.DWORD),
                ("created", wintypes.FILETIME),
                ("accessed", wintypes.FILETIME),
                ("modified", wintypes.FILETIME),
                ("volume", wintypes.DWORD),
                ("size_high", wintypes.DWORD),
                ("size_low", wintypes.DWORD),
                ("links", wintypes.DWORD),
                ("index_high", wintypes.DWORD),
                ("index_low", wintypes.DWORD),
            ]

        class AceHeader(ctypes.Structure):
            _fields_ = [
                ("kind", ctypes.c_ubyte), ("flags", ctypes.c_ubyte),
                ("size", wintypes.WORD),
            ]

        class AclSizeInfo(ctypes.Structure):
            _fields_ = [
                ("ace_count", wintypes.DWORD),
                ("bytes_in_use", wintypes.DWORD),
                ("bytes_free", wintypes.DWORD),
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        advapi = ctypes.WinDLL("advapi32", use_last_error=True)
        kernel.CreateFileW.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
            ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
        ]
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.GetFileInformationByHandle.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(FileInfo)]
        kernel.GetFileInformationByHandle.restype = wintypes.BOOL
        kernel.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
        kernel.GetDriveTypeW.restype = wintypes.UINT
        kernel.GetVolumeInformationW.argtypes = [
            wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
            wintypes.LPWSTR, wintypes.DWORD,
        ]
        kernel.GetVolumeInformationW.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p

        advapi.GetSecurityInfo.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
            ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        advapi.GetSecurityInfo.restype = wintypes.DWORD
        advapi.GetSecurityDescriptorControl.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(wintypes.WORD),
            ctypes.POINTER(wintypes.DWORD),
        ]
        advapi.GetSecurityDescriptorControl.restype = wintypes.BOOL
        advapi.IsValidAcl.argtypes = [ctypes.c_void_p]
        advapi.IsValidAcl.restype = wintypes.BOOL
        advapi.GetAclInformation.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p,
            wintypes.DWORD, wintypes.DWORD,
        ]
        advapi.GetAclInformation.restype = wintypes.BOOL
        advapi.GetAce.argtypes = [
            ctypes.c_void_p, wintypes.DWORD,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        advapi.GetAce.restype = wintypes.BOOL
        advapi.IsValidSid.argtypes = [ctypes.c_void_p]
        advapi.IsValidSid.restype = wintypes.BOOL
        advapi.GetLengthSid.argtypes = [ctypes.c_void_p]
        advapi.GetLengthSid.restype = wintypes.DWORD
        advapi.ConvertSidToStringSidW.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p),
        ]
        advapi.ConvertSidToStringSidW.restype = wintypes.BOOL

        def read_sid(sid_pointer: int) -> str:
            if not sid_pointer or not advapi.IsValidSid(sid_pointer):
                raise HeldWindowsRootError("Windows descriptor SID refused")
            allocated = ctypes.c_void_p()
            if not advapi.ConvertSidToStringSidW(
                    sid_pointer, ctypes.byref(allocated)):
                raise HeldWindowsRootError("Windows descriptor SID refused")
            try:
                sid = ctypes.wstring_at(allocated.value)
            finally:
                if allocated.value:
                    kernel.LocalFree(allocated)
            if not 7 <= len(sid) <= 256:
                raise HeldWindowsRootError("Windows descriptor SID refused")
            return sid

        def strict_private_dacl(handle: object) -> tuple[object, ...]:
            owner = ctypes.c_void_p()
            acl = ctypes.c_void_p()
            descriptor = ctypes.c_void_p()
            result = advapi.GetSecurityInfo(
                handle, 1, 0x5, ctypes.byref(owner), None,
                ctypes.byref(acl), None, ctypes.byref(descriptor))
            try:
                if result != 0 or not descriptor.value or not acl.value:
                    raise HeldWindowsRootError("Windows private DACL refused")
                if read_sid(owner.value) != current_user_sid:
                    raise HeldWindowsRootError("Windows private owner refused")
                control = wintypes.WORD()
                revision = wintypes.DWORD()
                if (not advapi.GetSecurityDescriptorControl(
                        descriptor, ctypes.byref(control),
                        ctypes.byref(revision))
                        or not control.value & 0x1000
                        or not advapi.IsValidAcl(acl)):
                    raise HeldWindowsRootError("Windows private DACL refused")
                size = AclSizeInfo()
                if (not advapi.GetAclInformation(
                        acl, ctypes.byref(size), ctypes.sizeof(size), 2)
                        or not 1 <= size.ace_count <= 16
                        or not 8 <= size.bytes_in_use <= 4096):
                    raise HeldWindowsRootError("Windows private ACEs refused")
                user_mask = 0
                entries = []
                for n in range(size.ace_count):
                    ace = ctypes.c_void_p()
                    if not advapi.GetAce(acl, n, ctypes.byref(ace)):
                        raise HeldWindowsRootError("Windows private ACE refused")
                    header = ctypes.cast(ace, ctypes.POINTER(AceHeader)).contents
                    if (header.kind != 0 or header.flags & 0x10
                            or not 16 <= header.size <= 4096):
                        raise HeldWindowsRootError("Windows private ACE refused")
                    mask = ctypes.c_uint32.from_address(ace.value + 4).value
                    sid_at = ace.value + 8
                    if (not advapi.IsValidSid(sid_at)
                            or advapi.GetLengthSid(sid_at) > header.size - 8):
                        raise HeldWindowsRootError("Windows private ACE refused")
                    trustee = read_sid(sid_at)
                    if trustee not in {current_user_sid, _SYSTEM_SID}:
                        raise HeldWindowsRootError("Windows private trustee refused")
                    # Inherit-only ACEs cannot grant effective root access.
                    if trustee == current_user_sid and not header.flags & 0x08:
                        user_mask |= mask
                    entries.append((
                        "CURRENT_USER" if trustee == current_user_sid else "SYSTEM",
                        mask, header.flags,
                    ))
                if (user_mask & _FULL_ACCESS != _FULL_ACCESS
                        and not user_mask & _GENERIC_ALL):
                    raise HeldWindowsRootError("Windows private owner rights refused")
                return tuple(entries)
            finally:
                if descriptor.value:
                    kernel.LocalFree(descriptor)

        disk = parts[0] + "\\"
        if kernel.GetDriveTypeW(disk) != 3:
            raise HeldWindowsRootError("Windows state volume refused")
        fs_name = ctypes.create_unicode_buffer(32)
        if (not kernel.GetVolumeInformationW(
                disk, None, 0, None, None, None, fs_name, len(fs_name))
                or fs_name.value.upper() != "NTFS"):
            raise HeldWindowsRootError("Windows state filesystem refused")

        pieces = [disk]
        for name in parts[1:]:
            pieces.append(pieces[-1].rstrip("\\") + "\\" + name)
        observed = []
        previous_volume = None
        for n, component in enumerate(pieces):
            handle = kernel.CreateFileW(
                component, 0x00020080, 0x7, None, 3,
                0x02000000 | 0x00200000, None)
            if handle is None or handle == ctypes.c_void_p(-1).value:
                raise HeldWindowsRootError("Windows root handle refused")
            try:
                info = FileInfo()
                if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
                    raise HeldWindowsRootError("Windows root identity refused")
                file_id = (int(info.volume),
                           (int(info.index_high) << 32) | info.index_low)
                if (not info.attributes & 0x10
                        or info.attributes & 0x400
                        or info.links != 1
                        or file_id[1] == 0
                        or (previous_volume is not None
                            and file_id[0] != previous_volume)):
                    raise HeldWindowsRootError("Windows root alias refused")
                previous_volume = file_id[0]
                acl = (strict_private_dacl(handle)
                       if inspect_private_dacl and n == len(pieces) - 1
                       else ())
                observed.append((file_id, int(info.attributes), acl))
            finally:
                kernel.CloseHandle(handle)
        return tuple(observed)
    except (OSError, ValueError, OverflowError, AttributeError, TypeError):
        raise HeldWindowsRootError("Windows root inspection refused") from None


def inspect_held_windows_root_candidate(
    *, project_key: str, project_root: str, state_root: str,
) -> dict[str, object]:
    """Diagnostic for the ORIGINAL #168 per-project state directory ONLY.

    Requires pre-existing VresOS/projects/<hashed-key> in the trusted local
    app-data folder, separate from the selected project. It NEVER grants
    capture, project writes, cleanup, rollback or protected Fable authority.
    """
    if (os.name != "nt" or type(project_key) is not str
            or not 1 <= len(project_key) <= 256
            or any(ord(c) < 32 or ord(c) == 127 for c in project_key)):
        raise HeldWindowsRootError("Windows project binding refused")
    try:
        key_hash = hashlib.sha256(project_key.encode("utf-8", "strict")).hexdigest()
    except UnicodeError:
        raise HeldWindowsRootError("Windows project binding refused") from None
    expected_path = (
        _trusted_local_appdata().rstrip("\\")
        + "\\VresOS\\projects\\" + key_hash[:24]
    )
    expected = _local_drive_components(expected_path)
    provided = _local_drive_components(state_root)
    _local_drive_components(project_root)
    if tuple(x.casefold() for x in provided) != tuple(
            x.casefold() for x in expected):
        raise HeldWindowsRootError("Windows state location refused")
    try:
        sid = _trusted_current_token_sid()
        first = _windows_handle_chain(
            state_root, sid, inspect_private_dacl=True)
        project = _windows_handle_chain(
            project_root, sid, inspect_private_dacl=False)
        last = _windows_handle_chain(
            state_root, sid, inspect_private_dacl=True)
    except (OSError, ValueError, OverflowError, AttributeError, TypeError):
        raise HeldWindowsRootError("Windows owner-private root refused") from None
    if (first != last or not first or not project
            or project[-1][0] in {entry[0] for entry in first}
            or first[-1][0] in {entry[0] for entry in project}):
        raise HeldWindowsRootError("Windows root identity drift refused")
    return {
        "state": "PROVISIONAL_WINDOWS_OWNER_ROOT_DIAGNOSTIC_ONLY",
        "protected_dacl_readback_observed": True,
        "current_user_owner_readback_observed": True,
        "reparse_and_hardlink_flags_refused": True,
        "cooperative_two_pass_handle_ids_agree": True,
        "atomic_handle_relative_confinement_proven": False,
        "independent_distinct_principal_acl_probe_proven": False,
        "encrypted_durable_recovery_proven": False,
        "capture_storage_authorized": False,
        "project_write_authorized": False,
        "protected_fable_high_granted": False,
    }
