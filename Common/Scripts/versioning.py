"""Async version checks against Docker Hub (digest + semver helpers) and Rich reporting.

Used by project scripts that register ``@checker`` functions for ``VER_*`` variables.
Requires dev extras: ``httpx``, ``rich``.
"""

from __future__ import annotations

import asyncio
import os
import re
import urllib.parse
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Final

import httpx
from rich.console import Console
from rich.table import Table
from rich.text import Text


class Status(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True)
class CheckResult:
    status: Status
    detail: str


@dataclass(frozen=True)
class DockerImageDigests:
    """Digest pair for ``image:current`` vs ``image:reference_tag``."""

    repository: str
    digest_current: str
    digest_reference: str


CheckerFn = Callable[[str], Awaitable[CheckResult]]

CHECKERS: dict[str, CheckerFn] = {}

_CONSOLE = Console()
_CONSOLE_ERR = Console(stderr=True)


def _status_cell(status: Status) -> Text:
    t = Text(status.value)
    if status == Status.PASS:
        t.stylize("bold green")
    elif status == Status.WARN:
        t.stylize("bold yellow")
    else:
        t.stylize("bold red")
    return t


def checker(suffix: str) -> Callable[[CheckerFn], CheckerFn]:
    """Register an async checker for ``VER_{suffix}`` (suffix is e.g. ``BUSYBOX``)."""

    def deco(fn: CheckerFn) -> CheckerFn:
        key = suffix.upper()
        if key in CHECKERS:
            raise ValueError(f"duplicate checker for {key!r}")
        CHECKERS[key] = fn
        return fn

    return deco


_http_client: ContextVar[httpx.AsyncClient | None] = ContextVar("_http_client", default=None)


def _client() -> httpx.AsyncClient:
    c = _http_client.get()
    if c is None:
        raise RuntimeError("HTTP client not installed (run inside run_async)")
    return c


_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?$")


def parse_semver(s: str) -> tuple[int, int, int] | None:
    s = s.strip()
    m = _SEMVER_RE.match(s)
    if not m:
        return None
    major, minor, patch = m.group(1), m.group(2), m.group(3)
    return (int(major), int(minor), int(patch) if patch is not None else 0)


def semver_newer_minor_or_patch(current: tuple[int, int, int], latest: tuple[int, int, int]) -> str:
    """Describe how ``latest`` is ahead of ``current`` (assumes latest > current)."""
    if latest[0] != current[0]:
        return f"newer major available ({'.'.join(map(str, latest))} vs {'.'.join(map(str, current))})"
    if latest[1] != current[1]:
        return f"newer minor available ({'.'.join(map(str, latest))} vs {'.'.join(map(str, current))})"
    return f"newer patch available ({'.'.join(map(str, latest))} vs {'.'.join(map(str, current))})"


REGISTRY: Final[str] = "https://registry-1.docker.io"
AUTH_URL: Final[str] = "https://auth.docker.io/token"
_ACCEPT_MANIFEST: Final[str] = (
    "application/vnd.docker.distribution.manifest.list.v2+json,"
    "application/vnd.oci.image.index.v1+json,"
    "application/vnd.docker.distribution.manifest.v2+json"
)

_token_cache: dict[str, str] = {}


async def registry_token_async(repository: str) -> str:
    if repository in _token_cache:
        return _token_cache[repository]
    q = urllib.parse.urlencode(
        {
            "service": "registry.docker.io",
            "scope": f"repository:{repository}:pull",
        }
    )
    r = await _client().get(f"{AUTH_URL}?{q}")
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict) or "token" not in data:
        raise RuntimeError("unexpected token response")
    tok = str(data["token"])
    _token_cache[repository] = tok
    return tok


async def manifest_digest_async(repository: str, tag: str) -> str:
    tok = await registry_token_async(repository)
    path = f"/v2/{repository}/manifests/{urllib.parse.quote(tag, safe=':')}"
    url = REGISTRY + path
    resp = await _client().head(
        url,
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": _ACCEPT_MANIFEST,
        },
    )
    resp.raise_for_status()
    d = resp.headers.get("docker-content-digest")
    if not d:
        raise RuntimeError("missing Docker-Content-Digest header")
    return d


async def manifest_exists_async(repository: str, tag: str) -> bool:
    """Return True if the registry has a manifest for ``tag`` (public pull scope)."""
    try:
        await manifest_digest_async(repository, tag)
        return True
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return False
        raise


async def fetch_docker_digests(image: str, current: str, reference_tag: str) -> DockerImageDigests:
    """
    Resolve digests for ``image:current`` and ``image:reference_tag`` (e.g. ``latest`` or ``1.29``).
    """
    cur = current.strip()
    ref = reference_tag.strip()
    if not cur:
        raise ValueError("empty current version string")
    if not ref:
        raise ValueError("empty reference tag")

    repository = image if "/" in image.strip() else f"library/{image.strip()}"

    d_cur, d_ref = await asyncio.gather(
        manifest_digest_async(repository, cur),
        manifest_digest_async(repository, ref),
    )
    return DockerImageDigests(
        repository=repository,
        digest_current=d_cur,
        digest_reference=d_ref,
    )


async def try_fetch_docker_digests(
    image: str, current: str, reference_tag: str,
) -> CheckResult | DockerImageDigests:
    try:
        return await fetch_docker_digests(image, current, reference_tag)
    except (httpx.HTTPError, ValueError, RuntimeError) as e:
        return CheckResult(Status.FAIL, f"registry error: {e}")


