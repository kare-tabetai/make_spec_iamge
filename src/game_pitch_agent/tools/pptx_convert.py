"""PPTX -> PDF / PNG 変換モジュール (LibreOffice + pdftoppm)"""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

LIBREOFFICE_TIMEOUT = 60  # seconds
PDFTOPPM_TIMEOUT = 30
PDFTOPPM_DPI = 200


def convert_pptx_to_pdf(pptx_path: str, output_dir: str | None = None) -> str | None:
    """PPTX -> PDF (LibreOffice headless)

    Args:
        pptx_path: 変換元のPPTXファイルパス
        output_dir: PDF出力先ディレクトリ（Noneの場合はPPTXと同じディレクトリ）

    Returns:
        生成されたPDFのパス文字列、または失敗時は None
    """
    if not shutil.which("libreoffice"):
        logger.warning("libreoffice が見つかりません。PDF変換をスキップします")
        return None

    pptx = Path(pptx_path)
    if not pptx.exists():
        logger.warning(f"PPTXファイルが見つかりません: {pptx_path}")
        return None

    outdir = Path(output_dir) if output_dir else pptx.parent

    # LibreOffice headless は非ASCIIパスを処理できないため、
    # 一時ディレクトリ（ASCII-onlyパス）経由で変換する
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_pptx = Path(tmpdir) / "input.pptx"
            shutil.copy2(pptx, tmp_pptx)

            result = subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", tmpdir,
                    str(tmp_pptx),
                ],
                capture_output=True,
                text=True,
                timeout=LIBREOFFICE_TIMEOUT,
            )

            if result.returncode != 0:
                logger.warning(f"LibreOffice変換失敗 (exit {result.returncode}): {result.stderr}")
                return None

            # returncode == 0 でも stderr にエラーが含まれる場合がある
            if result.stderr and "Error:" in result.stderr:
                logger.warning(f"LibreOffice stderr にエラー検出: {result.stderr}")

            tmp_pdf = Path(tmpdir) / "input.pdf"
            if not tmp_pdf.exists():
                logger.warning(f"PDF変換後のファイルが見つかりません (tmpdir): {tmp_pdf}")
                return None

            final_pdf = outdir / f"{pptx.stem}.pdf"
            shutil.move(str(tmp_pdf), str(final_pdf))

    except subprocess.TimeoutExpired:
        logger.warning(f"LibreOffice変換タイムアウト ({LIBREOFFICE_TIMEOUT}秒)")
        return None
    except Exception as e:
        logger.warning(f"LibreOffice変換エラー: {e}")
        return None

    if final_pdf.exists():
        logger.info(f"PDF生成完了: {final_pdf}")
        return str(final_pdf)

    logger.warning(f"PDF変換後のファイルが見つかりません: {final_pdf}")
    return None


def convert_pdf_to_png(pdf_path: str, output_path: str | None = None, dpi: int = PDFTOPPM_DPI) -> str | None:
    """PDF -> PNG (pdftoppm -singlefile)

    Args:
        pdf_path: 変換元のPDFファイルパス
        output_path: PNG出力パス（拡張子なし or .png付き、Noneの場合はPDFと同名）
        dpi: 解像度（デフォルト200）

    Returns:
        生成されたPNGのパス文字列、または失敗時は None
    """
    if not shutil.which("pdftoppm"):
        logger.warning("pdftoppm が見つかりません。PNG変換をスキップします")
        return None

    pdf = Path(pdf_path)
    if not pdf.exists():
        logger.warning(f"PDFファイルが見つかりません: {pdf_path}")
        return None

    if output_path:
        out_prefix = str(Path(output_path).with_suffix(""))
    else:
        out_prefix = str(pdf.with_suffix(""))

    try:
        result = subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-r", str(dpi),
                "-singlefile",
                str(pdf),
                out_prefix,
            ],
            capture_output=True,
            text=True,
            timeout=PDFTOPPM_TIMEOUT,
        )
        if result.returncode != 0:
            logger.warning(f"pdftoppm変換失敗 (exit {result.returncode}): {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        logger.warning(f"pdftoppm変換タイムアウト ({PDFTOPPM_TIMEOUT}秒)")
        return None
    except Exception as e:
        logger.warning(f"pdftoppm変換エラー: {e}")
        return None

    png_path = Path(f"{out_prefix}.png")
    if png_path.exists():
        logger.info(f"PNG生成完了: {png_path}")
        return str(png_path)

    logger.warning(f"PNG変換後のファイルが見つかりません: {png_path}")
    return None


def convert_pptx(pptx_path: str) -> dict[str, str | None]:
    """PPTX -> PDF + PNG をまとめて実行

    Args:
        pptx_path: 変換元のPPTXファイルパス

    Returns:
        {"pdf_path": str | None, "png_path": str | None}
    """
    pdf_path = convert_pptx_to_pdf(pptx_path)

    png_path = None
    if pdf_path:
        png_path = convert_pdf_to_png(pdf_path)

    return {"pdf_path": pdf_path, "png_path": png_path}
