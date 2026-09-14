"""Exercise Python entry points, not a real MCP transport or Windows runtime.

The only MCP substitution is its registration decorator. Calls below execute actual
Vres functions with isolated service doubles, so failures expose wiring/authority bugs.
"""
from __future__ import annotations
from contextlib import nullcontext
import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner
from test_audit_regressions import ScriptedConnection


@pytest.fixture
def surface(monkeypatch, tmp_path):
    class FastMCPRegistrationOnly:
        def __init__(self, *args, **kwargs):
            self.registered = {}
        def tool(self):
            def register(f):
                self.registered[f.__name__] = f
                return f
            return register
        def run(self):
            raise AssertionError('No real MCP transport in this unit test')
    for name in ('mcp', 'mcp.server', 'mcp.server.fastmcp'):
        monkeypatch.setitem(sys.modules, name, ModuleType(name))
    sys.modules['mcp.server.fastmcp'].FastMCP = FastMCPRegistrationOnly
    sys.modules.pop('vres_os.mcp_server', None)
    module = importlib.import_module('vres_os.mcp_server')
    monkeypatch.setattr(module, '_project', lambda root='.': (7, SimpleNamespace(root=tmp_path,key='P',name='test')))
    yield module
    sys.modules.pop('vres_os.mcp_server', None)


def test_mcp_registration_has_full_contract_and_no_pass_setter(surface):
    assert len(surface.mcp.registered) == 44
    assert 'procedure_get' in surface.mcp.registered
    assert 'validation_record' not in surface.mcp.registered
    assert 'optimization_gate' not in surface.mcp.registered


@pytest.mark.parametrize('owner,write,allowed', [(7,True,True),(7,False,True),(8,False,False),(None,False,True),(None,True,False)])
def test_public_node_scope_reads_and_writes(surface, monkeypatch, owner, write, allowed):
    import vres_os.db as db
    import vres_os.relations as relations
    monkeypatch.setattr(db, 'connect', lambda: nullcontext(object()))
    monkeypatch.setattr(relations, '_node', lambda *a: {'project_id':owner})
    if allowed:
        surface._require_node('knowledge','K',write=write)
    else:
        with pytest.raises(ValueError,match='outside the current project'):
            surface._require_node('knowledge','K',write=write)


def test_tool_session_validation_and_task_binding(surface, monkeypatch):
    import vres_os.db as db
    conn=ScriptedConnection([('provider_session_id=%s',{'ok':1})])
    monkeypatch.setattr(db,'connect',lambda:conn)
    repo=MagicMock();repo.begin_task.return_value='TASK-1'
    monkeypatch.setattr(surface,'Repository',lambda:repo)
    result=surface.task_begin('task','outcome','native-new-session')
    assert result=={'task_key':'TASK-1'}
    assert conn.calls[0][1]==(7,'native-new-session')
    repo.bind_session.assert_called_once_with(7,'native-new-session','TASK-1')


def test_task_complete_does_not_reach_completion_when_review_is_stale(surface,monkeypatch):
    import vres_os.validation as validation
    monkeypatch.setattr(surface,'_require_node',lambda *a,**k:None)
    review=MagicMock(spec=["assert_current"]);review.assert_current.side_effect=ValueError('review stale')
    monkeypatch.setattr(validation,'ValidationService',lambda:review)
    repo=MagicMock();monkeypatch.setattr(surface,'Repository',lambda:repo)
    with pytest.raises(ValueError,match='stale'):
        surface.task_complete('TASK-1','done')
    repo.complete_task.assert_not_called()


def test_procedure_get_authorizes_before_fetching_complete_method(surface,monkeypatch):
    auth=MagicMock();monkeypatch.setattr(surface,'_require_node',auth)
    service=MagicMock();service.get.return_value={'method':['append','aggregate']}
    monkeypatch.setattr(surface,'ProcedureService',lambda:service)
    assert surface.procedure_get('PROC',2)['method']==['append','aggregate']
    auth.assert_called_once_with('procedure','PROC')
    service.get.assert_called_once_with('PROC',2)


