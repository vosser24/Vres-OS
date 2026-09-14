"""Reproducible LOCAL gate. Does not claim Windows, PostgreSQL or live-model proof."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {'.git', '.pytest_cache', '__pycache__', 'build', 'dist', '.venv', 'htmlcov', '.live-test-venv'}


def files():
    for p in sorted(ROOT.rglob('*')):
        rel = p.relative_to(ROOT)
        if p.is_file() and not any(x in EXCLUDE or x.endswith('.egg-info') for x in rel.parts):
            yield p


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def command(args: list[str], output: Path, name: str, *, cwd: Path = ROOT, env: dict | None = None, timeout: int = 180):
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=timeout, check=False)
    (output / (name + '.log')).write_text(
        f'COMMAND: {json.dumps(args)}\nCWD: {cwd}\nEXIT: {result.returncode}\n\nSTDOUT\n'
        + result.stdout + '\nSTDERR\n' + result.stderr, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'{name} failed with exit {result.returncode}; inspect its log')
    return result.stdout


def _tool_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    return sorted(n.name for n in tree.body if isinstance(n, ast.FunctionDef)
                  and any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                          and d.func.attr == 'tool' for d in n.decorator_list))


def structure():
    import yaml
    from packaging.version import Version
    config = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    if config['build-system']['build-backend'] != 'setuptools.build_meta':
        raise ValueError('Unexpected build backend')
    plugin = ROOT / 'plugins/vres-os'
    manifest = json.loads((plugin / '.claude-plugin/plugin.json').read_text())
    assert Version(manifest['version']) == Version(config['project']['version'])
    agents, skills = [], []
    for glob, dest in [('agents/*.md', agents), ('skills/*/SKILL.md', skills)]:
        for path in plugin.glob(glob):
            text = path.read_text(encoding='utf-8')
            assert text.startswith('---\n'), path
            data = yaml.safe_load(text.split('---', 2)[1])
            assert isinstance(data, dict) and data.get('name') and data.get('description'), path
            assert data['name'] not in dest, path
            dest.append(data['name'])
            if glob.startswith('agents'):
                assert data.get('model', 'inherit') in {'inherit', 'default', 'best', 'fable', 'opus', 'sonnet', 'haiku'}, path
                assert not {'hooks', 'permissionMode', 'mcpServers'} & data.keys(), path
                if data['name'] == 'validator':
                    assert data['model'] == 'fable' and data['effort'] == 'high'
    hooks = json.loads((plugin / 'hooks/hooks.json').read_text())['hooks']
    assert {'SessionStart', 'UserPromptSubmit', 'PreCompact', 'PostCompact', 'Stop', 'SessionEnd', 'SubagentStop'} <= hooks.keys()
    for groups in hooks.values():
        for group in groups:
            for hook in group['hooks']:
                assert hook['type'] == 'command' and isinstance(hook.get('args'), list)
                for arg in hook['args']:
                    if '${CLAUDE_PLUGIN_ROOT}/' in arg:
                        assert (plugin / arg.split('${CLAUDE_PLUGIN_ROOT}/', 1)[1]).is_file()
    for path in files():
        if path.suffix == '.json':
            json.loads(path.read_text(encoding='utf-8'))
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    baseline = json.loads((ROOT / 'scripts/migration-baseline.json').read_text())['sha256']
    migrations = sorted((ROOT / 'src/vres_os/migrations').glob('*.sql'))
    numbers = [int(p.name[:3]) for p in migrations]
    assert numbers == list(range(1, len(migrations)+1)), numbers
    for p in migrations:
        if p.name in baseline:
            assert digest(p.read_bytes()) == baseline[p.name], f'Recovered migration changed: {p.name}'
    assert set(baseline) <= {p.name for p in migrations}
    tables = set()
    # Inventory only: not a PostgreSQL parser or runtime dependency validator.
    for p in migrations:
        tables.update(re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?vres\.([a-z_]+)', p.read_text(), re.I))
    for p in ROOT.rglob('*.md'):
        if any(x in EXCLUDE or x.endswith('.egg-info') for x in p.relative_to(ROOT).parts):
            continue
        text = p.read_text(encoding='utf-8')
        for link in re.findall(r'\]\(([^\s)]+)\)', text):
            if re.match(r'^(https?://|mailto:|#)', link):
                continue
            target = link.split('#')[0]
            if target:
                assert (p.parent / target).exists(), f'Broken local documentation link {p}: {target}'
    names = _tool_names(ROOT / 'src/vres_os/mcp_server.py')
    company_names = _tool_names(ROOT / 'src/vres_os/company_mcp.py')
    assert 'procedure_get' in names and 'optimization_gate' not in names and 'validation_record' not in names
    assert len(names) == len(set(names))
    assert {
        'company_approval_record',
        'company_source_register',
        'company_knowledge_propose',
        'company_registry_register',
        'company_capability_register',
    } <= set(company_names)
    assert len(company_names) == len(set(company_names))
    return {'package_version': config['project']['version'], 'plugin_version': manifest['version'],
            'agents': sorted(agents), 'skills': sorted(skills), 'mcp_tools': names,
            'company_mcp_tools': company_names,
            'migrations': {p.name: digest(p.read_bytes()) for p in migrations},
            'table_inventory': sorted(tables), 'migration_proof': 'numbering/hash/inventory only; no PostgreSQL execution'}


def package(output: Path, env: dict):
    wheel_dir = output / 'wheel'
    wheel_dir.mkdir()
    command([sys.executable, '-m', 'pip', 'wheel', '.', '--no-deps', '--no-build-isolation',
             '--wheel-dir', str(wheel_dir)], output, 'wheel-build', env=env)
    wheels = list(wheel_dir.glob('*.whl'))
    assert len(wheels) == 1
    path = wheels[0]
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        compared = []
        for source in sorted((ROOT / 'src/vres_os').rglob('*')):
            if source.is_file() and source.suffix in {'.py', '.sql'} and '__pycache__' not in source.parts:
                name = str(source.relative_to(ROOT / 'src')).replace('\\', '/')
                assert name in names, f'Wheel missing {name}'
                assert z.read(name) == source.read_bytes(), f'Wheel byte mismatch: {name}'
                compared.append(name)
        assert not any(n.endswith(('.pyc', '.env')) for n in names)
    with tempfile.TemporaryDirectory(prefix='vres-wheel-smoke-') as d:
        target = Path(d) / 'installed'
        target.mkdir()
        command([sys.executable, '-m', 'pip', 'install', '--no-deps', '--no-compile', '--target', str(target), str(path)],
                output, 'wheel-install', cwd=Path(d), env=env)
        smoke = """import sys, pathlib, importlib.resources
