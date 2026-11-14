"""PKM (Personal Knowledge Management) export service for Obsidian, Anki, and BibTeX."""

import html
import re
from typing import Any

VAL_UNKNOWN_AUTHOR = "Bilinmeyen Yazar"
VAL_GENERAL_CATEGORY = "Genel"
TAG_BASE_OBSIDIAN = "dijital-kutuphane"
TAG_BASE_ANKI = "dijital_kutuphane"


def _clean_yaml_value(val: Any) -> str:
    """Escape and format value for safe YAML frontmatter string."""
    if val is None:
        return ""
    text = str(val).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return text.strip()


def _slugify(text: str) -> str:
    """Produce a safe ASCII/alphanumeric slug for tags and citation keys."""
    if not text:
        return ""
    # Lowercase and replace Turkish characters for clean keys
    mapping = {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "Ç": "c",
        "Ğ": "g",
        "İ": "i",
        "Ö": "o",
        "Ş": "s",
        "Ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
        "Â": "a",
        "Î": "i",
        "Û": "u",
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
    }
    cleaned = text
    for tr, en in mapping.items():
        cleaned = cleaned.replace(tr, en)
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]+", "_", cleaned)
    return cleaned.strip("_").lower()


def _escape_bibtex(text: str) -> str:
    """Escape special LaTeX/BibTeX characters."""
    if not text:
        return ""
    # Map special chars to escaped counterparts
    chars = {
        "\\": "\\textbackslash{}",
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
    }
    res = []
    for char in text:
        res.append(chars.get(char, char))
    return "".join(res)


def generate_citation_key(author: str, title: str, year: str = "", file_hash: str = "") -> str:
    """Generate a clean citation key for BibTeX (e.g. 'turing1950computing')."""
    author_parts = author.split(",")[0].split() if author else []
    author_name = author_parts[-1] if author_parts else "anon"
    author_slug = _slugify(author_name)
    title_words = [w for w in re.split(r"\W+", title or "") if w]
    first_word = _slugify(title_words[0]) if title_words else "book"

    # Try to extract 4-digit year from year or fallback to hash prefix
    year_match = re.search(r"\b(19\d\d|20\d\d)\b", str(year or ""))
    if year_match:
        year_str = year_match.group(1)
    elif file_hash:
        year_str = file_hash[:4]
    else:
        year_str = "nd"

    return f"{author_slug}_{year_str}_{first_word}"


