import pytest
from app.rag import extract_text
from app.sales import monthly_summary, seed_demo_db


def test_text_extraction():
    name, content = extract_text('C:\\docs\\rules.txt', b'Payment must be checked before sale.')
    assert name == 'rules.txt'
    assert 'Payment' in content


def test_bad_file():
    with pytest.raises(ValueError):
        extract_text('hack.exe', b'print("hello world")')


def test_utf8():
    _, content = extract_text('prosedur.md', 'Her cuma stok sayımı yapılmaktadır.'.encode('utf8'))
    assert 'stok' in content


def test_sales_summary(tmp_path):
    path = seed_demo_db(tmp_path / 'sales.sqlite')
    result = monthly_summary('2026-11', path)
    assert result['total_revenue_try'] == 336000
    assert len(result['products']) == 3
    assert monthly_summary('2026-09', path)['total_revenue_try'] == 0
