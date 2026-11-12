"""Source-only Windows current-user DPAPI preimage candidate for ORIGINAL #168.

In-memory cryptographic boundary ONLY. This module never opens a project/state
path, saves plaintext, adjusts Windows ACLs or enables legacy held capture.
The existing #168 Windows storage gate stays CLOSED. Independent evidence for
protected DACLs, no-follow handles, exclusive crash-safe journal/flush/readback,
separate human write consent and #174 protected Fable is NOT_GRANTED.

DPAPI protects against other-user/offline disclosure under its OS assumptions.
It does not protect against same-user malware, privileged OS compromise, or
filesystem substitution. Do not use this as an independent security verdict.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re

_MAX_PREIMAGE = 1024 * 1024
_MAX_ENVELOPE = _MAX_PREIMAGE + 65536
_ENVELOPE_PREFIX = b"VRES-168-DPAPI-PREIMAGE-V1\x00"
_INNER_PREFIX = b"VRES-168-INNER-PREIMAGE-V1\x00"
_DOMAIN = b"VRES-OS/168/WINDOWS/CURRENT-USER/DPAPI/V1\x00"


class HeldWindowsPrivacyError(RuntimeError):
    """Redacted Windows held-preimage candidate refusal; no path or secret."""


def _preimage_context(
    *, project_key: str, capture_id: str, number: int,
    plan_digest: str, expected_sha256: str,
) -> bytes:
    """Canonical domain-separated identity, not a user-issued approval.

    Project key is hashed to avoid carrying its raw identifier in metadata.
    The exact capture ID, selected number, plan and expected preimage digest
    are DPAPI optional entropy inputs; none is a Fable/authenticated journal.
    """
    if (type(project_key) is not str or not 1 <= len(project_key) <= 256
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in project_key)):
        raise HeldWindowsPrivacyError("Held preimage project binding invalid")
    if (type(number) is not int or not 1 <= number <= 60
            or type(capture_id) is not str
            or re.fullmatch(r"[0-9a-f]{32}", capture_id) is None
            or type(plan_digest) is not str
            or re.fullmatch(r"[0-9a-f]{64}", plan_digest) is None
            or type(expected_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None):
        raise HeldWindowsPrivacyError("Held preimage identity metadata invalid")
    try:
        key = hashlib.sha256(project_key.encode("utf-8", errors="strict")).hexdigest()
    except UnicodeError:
        raise HeldWindowsPrivacyError("Held preimage project binding invalid") from None
    return json.dumps({
        "format": "VRES_168_CURRENT_USER_DPAPI_PREIMAGE_V1",
        "project_key_sha256": key,
        "capture_id": capture_id,
        "target_number": number,
        "plan_digest": plan_digest,
        "preimage_sha256": expected_sha256,
    }, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def _trusted_current_token_sid() -> str:
    """Read the actual Windows process-token user SID, never a supplied SID."""
    if os.name != "nt":
        raise HeldWindowsPrivacyError("Windows token API unavailable")
    try:
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        advapi = ctypes.WinDLL("advapi32", use_last_error=True)
        kernel.GetCurrentProcess.argtypes = []
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        advapi.OpenProcessToken.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
        advapi.OpenProcessToken.restype = wintypes.BOOL
        advapi.GetTokenInformation.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
            wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        advapi.GetTokenInformation.restype = wintypes.BOOL
        advapi.ConvertSidToStringSidW.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        advapi.ConvertSidToStringSidW.restype = wintypes.BOOL

        class SidAndAttributes(ctypes.Structure):
            _fields_ = [("sid", ctypes.c_void_p), ("attributes", wintypes.DWORD)]

        class TokenUser(ctypes.Structure):
            _fields_ = [("user", SidAndAttributes)]

        token = wintypes.HANDLE()
        if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008,
                                       ctypes.byref(token)):
            raise HeldWindowsPrivacyError("Windows user token unavailable")
        try:
            needed = wintypes.DWORD()
            first = advapi.GetTokenInformation(
                token, 1, None, 0, ctypes.byref(needed))
            if (first or ctypes.get_last_error() != 122
                    or not 0 < needed.value <= 65536):
                raise HeldWindowsPrivacyError("Windows token identity refused")
            buffer = ctypes.create_string_buffer(needed.value)
            if not advapi.GetTokenInformation(
                token, 1, buffer, needed.value, ctypes.byref(needed)):
                raise HeldWindowsPrivacyError("Windows token identity refused")
            token_user = ctypes.cast(
                buffer, ctypes.POINTER(TokenUser)).contents
            if not token_user.user.sid:
                raise HeldWindowsPrivacyError("Windows token identity refused")
            sid_pointer = ctypes.c_void_p()
            if not advapi.ConvertSidToStringSidW(
                token_user.user.sid, ctypes.byref(sid_pointer)):
                raise HeldWindowsPrivacyError("Windows token identity refused")
            try:
                sid = ctypes.wstring_at(sid_pointer.value)
            finally:
                if sid_pointer.value:
                    kernel.LocalFree(sid_pointer)
            if not 7 <= len(sid) <= 256 or re.fullmatch(
                    r"S-1-(?:[0-9]+-)+[0-9]+", sid) is None:
                raise HeldWindowsPrivacyError("Windows token identity refused")
            return sid
        finally:
            kernel.CloseHandle(token)
    except (OSError, ValueError, OverflowError, AttributeError, TypeError):
        raise HeldWindowsPrivacyError("Windows token identity refused") from None


def _current_user_entropy(context: bytes) -> bytes:
    if type(context) is not bytes or len(context) > 2048:
        raise HeldWindowsPrivacyError("Held preimage identity context refused")
    sid = _trusted_current_token_sid()
    return hashlib.sha256(_DOMAIN + sid.encode("ascii") + b"\x00" + context).digest()


def _current_user_dpapi(data: bytes, entropy: bytes, *, decrypt: bool) -> bytes:
    """CryptProtectData/CryptUnprotectData with current USER scope and no UI.

    This API works in memory only, makes no claim about zeroized Python buffers
    and MUST NOT be used to justify persistent storage until WPR-01..10 pass.
    """
    if (os.name != "nt" or type(data) is not bytes or not data
            or len(data) > _MAX_ENVELOPE
            or type(entropy) is not bytes or len(entropy) != 32):
        raise HeldWindowsPrivacyError("Windows DPAPI operation refused")
    try:
        import ctypes
        from ctypes import wintypes

        class DataBlob(ctypes.Structure):
            _fields_ = [("length", wintypes.DWORD),
                        ("data", ctypes.POINTER(ctypes.c_ubyte))]

        def blob(raw: bytes):
            backing = ctypes.create_string_buffer(raw, len(raw))
            return DataBlob(
                len(raw), ctypes.cast(backing, ctypes.POINTER(ctypes.c_ubyte))
            ), backing

        incoming, incoming_backing = blob(data)
        extra, extra_backing = blob(entropy)
        _buffers_alive = (incoming_backing, extra_backing)
        output = DataBlob()
        crypt = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        if decrypt:
            fn = crypt.CryptUnprotectData
            fn.argtypes = [
                ctypes.POINTER(DataBlob), ctypes.POINTER(ctypes.c_void_p),
                ctypes.POINTER(DataBlob), ctypes.c_void_p, ctypes.c_void_p,
                wintypes.DWORD, ctypes.POINTER(DataBlob)]
            fn.restype = wintypes.BOOL
            success = fn(
                ctypes.byref(incoming), None, ctypes.byref(extra),
                None, None, 0x01, ctypes.byref(output))
        else:
            fn = crypt.CryptProtectData
            fn.argtypes = [
                ctypes.POINTER(DataBlob), wintypes.LPCWSTR,
                ctypes.POINTER(DataBlob), ctypes.c_void_p, ctypes.c_void_p,
                wintypes.DWORD, ctypes.POINTER(DataBlob)]
            fn.restype = wintypes.BOOL
            success = fn(
                ctypes.byref(incoming), "Vres-OS held preimage",
                ctypes.byref(extra), None, None, 0x01, ctypes.byref(output))
        try:
            if not success or not output.data or not 0 < output.length <= _MAX_ENVELOPE:
                raise HeldWindowsPrivacyError("Windows DPAPI refused preimage operation")
            return ctypes.string_at(output.data, output.length)
        finally:
            if output.data:
                kernel.LocalFree(ctypes.cast(output.data, ctypes.c_void_p))
    except (OSError, ValueError, OverflowError, AttributeError, TypeError):
        raise HeldWindowsPrivacyError("Windows DPAPI refused preimage operation") from None


def protect_held_preimage(
    raw: bytes, *, project_key: str, capture_id: str, number: int,
    plan_digest: str,
) -> bytes:
    """Candidate current-user encrypted envelope; NEVER persists it to disk."""
    if type(raw) is not bytes or len(raw) > _MAX_PREIMAGE:
        raise HeldWindowsPrivacyError("Held preimage content exceeds bounded policy")
    digest = hashlib.sha256(raw).hexdigest()
    context = _preimage_context(
        project_key=project_key, capture_id=capture_id, number=number,
        plan_digest=plan_digest, expected_sha256=digest)
    entropy = _current_user_entropy(context)
    body = _INNER_PREFIX + len(raw).to_bytes(4, "big") + raw
    encrypted = _current_user_dpapi(body, entropy, decrypt=False)
    envelope = _ENVELOPE_PREFIX + encrypted
    if len(envelope) > _MAX_ENVELOPE:
        raise HeldWindowsPrivacyError("Windows DPAPI envelope exceeded bound")
    return envelope


def recover_held_preimage(
    envelope: bytes, *, project_key: str, capture_id: str, number: int,
    plan_digest: str, expected_sha256: str,
) -> bytes:
    """Candidate exact-context decrypt and bounded local bytes readback ONLY."""
    if (type(envelope) is not bytes
            or not envelope.startswith(_ENVELOPE_PREFIX)
            or len(envelope) <= len(_ENVELOPE_PREFIX)
            or len(envelope) > _MAX_ENVELOPE):
        raise HeldWindowsPrivacyError("Held DPAPI envelope format refused")
    context = _preimage_context(
        project_key=project_key, capture_id=capture_id, number=number,
        plan_digest=plan_digest, expected_sha256=expected_sha256)
    raw = _current_user_dpapi(
        envelope[len(_ENVELOPE_PREFIX):],
        _current_user_entropy(context), decrypt=True)
    if (not raw.startswith(_INNER_PREFIX)
            or len(raw) < len(_INNER_PREFIX) + 4):
        raise HeldWindowsPrivacyError("Held DPAPI plaintext format refused")
    size = int.from_bytes(raw[len(_INNER_PREFIX):len(_INNER_PREFIX) + 4], "big")
    preimage = raw[len(_INNER_PREFIX) + 4:]
    if (size > _MAX_PREIMAGE or size != len(preimage)
            or not hmac.compare_digest(
                hashlib.sha256(preimage).hexdigest(), expected_sha256)):
        raise HeldWindowsPrivacyError("Held DPAPI preimage evidence mismatch")
    return preimage
