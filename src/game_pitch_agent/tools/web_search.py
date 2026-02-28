"""DuckDuckGo 検索ツール - ADKカスタムツール"""

import logging

logger = logging.getLogger(__name__)


def duckduckgo_search(query: str, max_results: int = 5) -> str:
    """
    DuckDuckGo を使ってウェブ検索を行い、結果を文字列で返す。

    Args:
        query: 検索クエリ
        max_results: 最大結果数（デフォルト5件）

    Returns:
        検索結果を整形した文字列
    """
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=max_results))

        if not search_results:
            return f"検索結果が見つかりませんでした: {query}"

        for i, result in enumerate(search_results, 1):
            title = result.get("title", "タイトルなし")
            body = result.get("body", "内容なし")
            href = result.get("href", "")
            results.append(f"{i}. **{title}**\n   {body}\n   URL: {href}")

        return "\n\n".join(results)

    except ImportError:
        logger.error("duckduckgo-search ライブラリがインストールされていません")
        return "エラー: duckduckgo-search ライブラリが見つかりません"
    except Exception as e:
        logger.error(f"DuckDuckGo 検索エラー: {e}")
        return f"検索エラー: {str(e)}"