sys.path.insert(0, sys.argv[1])
import vres_os, vres_os.cli, vres_os.metrics, vres_os.optimization, vres_os.company_mcp
assert pathlib.Path(vres_os.__file__).resolve().is_relative_to(pathlib.Path(sys.argv[1]).resolve())
assert callable(vres_os.company_mcp.main)
assert len(list(importlib.resources.files('vres_os').joinpath('migrations').iterdir())) >= 10
print('installed runtime source:', vres_os.__file__)
print('selected imports, company MCP and migration resources: passed')
"""
        command([sys.executable, '-I', '-X', 'utf8', '-c', smoke, str(target)], output, 'wheel-import-smoke', cwd=Path(d), env=env)
    return {'filename': path.name, 'sha256': digest(path.read_bytes()), 'bytes': path.stat().st_size,
            'source_files_compared': compared, 'proof': 'offline wheel build, exact Python/SQL bytes, selected installed imports; not full dependency resolution'}


def ledger(output: Path, coverage_data: dict):
    coverage_files = coverage_data.get('files', {})
    rows = []
    for p in files():
        rel = p.relative_to(ROOT).as_posix()
        if p.name.startswith('.coverage') or p.suffix == '.pyc':
            continue
        info = coverage_files.get(rel, {})
        if p.suffix == '.py' and rel.startswith('src/'):
            summary = info.get('summary')
            label = 'executed lines measured; see limitations and branch coverage' if summary and summary['covered_lines'] else 'AST/compile only; no measured execution'
        elif p.suffix == '.ps1':
            summary = None; label = 'source/static contract review only; PowerShell NOT EXECUTED'
        elif p.suffix == '.sql':
            summary = None; label = 'packaging/hash/sequence and scripted SQL boundary checks; PostgreSQL NOT EXECUTED'
        elif rel.startswith('tests/') and p.suffix == '.py':
            summary = None; label = 'pytest source; integration modules may be skipped (see JUnit)'
        elif p.suffix == '.md':
            summary = None; label = 'source reconciliation/local links; agent behavior NOT live-evaluated'
        elif p.suffix == '.json':
            summary = None; label = 'JSON parse; field contracts where tested'
        elif p.suffix == '.xlsx':
            summary = None; label = 'synthetic fixture; read-only first-sheet/expected-result regression test'
        else:
            summary = None; label = 'manifested source asset; no automatic runtime assurance'
        rows.append({'path': rel, 'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size,
                     'validation': label, 'coverage': summary})
    (output / 'file-ledger.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    lines = ['# File-level evidence ledger', '', 'A row is not a claim that every behavior/branch is verified.', '',
             '| File | Evidence | Line coverage |', '|---|---|---|']
    for row in rows:
        cov = row['coverage']; display = f"{cov['covered_lines']}/{cov['num_statements']}" if cov else '—'
        lines.append(f"| `{row['path']}` | {row['validation']} | {display} |")
    (output / 'FILE-LEDGER.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return len(rows)


def main():
    # This gate deliberately uses assertions for source contracts. Never silently
    # strip them with Python -O / PYTHONOPTIMIZE.
    if not __debug__:
        print("Release gate refuses optimized Python: assertions must remain enabled", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out == ROOT or out.is_relative_to(ROOT):
        parser.error('Evidence output must be outside the source checkout')
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        parser.error('Use a new empty evidence directory; do not mix test runs')
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'scope': 'local/static/runtime-unit gate only',
              'python': sys.version, 'platform': sys.platform, 'status': 'RUNNING', 'gates': {}}
    env = dict(os.environ, PYTHONUTF8='1', COVERAGE_FILE=str(out / '.coverage'), PIP_DISABLE_PIP_VERSION_CHECK='1', PIP_NO_INDEX='1')
    # Do not allow an ambient credential to unexpectedly enable real integration tests in this local gate.
    env.pop('VRES_DATABASE_URL', None)
    env.pop('VRES_TEST_DATABASE_URL', None)
    env.pop('VRES_ALLOW_TEST_DB', None)
    try:
        if shutil.which('git') and (ROOT / '.git').exists():
            report['git_commit'] = command(['git', 'rev-parse', 'HEAD'], out, 'git-commit').strip()
            report['git_tree'] = command(['git', 'rev-parse', 'HEAD^{tree}'], out, 'git-tree').strip()
            report['dirty'] = bool(command(['git', 'status', '--porcelain'], out, 'git-status').strip())
            epoch = command(['git', 'show', '-s', '--format=%ct', 'HEAD'], out, 'git-epoch').strip()
            env['SOURCE_DATE_EPOCH'] = epoch
            command(['git', 'diff', '--check'], out, 'git-diff-check')
        report['gates']['structure'] = structure()
        command([sys.executable, '-m', 'pytest', '-o', 'addopts=', '-q', '-ra',
                 '--junitxml', str(out / 'junit.xml'), '--cov=vres_os', '--cov-branch',
                 '--cov-report=term-missing', '--cov-report=json:' + str(out / 'coverage.json')],
                out, 'pytest', env=env)
        suites = ET.parse(out / 'junit.xml').getroot()
        cases = list(suites.iter('testcase'))
        report['gates']['tests'] = {'passed': sum(c.find('skipped') is None and c.find('failure') is None and c.find('error') is None for c in cases),
                                   'skipped': sum(c.find('skipped') is not None for c in cases),
                                   'skip_reasons': [(c.find('skipped').text or c.find('skipped').get('message')) for c in cases if c.find('skipped') is not None]}
        cov = json.loads((out / 'coverage.json').read_text())
        report['gates']['coverage'] = cov['totals']
        command([sys.executable, '-m', 'compileall', '-q', 'src', 'tests', 'scripts'], out, 'compileall', env=env)
        report['gates']['package'] = package(out, env)
        report['file_count'] = ledger(out, cov)
        inventory = {d.metadata['Name']: d.version for d in metadata.distributions() if d.metadata.get('Name')}
        (out / 'environment-packages.json').write_text(json.dumps(inventory, indent=2, sort_keys=True), encoding='utf-8')
        report['unexecuted'] = ['PowerShell/Windows installer', 'PostgreSQL/psycopg engine', 'Windows Credential Manager',
                                'live Claude plugin/hooks/models', 'real MCP SDK transport', 'live Codex',
                                'actual downloaded SentenceTransformer', 'full runtime dependency resolution', 'separate live validator model']
        report['status'] = 'PASSED_WITH_EXPLICIT_LIVE_GATES'
    except Exception as exc:
        report['status'] = 'FAILED'
        report['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        (out / 'gate-result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report.get(k) for k in ('status', 'git_commit', 'dirty', 'error')}, indent=2))
    print('Tests:', report['gates'].get('tests', 'not reached'))
    print('Evidence:', out)
    return 0 if report['status'].startswith('PASSED') else 1


if __name__ == '__main__':
    raise SystemExit(main())
