"""#176 E7 B3: E5 v5 observed-episode rank determinism (DB-free); v1-v4 stay replayable."""

import inspect
import itertools
from datetime import timedelta

from test_experience_retrieval import NOW, _episode_row, _proc_row, _req

from vres_os import experience_retrieval as er
from vres_os.experience import _sha256

V1 = "7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9"
V2 = "0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5"
V3 = "272b10b6042a77bb79812ec637ec9296e28867628285165775c5aeee4af1a4ad"
V4 = "4e468f39ee775aebe33c0b2774c61b6fb7c3531ffb16be9dafa209b765717b41"
V5 = "7b5422cf9201bb195b12e9b08ae2f7048b9fbb075951ab598e0e486cfba0dcbf"
WORDS = "alpha bravo charlie delta echo".split()
OBJECTIVES = [f"supplier insolvency {w} recurrence" for w in WORDS]
RANKED = [0.8, 0.8, 0.5, 0.5, 0.2]
A_OFFSETS = [0.10, 0.40, 0.80, 1.20, 1.50]  # seconds after NOW; crosses a second boundary after e3
B_OFFSETS = [0.70, 1.05, 1.35, 1.70, 2.05]  # same relative order, different boundaries
KEYS = [f"EPI-{n * 5}" for n in "abcde"]


def _rows(keys, offsets, ranks=None):
    rows = []
    for i, key in enumerate(keys):
        row = _episode_row(
            key,
            participation="observed",
            trust="external_untrusted_observation",
            objective=OBJECTIVES[i],
        )
        row["task_id"] = 100 + i
        row["rank"] = (ranks or [0.2] * 5)[i]
        row["observed_at"] = NOW + timedelta(seconds=offsets[i])
        row["payload_digest"] = er.episode_payload_digest(row)
        rows.append(row)
    return rows


def _pack(keys, offsets, base, ranks=None):
    rows = _rows(keys, offsets, ranks)
    er._positions_observed(rows)  # isolates the recency/sort rule: equal scores share one position
    items = [er.episode_item(row, _req(), NOW)[0] for row in rows]
    procedure = er.procedure_item(_proc_row(), _req(), NOW)[0]
    return er.compose([*items, procedure], _req(), {}, base_policy=base)


def _texts(pack):
    return [i["text"] for i in pack["low_trust_observations"]]


def _obj(index):
    return f"Precedent. Objective: {OBJECTIVES[index]}. Outcome: completed."


def test_policy_identities_are_exact_and_v5_adds_one_field():
    old = (er.E5_V1_POLICY, er.E5_V2_POLICY, er.E5_V3_POLICY, er.E5_V4_POLICY)
    assert [_sha256(p) for p in old] == [V1, V2, V3, V4]
    assert er.E5_V5_SCHEMA_VERSION == "176.e5.v5" and _sha256(er.E5_V5_POLICY) == V5
    assert er.SCHEMA_VERSION == "176.e5.v5" and er.POLICY is er.E5_V5_POLICY
    assert er.E5_V5_POLICY["observed_episode_ranking"] == {
        "scope": "low_trust_observations",
        "lexical_score_ties": "shared_competition_rank",
        "recency": "exact_observed_at_desc",
        "recency_tie": "semantic_digest_then_memory_key",
    }
    skip = {"version", "observed_episode_ranking"}
    assert {k: v for k, v in er.E5_V5_POLICY.items() if k not in skip} == {
        k: v for k, v in er.E5_V4_POLICY.items() if k != "version"
    }
    assert "observed_episode_ranking" not in er.E5_V4_POLICY


def test_shared_competition_rank_for_tied_lexical_scores():
    for keys in itertools.islice(itertools.permutations(KEYS), 0, 120, 7):
        rows = _rows(list(keys), A_OFFSETS, RANKED)
        er._positions_observed(rows)
        assert [r["lex_pos"] for r in rows] == [1, 1, 3, 3, 5]


def test_v4_positions_follow_the_physical_key_for_tied_scores():
    asc, desc = _rows(KEYS, A_OFFSETS, RANKED), _rows(list(reversed(KEYS)), A_OFFSETS, RANKED)
    er._positions(asc, "episode_key")
    er._positions(desc, "episode_key")
    assert [r["lex_pos"] for r in asc] == [1, 2, 3, 4, 5]
    assert [r["lex_pos"] for r in desc] == [2, 1, 4, 3, 5]  # historical RED: physical-key dependent


