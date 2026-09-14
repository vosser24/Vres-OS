"""Verify the synthetic inputs independently of the builder and expected-result file."""
from collections import defaultdict
import json
from pathlib import Path
import pytest
from openpyxl import load_workbook

ROOT = Path(__file__).parent / 'fixtures/live'

@pytest.mark.parametrize('day', [1, 2])
def test_live_fixture_first_sheet_results_and_traps(day):
    expected = json.loads((ROOT/'expected.json').read_text())[f'day{day}_expected']
    totals = defaultdict(int)
    n = 0
    for side in ('A', 'B'):
        w = load_workbook(ROOT/f'day{day}_{side}.xlsx', read_only=True, data_only=True)
        try:
            assert w.worksheets[1]['A2'].value == '999999'
            for sku, description, sales, units in w.worksheets[0].iter_rows(min_row=2, values_only=True):
                assert isinstance(sku, str) and len(sku) == 6
                assert sku != '999999'
                totals[sku] += sales
                n += 1
        finally:
            w.close()
    assert n == 26 and len(totals) == 12
    assert sum(totals.values()) == expected['total_net_sales_all_products']
    top = [{'SKU': k, 'Net Sales': v} for k, v in sorted(totals.items(), key=lambda x:(-x[1],x[0]))[:10]]
    assert top == expected['top10']
    assert totals['000003'] == 3*130*day + 5 + 25*day
    assert totals['000007'] == 7*130*day + 5 - 20*day
