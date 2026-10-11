"""文档加载与文本切分。"""
import io

import pytest

from app.rag.loader import load_document_bytes
from app.rag.splitter import get_splitter


def test_load_txt():
    docs = load_document_bytes("a.txt", "你好世界".encode("utf-8"))
    assert len(docs) == 1
    assert "你好世界" in docs[0].page_content


def test_load_md():
    docs = load_document_bytes("a.md", "# 标题\n内容".encode("utf-8"))
    assert docs[0].page_content == "# 标题\n内容"


def test_load_csv():
    data = "名称,价格\n手机,4299\n耳机,399\n".encode("utf-8-sig")
    docs = load_document_bytes("a.csv", data)
    assert "手机 4299" in docs[0].page_content


def test_load_xlsx():
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["名称", "价格"])
    ws.append(["手机", 4299])
    buf = io.BytesIO()
    wb.save(buf)
    docs = load_document_bytes("a.xlsx", buf.getvalue())
    assert "手机 4299" in docs[0].page_content


def test_unsupported_extension_raises():
    with pytest.raises(ValueError):
        load_document_bytes("a.exe", b"xx")


def test_split_long_text_multiple_chunks():
    splitter = get_splitter()
    text = "这是一段话。它会被切分。" * 100
    chunks = splitter.split_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 600 for c in chunks)


def test_split_short_text_single_chunk():
    splitter = get_splitter()
    assert len(splitter.split_text("短文本")) == 1