class PKMExporter:
    """Service to export books, highlights and notes to PKM systems."""

    @staticmethod
    def _build_obsidian_tags(category: str, sub_cat: str, keywords_str: str) -> list[str]:
        """Compile normalized tag slugs for Obsidian metadata."""
        tags = [TAG_BASE_OBSIDIAN]
        if category and category != VAL_GENERAL_CATEGORY:
            tags.append(_slugify(category))
        if sub_cat:
            tags.append(_slugify(sub_cat))
        if keywords_str:
            for kw in re.split(r"[,;]+", keywords_str):
                cleaned_kw = _slugify(kw.strip())
                if cleaned_kw and cleaned_kw not in tags:
                    tags.append(cleaned_kw)
        return tags

    @staticmethod
    def _format_obsidian_annotations(annotations: list[dict]) -> list[str]:
        """Format highlight quotes and personal notes into Markdown blockquotes."""
        if not annotations:
            return ["_Bu kitapta henüz alınmış bir not veya alıntı bulunmamaktadır._\n"]

        lines = []
        sorted_anns = sorted(
            annotations,
            key=lambda x: (
                x.get("sayfa_no", 1),
                str(x.get("olusturma_tarihi", "")),
            ),
        )
        for ann in sorted_anns:
            page_no = ann.get("sayfa_no", 1)
            secilen = (ann.get("secilen_metin") or "").strip()
            not_metni = (ann.get("not_metni") or "").strip()
            tarih = (ann.get("olusturma_tarihi") or "").strip()
            renk = (ann.get("renk_sinif") or "yellow").strip()

            lines.append(f"### Sayfa {page_no}")
            if secilen:
                quote_block = "\n> ".join(secilen.splitlines())
                lines.append(f"> {quote_block}")
                lines.append("")
            if not_metni:
                lines.append(f"- **Kullanıcı Notu:** {not_metni}")
            meta_parts = []
            if tarih:
                meta_parts.append(f"Tarih: {tarih}")
            if renk:
                meta_parts.append(f"Renk: {renk}")
            if meta_parts:
                lines.append(f"- *{' | '.join(meta_parts)}*")
            lines.append("")
        return lines

    @classmethod
    def export_obsidian(cls, book: dict, annotations: list[dict] | None = None) -> str:
        """Export book and notes as an Obsidian Markdown note with YAML frontmatter and [[Wikilinks]]."""
        annotations = annotations or []
        title = (book.get("kitap_adi") or "İsimsiz Kitap").strip()
        author = (book.get("yazar") or VAL_UNKNOWN_AUTHOR).strip()
        category = (book.get("kategori") or VAL_GENERAL_CATEGORY).strip()
        sub_cat = (book.get("alt_kategori") or "").strip()
        summary = (book.get("ozet") or "").strip()
        keywords_str = (book.get("anahtar_kelimeler") or "").strip()
        file_hash = (book.get("dosya_hash") or "").strip()
        file_name = (book.get("dosya_adi") or "").strip()
        added_date = (book.get("ekleme_tarihi") or "").strip()
        reading_page = book.get("okunulan_sayfa") or 1

        tags = cls._build_obsidian_tags(category, sub_cat, keywords_str)

        lines = [
            "---",
            f'title: "{_clean_yaml_value(title)}"',
            f'author: "{_clean_yaml_value(author)}"',
            f'category: "{_clean_yaml_value(category)}"',
        ]
        if sub_cat:
            lines.append(f'sub_category: "{_clean_yaml_value(sub_cat)}"')
        lines.extend(
            [
                f'file_name: "{_clean_yaml_value(file_name)}"',
                f'file_hash: "{_clean_yaml_value(file_hash)}"',
                f'added_date: "{_clean_yaml_value(added_date)}"',
                f"reading_progress_page: {reading_page}",
                f"total_annotations: {len(annotations)}",
                "tags:",
            ]
        )
        for tag in tags:
            lines.append(f"  - {tag}")
        lines.extend(
            [
                "aliases:",
                f'  - "{_clean_yaml_value(title)}"',
                "---",
                "",
                f"# {title}",
                "",
                "> [!INFO] Kitap Bilgileri",
                f"> - **Yazar:** [[{author}]]",
                f"> - **Kategori:** [[{category}]]" + (f" / [[{sub_cat}]]" if sub_cat else ""),
                f"> - **Eklenme Tarihi:** {added_date or 'Belirtilmedi'}",
                f"> - **Okuma İlerlemesi:** Sayfa {reading_page}",
                "",
                "## 📖 Kitap Özeti",
                "",
                summary if summary else "_Bu kitap için henüz bir özet bulunmuyor._",
                "",
                "## ✍️ Alıntılar ve Notlar",
                "",
            ]
        )
        lines.extend(cls._format_obsidian_annotations(annotations))
        return "\n".join(lines).strip() + "\n"

    @staticmethod
    def _build_anki_card_for_annotation(
        ann: dict, title: str, author: str, category: str, tags_str: str
    ) -> str | None:
        """Create front/back TSV card content for a single user annotation."""

        def sanitize_field(text: str) -> str:
            if not text:
                return ""
            cleaned = html.escape(str(text), quote=False).replace("\t", "    ")
            return cleaned.replace("\r\n", "<br>").replace("\n", "<br>").strip()

        page_no = ann.get("sayfa_no", 1)
        secilen = sanitize_field(ann.get("secilen_metin") or "")
        not_metni = sanitize_field(ann.get("not_metni") or "")

        if not secilen and not not_metni:
            return None

        if secilen and not_metni:
            front = (
                f"<b>{title}</b> (Sayfa {page_no})<br><br>"
                f'<i>"{secilen}"</i><br><br>'
                f"<b>Soru / Not:</b> Bu alıntının temel mesajı ve bağlamı nedir?"
            )
            back = (
                f"<b>Açıklama:</b><br>{not_metni}<br><br>"
                f"<small>Yazar: {author} | Kategori: {category}</small>"
            )
        elif secilen:
            front = (
                f"<b>{title}</b> (Sayfa {page_no})<br><br>"
                f"Aşağıdaki alıntı neyi ifade etmektedir?<br><br>"
                f'<i>"{secilen}"</i>'
            )
            back = (
                f"<b>Kaynak:</b> {title} - Sayfa {page_no}<br>"
                f"<small>Yazar: {author} | Kategori: {category}</small>"
            )
        else:
            front = (
                f"<b>{title}</b> (Sayfa {page_no}) - Not<br><br><b>Kavram / Soru:</b> {not_metni}"
            )
            back = (
                f"<b>Kaynak:</b> {title} (Sayfa {page_no})<br>"
                f"<small>Yazar: {author} | Kategori: {category}</small>"
            )
        return f"{front}\t{back}\t{tags_str}"

    @classmethod
    def export_anki(cls, book: dict, annotations: list[dict] | None = None) -> str:
        """Export book notes as Anki flashcards in tab-separated values (TSV) format."""
        annotations = annotations or []

        def _clean_meta(text: Any) -> str:
            if not text:
                return ""
            val = re.sub(r"[\t\r\n]+", " ", str(text)).strip()
            return html.escape(val, quote=False)

        title = _clean_meta(book.get("kitap_adi") or "Kitap")
        author = _clean_meta(book.get("yazar") or VAL_UNKNOWN_AUTHOR)
        category = _clean_meta(book.get("kategori") or VAL_GENERAL_CATEGORY)
        summary = (book.get("ozet") or "").strip()
        keywords_str = (book.get("anahtar_kelimeler") or "").strip()

        base_tags = [TAG_BASE_ANKI, _slugify(category)]
        if author and author != VAL_UNKNOWN_AUTHOR:
            base_tags.append(_slugify(author))
        tags_str = " ".join(t for t in base_tags if t)

        cards: list[str] = []
        if annotations:
            for ann in annotations:
                card = cls._build_anki_card_for_annotation(ann, title, author, category, tags_str)
                if card:
                    cards.append(card)
        else:
            clean_sum = html.escape(summary or "Özet bilgisi girilmemiştir.", quote=False).replace(
                "\n", "<br>"
            )
            clean_kw = html.escape(keywords_str or category, quote=False)
            front = f"<b>{title}</b> - {author}<br><br>Bu eserin temel konusu, ele aldığı problem ve anahtar kavramlar nelerdir?"
            back = f"<b>Özet:</b><br>{clean_sum}<br><br><b>Anahtar Kelimeler:</b> {clean_kw}<br><small>Kategori: {category}</small>"
            cards.append(f"{front}\t{back}\t{tags_str}")

        return "\n".join(cards) + "\n"

    @staticmethod
    def export_bibtex(book: dict) -> str:
        """Export book citation as a standard BibTeX entry."""
        title = (book.get("kitap_adi") or "Untitled Document").strip()
        author = (book.get("yazar") or "").strip()
        category = (book.get("kategori") or "").strip()
        summary = (book.get("ozet") or "").strip()
        keywords = (book.get("anahtar_kelimeler") or "").strip()
        file_hash = (book.get("dosya_hash") or "").strip()
        added_date = (book.get("ekleme_tarihi") or "").strip()

        # Extract year if possible
        year_match = re.search(r"\b(19\d\d|20\d\d)\b", added_date)
        year = year_match.group(1) if year_match else "2026"

        cite_key = generate_citation_key(author, title, year, file_hash)

        # Decide entry type: @book if author and title present, else @misc
        entry_type = "book" if author else "misc"

        fields = [
            f"  title = {{{_escape_bibtex(title)}}}",
        ]
        if author:
            fields.append(f"  author = {{{_escape_bibtex(author)}}}")
        fields.append(f"  year = {{{year}}}")
        if category:
            fields.append(
                f"  keywords = {{{_escape_bibtex(category + (', ' + keywords if keywords else ''))}}}"
            )
        if summary:
            # Shorten summary for BibTeX note if too long
            short_note = (summary[:250] + "...") if len(summary) > 250 else summary
            fields.append(f"  note = {{{_escape_bibtex(short_note)}}}")
        fields.append("  publisher = {Dijital Kütüphane}")

        body = ",\n".join(fields)
        return f"@{entry_type}{{{cite_key},\n{body}\n}}\n"