@pytest.mark.parametrize('accept,action', [(True,'procedure_candidate_decision'),(False,'procedure_candidate_reject')])
def test_candidate_decision_uses_exact_accept_or_reject_action(surface,monkeypatch,accept,action):
    monkeypatch.setattr(surface,'_require_node',lambda *a,**k:None)
    approvals=MagicMock();approvals.record_latest_user_approval.return_value='APP'
    procedures=MagicMock();procedures.decide_candidate.return_value={'decided':True}
    monkeypatch.setattr(surface,'ApprovalService',lambda:approvals)
    monkeypatch.setattr(surface,'ProcedureService',lambda:procedures)
    surface.procedure_decide_candidate('TASK','PROC',3,accept)
    call=approvals.record_latest_user_approval.call_args.kwargs
    assert call['approval_type']==action and call['subject_key']=='PROC:v3'
    procedures.decide_candidate.assert_called_once_with('PROC',3,accept=accept,approval_key='APP')


def test_global_source_publication_fails_before_service_write(surface,monkeypatch):
    service=MagicMock();monkeypatch.setattr(surface,'SourceService',lambda:service)
    with pytest.raises(ValueError,match='Company-wide publication is held'):
        surface.source_register('internal_document','title',company_wide=True)
    service.register.assert_not_called()


def test_onboarding_reports_worker_failure_without_claiming_vectors(surface,monkeypatch,tmp_path):
    import vres_os.workers as workers
    service=MagicMock();service.inventory.return_value={'embedding_jobs_queued':2}
    monkeypatch.setattr(surface,'OnboardingService',lambda:service)
    monkeypatch.setattr(surface,'ConfigStore',lambda:SimpleNamespace(load=lambda:SimpleNamespace(embeddings_enabled=True)))
    def fail(): raise OSError('worker error password=secret')
    monkeypatch.setattr(workers,'launch_embedding_worker',fail)
    out=surface.onboard_folder(str(tmp_path))
    service.inventory.assert_called_once_with(tmp_path,project_id=7)
    assert out['embedding_worker']['launched'] is False
    assert 'secret' not in out['embedding_worker']['error']


def test_cli_doctor_unconfigured_is_read_only(monkeypatch):
    import vres_os.cli as cli
    import vres_os.db as db
    monkeypatch.setattr(cli,'prerequisite_status',lambda:{'git':True,'claude':True,'codex':False})
    monkeypatch.setattr(cli,'ConfigStore',lambda:SimpleNamespace(load=lambda:SimpleNamespace(configured=False)))
    monkeypatch.setattr(importlib.util,'find_spec',lambda name:object())
    def fail(*a,**k): raise AssertionError('doctor must not contact DB while unconfigured')
    monkeypatch.setattr(db,'connect',fail)
    runner=CliRunner()
    assert runner.invoke(cli.app,['doctor','--allow-unconfigured']).exit_code==0
    assert runner.invoke(cli.app,['doctor']).exit_code==2


def test_cli_selftest_failure_has_failure_exit(monkeypatch):
    import vres_os.cli as cli
    import vres_os.selftest as selftest
    monkeypatch.setattr(selftest,'run_core_selftest',lambda:{'passed':False})
    result=CliRunner().invoke(cli.app,['selftest'])
    assert result.exit_code==2 and 'false' in result.output.lower()


def test_codex_adapter_stdin_and_read_only_contract(monkeypatch,tmp_path):
    import vres_os.codex as codex
    monkeypatch.setattr(codex.shutil,'which',lambda n:'/fake/codex')
    run=MagicMock(return_value=codex.CodexResult(True,'review',0))
    monkeypatch.setattr(codex,'run_bounded',run)
    assert codex.CodexAdapter().exec('review code',cwd=tmp_path,project_root=tmp_path).ok
    assert run.call_args.args[0]==['/fake/codex','exec','--sandbox','read-only','-']
    assert run.call_args.kwargs['prompt']=='review code'
    assert 'review code' not in run.call_args.args[0]


@pytest.mark.parametrize('bad', ['', 'password=do-not-send', 'x'*262145])
def test_codex_rejects_invalid_prompt_before_executable_lookup(monkeypatch,tmp_path,bad):
    import vres_os.codex as codex
    lookup=MagicMock();monkeypatch.setattr(codex.shutil,'which',lookup)
    with pytest.raises(ValueError):codex.CodexAdapter().exec(bad,cwd=tmp_path)
    lookup.assert_not_called()


