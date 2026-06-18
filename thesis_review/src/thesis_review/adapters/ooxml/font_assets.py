"""保留输入 docx 的字体相关 OOXML 资产。"""
from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

_FONT_ASSET_FILES = {
    "word/theme/theme1.xml",
    "word/fontTable.xml",
    "word/_rels/fontTable.xml.rels",
}


def _is_font_asset(name: str) -> bool:
    return name in _FONT_ASSET_FILES or name.startswith("word/fonts/")


def restore_font_assets(source_docx: str | Path, target_docx: str | Path) -> None:
    """把 source_docx 中的字体/主题资产原样恢复到 target_docx。

    LibreOffice/UNO 另存 docx 时会重写 theme/fontTable，导致中文主题字体
    映射丢失。标注仍由 UNO 写入，但最终包里的字体资产以输入文件为准。
    """
    source_path = Path(source_docx)
    target_path = Path(target_docx)

    with ZipFile(source_path) as source_zip:
        source_assets = {
            info.filename: (info, source_zip.read(info.filename))
            for info in source_zip.infolist()
            if _is_font_asset(info.filename)
        }

    with ZipFile(target_path) as target_zip:
        target_infos = target_zip.infolist()
        target_payloads = {
            info.filename: target_zip.read(info.filename)
            for info in target_infos
        }

    with NamedTemporaryFile(
        dir=target_path.parent,
        suffix=".docx",
        delete=False,
    ) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with ZipFile(tmp_path, "w", ZIP_DEFLATED) as out_zip:
            written: set[str] = set()
            for info in target_infos:
                name = info.filename
                if name in source_assets:
                    source_info, data = source_assets[name]
                    out_zip.writestr(source_info, data)
                elif not _is_font_asset(name):
                    out_zip.writestr(info, target_payloads[name])
                written.add(name)

            for name, (source_info, data) in source_assets.items():
                if name not in written:
                    out_zip.writestr(source_info, data)

        tmp_path.replace(target_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
