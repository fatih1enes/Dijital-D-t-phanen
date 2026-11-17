"""Smart Dynamic Collections DQL Rule Compiler."""

from typing import Any


class SmartCollectionCompiler:
    """Compiles JSON-based dynamic collection rules into safe parameterized SQL."""

    @staticmethod
    def compile_rules(rule_dict: dict[str, Any]) -> tuple[list[str], list[Any]]:
        """Compile a dictionary of rule constraints into WHERE clause fragments and params."""
        clauses: list[str] = []
        params: list[Any] = []

        if not rule_dict or not isinstance(rule_dict, dict):
            return clauses, params

        # Category constraint
        category = rule_dict.get("category")
        if category and category != "all":
            clauses.append("kategori = ?")
            params.append(category)

        # Favorite constraint
        fav = rule_dict.get("favorite_only")
        if fav is True:
            clauses.append("is_favorite = 1")

        # Minimum / Maximum pages (okunulan_sayfa)
        min_page = rule_dict.get("min_page")
        if min_page is not None and isinstance(min_page, (int, float)):
            clauses.append("okunulan_sayfa >= ?")
            params.append(int(min_page))

        max_page = rule_dict.get("max_page")
        if max_page is not None and isinstance(max_page, (int, float)):
            clauses.append("okunulan_sayfa <= ?")
            params.append(int(max_page))

        # Recent addition (e.g. added within last N days)
        added_days = rule_dict.get("added_within_days")
        if added_days is not None and isinstance(added_days, int) and added_days > 0:
            clauses.append("ekleme_tarihi >= datetime('now', ? || ' days')")
            params.append(f"-{added_days}")

        # Has user notes/annotations constraint
        has_notes = rule_dict.get("has_notes")
        if has_notes is True:
            clauses.append("dosya_hash IN (SELECT DISTINCT dosya_hash FROM kitap_notlari)")

        # Keyword / search constraint (Turkish-aware when TR_LOWER is registered, else standard LIKE)
        kw = rule_dict.get("keyword")
        if kw and str(kw).strip():
            from app.utils import tr_lower

            term = f"%{tr_lower(str(kw).strip())}%"
            clauses.append(
                "(TR_LOWER(kitap_adi) LIKE ? OR TR_LOWER(yazar) LIKE ? OR TR_LOWER(anahtar_kelimeler) LIKE ? OR TR_LOWER(ozet) LIKE ?)"
            )
            params.extend([term, term, term, term])

        return clauses, params


smart_collection_compiler = SmartCollectionCompiler()