def test_codex_missing_cli_is_explicit(monkeypatch,tmp_path):
    import vres_os.codex as codex
    monkeypatch.setattr(codex.shutil,'which',lambda n:None)
    assert codex.CodexAdapter().doctor().returncode==127
    assert codex.CodexAdapter().exec('review',cwd=tmp_path).returncode==127


def test_embedding_worker_does_not_loop_forever_when_idle(monkeypatch):
    import vres_os.embedding_worker as worker
    service=MagicMock();service.run_pending.side_effect=[{'processed':2},{'processed':0},{'processed':0}]
    monkeypatch.setattr(worker,'local_lock',lambda n:nullcontext(True))
    monkeypatch.setattr(worker,'EmbeddingService',lambda:service)
    monkeypatch.setattr(worker.time,'sleep',lambda n:None)
    assert worker.run_worker()==2
    assert service.run_pending.call_count==3


def test_embedding_worker_duplicate_does_not_load_model(monkeypatch):
    import vres_os.embedding_worker as worker
    monkeypatch.setattr(worker,'local_lock',lambda n:nullcontext(False))
    factory=MagicMock();monkeypatch.setattr(worker,'EmbeddingService',factory)
    assert worker.run_worker()==0
    factory.assert_not_called()


def test_worker_launch_uses_isolated_python_and_closes_parent_log(monkeypatch,tmp_path):
    import vres_os.workers as workers
    monkeypatch.setattr(workers,'logs_dir',lambda:tmp_path)
    def launch(args,**kwargs):
        assert '-I' in args
        assert kwargs['stdin']==workers.subprocess.DEVNULL
        assert not kwargs['stdout'].closed
        return SimpleNamespace(pid=123)
    popen=MagicMock(side_effect=launch);monkeypatch.setattr(workers.subprocess,'Popen',popen)
    assert workers.launch_embedding_worker()['pid']==123
    assert popen.call_args.kwargs['stdout'].closed


def test_review_queue_resolve_does_not_promote_and_redacts(monkeypatch):
    import vres_os.review as review
    conn=ScriptedConnection([('FOR UPDATE',{'status':'pending'}),('UPDATE vres.review_queue',None)])
    monkeypatch.setattr(review,'_connect',lambda:conn)
    review.ReviewQueueService().resolve(4,resolved_by='reviewer',resolution={'reason':'token=secret'},project_id=7)
    assert 'secret' not in str(conn.calls[-1][1])
    assert conn.calls[0][1]==(4,7,7)
    assert not any('knowledge_items' in sql for sql,_ in conn.calls)


def test_capability_change_does_not_inherit_old_proof(monkeypatch):
    import vres_os.capabilities as capabilities
    conn=ScriptedConnection([('pg_advisory_xact_lock',None),('SELECT name',{'name':'Old','description':'Old knowledge','domain':'data'})])
    monkeypatch.setattr(capabilities,'_connect',lambda:conn)
    monkeypatch.setattr(capabilities,'require_company_approval',lambda *a,**k:11)
    with pytest.raises(ValueError,match='new key'):
        capabilities.CapabilityService().register('CAP','New','Different','data','cto')


def test_incomplete_procedure_metrics_do_not_consume_approval(surface,monkeypatch):
    monkeypatch.setattr(surface,'_require_node',lambda *a,**k:None)
    approvals=MagicMock();monkeypatch.setattr(surface,'ApprovalService',lambda:approvals)
    with pytest.raises(ValueError,match='together'):
        surface.procedure_accept('TASK','PROC','Name','desc','family',{},['run'],['keep'],['check'],{},quality_score=1)
    approvals.record_latest_user_approval.assert_not_called()


def test_shared_capability_catalog_cannot_be_overwritten_by_project_agent(surface,monkeypatch):
    service=MagicMock();monkeypatch.setattr(surface,'CapabilityService',lambda:service)
    with pytest.raises(ValueError,match='catalog authority'):
        surface.capability_register('CAP','Expert','Unverified expertise')
    service.register.assert_not_called()


def test_release_gate_refuses_disabled_assertions(tmp_path):
    import subprocess
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "must-not-exist"
    result = subprocess.run(
        [sys.executable, "-O", str(root / "scripts/release_gate.py"), "--output", str(output)],
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode == 2
    assert "assertions must remain enabled" in result.stderr
    assert not output.exists()