def test_tied_scores_get_equal_fusion_and_non_low_trust_keep_v4_positions():
    rows = _rows(KEYS, A_OFFSETS, RANKED)
    precedent = _episode_row("EPI-zzzzz", objective="supplier insolvency precedent recurrence")
    precedent["rank"] = 0.7
    er._positions_observed([*rows, precedent])
    fusions = [er.episode_item(r, _req(), NOW)[0]["signals"]["fusion_rank_score"] for r in rows]
    assert fusions[0] == fusions[1] and fusions[2] == fusions[3]
    assert fusions[0] > fusions[2] > fusions[4]
    assert precedent["lex_pos"] == 3  # unchanged v4 ordinal among all hits (0.8, 0.8, 0.7, ...)


def test_instant_is_exact_not_bucketed():
    assert er._instant_us(NOW + timedelta(microseconds=1)) - er._instant_us(NOW) == 1
    early, late = NOW + timedelta(seconds=0.4), NOW + timedelta(seconds=0.8)
    assert er._instant_us(early) != er._instant_us(late)
    assert er._epoch(early) == er._epoch(late)
    assert er._instant_us(None) == 0


def test_v4_second_boundaries_change_the_selection_but_v5_does_not():
    v4a = _texts(_pack(KEYS, A_OFFSETS, er.E5_V4_POLICY))
    v4b = _texts(_pack(KEYS, B_OFFSETS, er.E5_V4_POLICY))
    assert v4a != v4b  # historical RED: same relative order, different selection
    v5a = _texts(_pack(KEYS, A_OFFSETS, er.E5_V5_POLICY))
    v5b = _texts(_pack(KEYS, B_OFFSETS, er.E5_V5_POLICY))
    assert v5a == v5b == [_obj(4), _obj(3), _obj(2)]


def test_combined_selection_is_the_three_most_recent_and_key_independent():
    expected = [_obj(4), _obj(3), _obj(2)]
    for keys in itertools.islice(itertools.permutations(KEYS), 0, 120, 5):
        for offsets in (A_OFFSETS, B_OFFSETS):
            assert _texts(_pack(list(keys), offsets, er.E5_V5_POLICY)) == expected


def test_identical_instants_fall_to_the_semantic_digest_not_the_key():
    same = [0.5] * 5
    asc = _texts(_pack(KEYS, same, er.E5_V5_POLICY))
    desc = _texts(_pack(list(reversed(KEYS)), same, er.E5_V5_POLICY))
    mixed = _texts(_pack([KEYS[i] for i in (3, 0, 4, 2, 1)], same, er.E5_V5_POLICY))
    assert len(asc) == 3 and asc == desc == mixed


def test_fusion_still_precedes_exact_recency():
    pack = _pack(KEYS, A_OFFSETS, er.E5_V5_POLICY, ranks=[0.9, 0.2, 0.2, 0.2, 0.2])
    assert pack["low_trust_observations"][0]["text"] == _obj(0)


def test_v5_sort_key_only_changes_low_trust_items():
    precedent = er.episode_item(_episode_row("EPI-p"), _req(), NOW)[0]
    assert er._sort_key_v5(precedent) == er._sort_key_v4(precedent)
    low = er.episode_item(_rows(KEYS, A_OFFSETS)[0], _req(), NOW)[0]
    assert er._sort_key_v5(low) != er._sort_key_v4(low)
    assert "_recency_instant" not in er._public(low)


class _Cur:
    def fetchone(self):
        return {"excluded_revoked_episode": 0, "excluded_revoked_source": 0}

    def fetchall(self):
        return []


class _Conn:
    def __init__(self):
        self.sqls = []

    def execute(self, sql, params=None):
        self.sqls.append(sql)
        return _Cur()


def test_sql_prelimit_order_is_stable_semantics_before_key_in_v5_only():
    v5, v4 = _Conn(), _Conn()
    er.ExperienceRetrievalService._episodes(v5, {}, {}, exact_order=True)
    er.ExperienceRetrievalService._episodes(v4, {}, {}, exact_order=False)
    order5 = v5.sqls[-1].split("ORDER BY", 1)[1]
    at, sem, key = (order5.index(s) for s in ("e.observed_at DESC", "objective", "e.episode_key"))
    assert at < sem < key
    assert 'COLLATE "C"' in order5 and "e.project_id" not in order5 and "digest" not in order5
    order4 = v4.sqls[-1].split("ORDER BY", 1)[1].split("LIMIT")[0]
    assert order4.split() == ["rank", "DESC,e.observed_at", "DESC,e.episode_key"]


def test_frozen_v4_path_exists_and_no_public_policy_selector():
    assert hasattr(er.ExperienceRetrievalService, "_retrieve_frozen_v4")
    params = inspect.signature(er.ExperienceRetrievalService.retrieve).parameters
    assert list(params) == ["self", "request"]