def pass_if_digests_match(digs: DockerImageDigests, reference_tag: str) -> CheckResult | None:
    """Return PASS when digests match; otherwise ``None``."""
    if digs.digest_current != digs.digest_reference:
        return None
    return CheckResult(
        Status.PASS,
        f"digest matches reference tag {reference_tag!r} ({digs.digest_current[:19]}…)",
    )


async def compare_docker_to_reference(
    image: str, current: str, reference_tag: str,
) -> CheckResult:
    """Fetch digests, PASS if they match, otherwise semver follow-up."""
    digs = await try_fetch_docker_digests(image, current, reference_tag)
    if isinstance(digs, CheckResult):
        return digs
    p = pass_if_digests_match(digs, reference_tag)
    return p if p is not None else await warn_if_newer_semver_exists(digs, current, reference_tag)


async def warn_if_newer_semver_exists(
    digs: DockerImageDigests, current: str, reference_tag: str,
) -> CheckResult:
    """After a digest mismatch: classify semver gap vs ``reference_tag`` or warn generically."""
    cur_t = parse_semver(current.strip())
    if cur_t is None:
        return CheckResult(
            Status.FAIL,
            f"digest differs from {reference_tag!r} and version {current!r} is not x.y or x.y.z",
        )

    try:
        newer = await probe_newer_semver(digs.repository, cur_t)
    except (httpx.HTTPError, RuntimeError) as e:
        return CheckResult(Status.FAIL, f"registry probe error: {e}")

    if newer is None:
        return CheckResult(
            Status.WARN,
            f"digest differs from {reference_tag!r} but no newer x.y.z tag found via probe "
            f"(current digest {digs.digest_current[:19]}…)",
        )

    return CheckResult(
        Status.WARN,
        semver_newer_minor_or_patch(cur_t, newer)
        + f"; reference digest {digs.digest_reference[:19]}…",
    )


async def probe_newer_semver(repository: str, cur: tuple[int, int, int]) -> tuple[int, int, int] | None:
    """Find a semver strictly greater than ``cur`` that exists as a tag (bounded HEAD probes)."""
    ma, mi, pa = cur

    async def exists(tag: str) -> bool:
        return await manifest_exists_async(repository, tag)

    for p in range(pa + 1, pa + 20):
        cand = (ma, mi, p)
        if await exists(f"{ma}.{mi}.{p}"):
            return cand

    for m in range(mi + 1, mi + 25):
        if await exists(f"{ma}.{m}.0"):
            return (ma, m, 0)
        for p in range(1, 12):
            if await exists(f"{ma}.{m}.{p}"):
                return (ma, m, p)

    for ma2 in range(ma + 1, ma + 8):
        if await exists(f"{ma2}.0.0"):
            return (ma2, 0, 0)

    return None


async def _run_one_key(key: str) -> tuple[str, CheckResult]:
    """Run one check or FAIL when env keys and registered checkers disagree."""
    suffix = key.removeprefix("VER_").upper()
    in_env = key in os.environ
    fn = CHECKERS.get(suffix)
    val = os.environ.get(key, "").strip()

    if in_env and fn is None:
        return (
            key,
            CheckResult(
                Status.FAIL,
                f"environment has {key!r} but no checker is registered for {suffix!r}",
            ),
        )
    if fn is not None and not in_env:
        return (
            key,
            CheckResult(
                Status.FAIL,
                f"checker is registered for {suffix!r} but {key!r} is not set",
            ),
        )
    assert fn is not None
    if not val:
        return (key, CheckResult(Status.FAIL, "empty value"))
    try:
        r = await fn(val)
    except Exception as e:
        return (key, CheckResult(Status.FAIL, repr(e)))
    return (key, r)


async def run_async() -> int:
    env_keys = {k for k in os.environ if k.startswith("VER_")}
    checker_keys = {f"VER_{s}" for s in CHECKERS}
    all_keys = sorted(env_keys | checker_keys)

    if not all_keys:
        _CONSOLE_ERR.print("[yellow]No VER_* variables and no checkers registered.[/yellow]")
        return 1

    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        token = _http_client.set(client)
        try:
            pairs = await asyncio.gather(*(_run_one_key(k) for k in all_keys))
        finally:
            _http_client.reset(token)

    table = Table(
        title="[bold]Version checks[/bold] (VER_*)",
        show_header=True,
        header_style="bold",
        border_style="dim",
        show_lines=True,
    )
    table.add_column("Variable", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_column("Status", justify="center", width=6)
    table.add_column("Detail")

    exit_fail = False
    env_checker_mismatch = False
    for key, r in sorted(pairs, key=lambda p: p[0]):
        val = os.environ.get(key, "").strip()
        table.add_row(key, val or "—", _status_cell(r.status), r.detail)
        if r.status == Status.FAIL:
            exit_fail = True
            d = r.detail
            if ("environment has" in d and "no checker is registered" in d) or (
                "checker is registered" in d and "is not set" in d
            ):
                env_checker_mismatch = True

    _CONSOLE.print(table)

    if env_checker_mismatch:
        raise SystemExit(
            "error: VER_* variables and registered checkers do not match (see table above).",
        )

    return 1 if exit_fail else 0


def run() -> int:
    return asyncio.run(run_async())
