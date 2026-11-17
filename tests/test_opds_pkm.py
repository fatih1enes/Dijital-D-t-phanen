"""Tests for Phase 1: PKM Exporter (Obsidian, Anki, BibTeX) and OPDS 1.2 Catalog."""

import base64
import os

import pytest

from app.services.pkm_exporter import PKMExporter, _escape_bibtex, _slugify, generate_citation_key


class TestPKMExporterUnit:
    """Unit tests for PKM export format transformations."""

    def test_slugify(self):
        assert _slugify("Yapay Zekâ ve Veri Bilimi!") == "yapay_zeka_ve_veri_bilimi"
        assert _slugify("İstanbul Çiçekçileri") == "istanbul_cicekcileri"
        assert _slugify("") == ""

    def test_escape_bibtex(self):
        assert _escape_bibtex("A & B: 50% $100 {Test}") == "A \\& B: 50\\% \\$100 \\{Test\\}"
        assert _escape_bibtex("") == ""

    def test_generate_citation_key(self):
        key = generate_citation_key(
            "Alan Turing", "Computing Machinery and Intelligence", "1950", "a1b2c3d4"
        )
        assert key == "turing_1950_computing"

        fallback_key = generate_citation_key("", "", "", "abcdef123456")
        assert "abcdef12"[:4] in fallback_key

    def test_export_obsidian_structure(self):
        book = {
            "kitap_adi": "Dune Gezegeni",
            "yazar": "Frank Herbert",
            "kategori": "Bilim Kurgu",
            "alt_kategori": "Uzay Operası",
            "ozet": "Arrakis çöl gezegeninde geçen bir destan.",
            "anahtar_kelimeler": "baharat, solucan, melanj",
            "dosya_hash": "dune_hash_123",
            "dosya_adi": "dune.pdf",
            "ekleme_tarihi": "2026-11-07 10:00:00",
            "okunulan_sayfa": 42,
        }
        annotations = [
            {
                "id": "ann1",
                "sayfa_no": 15,
                "secilen_metin": "Korku aklın katilidir.",
                "not_metni": "Bene Gesserit öğretisinin temel mantrasıdır.",
                "olusturma_tarihi": "2026-11-07 10:30:00",
                "renk_sinif": "yellow",
            }
        ]

        md = PKMExporter.export_obsidian(book, annotations)
        assert "---" in md
        assert 'title: "Dune Gezegeni"' in md
        assert 'author: "Frank Herbert"' in md
        assert "[[Frank Herbert]]" in md
        assert "[[Bilim Kurgu]]" in md
        assert "[[Uzay Operası]]" in md
        assert "Sayfa 15" in md
        assert "Korku aklın katilidir." in md
        assert "Bene Gesserit öğretisinin temel mantrasıdır." in md

    def test_export_obsidian_empty_annotations(self):
        book = {
            "kitap_adi": "Boş Notlu Kitap",
            "yazar": "Yazar",
            "dosya_hash": "bos_hash",
        }
        md = PKMExporter.export_obsidian(book, [])
        assert "# Boş Notlu Kitap" in md
        assert "henüz alınmış bir not veya alıntı bulunmamaktadır" in md

    def test_export_anki_format(self):
        book = {
            "kitap_adi": "Temiz Kod",
            "yazar": "Robert C. Martin",
            "kategori": "Yazılım",
            "ozet": "Sürdürülebilir kod geliştirme pratikleri.",
            "anahtar_kelimeler": "refactoring, solid",
        }
        annotations = [
            {
                "sayfa_no": 22,
                "secilen_metin": "Kod bir kere yazılır, on kere okunur.",
                "not_metni": "Okunabilirliğe yatırım yapın.",
            }
        ]

        tsv = PKMExporter.export_anki(book, annotations)
        lines = tsv.strip().split("\n")
        assert len(lines) == 1
        cols = lines[0].split("\t")
        assert len(cols) == 3
        # Front has book title, page and quote
        assert "Temiz Kod" in cols[0]
        assert "Sayfa 22" in cols[0]
        # Back has user note
        assert "Okunabilirliğe yatırım yapın." in cols[1]
        # Tags
        assert "dijital_kutuphane" in cols[2]

    def test_export_bibtex_format(self):
        book = {
            "kitap_adi": "Gödel, Escher, Bach",
            "yazar": "Douglas Hofstadter",
            "kategori": "Felsefe",
            "ozet": "Bir Ebedi Gökçe Belik",
            "dosya_hash": "geb_hash_123",
            "ekleme_tarihi": "1979-01-01",
        }
        bib = PKMExporter.export_bibtex(book)
        assert "@book{" in bib
        assert "hofstadter_1979_godel" in bib
        assert ('title = {G\\"odel, Escher, Bach}' in bib) or (
            "title = {Gödel, Escher, Bach}" in bib
        )
        assert "author = {Douglas Hofstadter}" in bib
        assert "publisher = {Dijital Kütüphane}" in bib


class TestExportAndOPDSAPI:
    """Integration tests for Export and OPDS endpoints."""

    @pytest.fixture(autouse=True)
    def setup_book(self, tmp_path):
        """Prepare sample library book."""
        from app.constants import LIBRARY_ROOT

        os.makedirs(LIBRARY_ROOT, exist_ok=True)
        pdf_path = os.path.join(LIBRARY_ROOT, "test_pkm_opds.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 sample content for test")
        self.test_hash = "a" * 64
        self.pdf_path = pdf_path

    @pytest.mark.asyncio
    async def test_pkm_export_endpoints(self, temp_db, async_client):
        """Test /api/books/{hash}/export/{format} endpoints."""
        await temp_db.add_book(
            {
                "dosya_hash": self.test_hash,
                "dosya_yolu": self.pdf_path,
                "dosya_adi": "test_pkm_opds.pdf",
                "kitap_adi": "PKM Test Kitabı",
                "yazar": "Uzman Yazar",
                "kategori": "Felsefe",
                "alt_kategori": "Mantık",
                "ozet": "Felsefi çıkarımlar ve mantık yürütme.",
                "anahtar_kelimeler": "mantik, epistemoloji",
                "has_cover": False,
            }
        )
        await temp_db.save_book_annotation(
            {
                "id": "ann_test_1",
                "dosya_hash": self.test_hash,
                "sayfa_no": 5,
                "secilen_metin": "Düşünüyorum, öyleyse varım.",
                "not_metni": "Descartes cogito ilkesi",
                "renk_hex": "#fef08a",
                "renk_sinif": "yellow",
                "koordinatlar": "[]",
            }
        )

        # 1. Obsidian Export
        res_obs = await async_client.get(f"/api/books/{self.test_hash}/export/obsidian")
        assert res_obs.status_code == 200
        assert "text/markdown" in res_obs.headers["content-type"]
        assert "Düşünüyorum, öyleyse varım." in res_obs.text
        assert ("[[Descartes cogito ilkesi]]" in res_obs.text) or (
            "Descartes cogito ilkesi" in res_obs.text
        )

        # 2. Anki Export
        res_anki = await async_client.get(f"/api/books/{self.test_hash}/export/anki")
        assert res_anki.status_code == 200
        assert "text/tab-separated-values" in res_anki.headers["content-type"]
        assert "\t" in res_anki.text

        # 3. BibTeX Export
        res_bib = await async_client.get(f"/api/books/{self.test_hash}/export/bibtex")
        assert res_bib.status_code == 200
        assert "application/x-bibtex" in res_bib.headers["content-type"]
        assert "@book{" in res_bib.text

        # 4. Invalid Format
        res_invalid = await async_client.get(f"/api/books/{self.test_hash}/export/invalid_fmt")
        assert res_invalid.status_code == 400

        # 5. Non-existent Book
        res_404 = await async_client.get(f"/api/books/{'0' * 64}/export/obsidian")
        assert res_404.status_code == 404

    @pytest.mark.asyncio
    async def test_opds_root_and_feeds(self, temp_db, async_client):
        """Test OPDS 1.2 root navigation and acquisition feeds."""
        await temp_db.add_book(
            {
                "dosya_hash": self.test_hash,
                "dosya_yolu": self.pdf_path,
                "dosya_adi": "test_pkm_opds.pdf",
                "kitap_adi": "OPDS Test Eseri",
                "yazar": "Test Yazarı",
                "kategori": "Felsefe",
                "ozet": "Felsefi araştırmalar bütünü.",
                "has_cover": False,
            }
        )

        # 1. Root Navigation Feed
        res_root = await async_client.get("/opds")
        assert res_root.status_code == 200
        assert "profile=opds-catalog;kind=navigation" in res_root.headers["content-type"]
        assert "urn:dijital-kutuphane:opds:root" in res_root.text
        assert "/opds/recent.xml" in res_root.text
        assert "/opds/all.xml" in res_root.text
        assert "/opds/opensearch.xml" in res_root.text

        # 2. Recent Acquisition Feed
        res_recent = await async_client.get("/opds/recent.xml")
        assert res_recent.status_code == 200
        assert "profile=opds-catalog;kind=acquisition" in res_recent.headers["content-type"]
        assert "OPDS Test Eseri" in res_recent.text
        assert f"/opds/download/{self.test_hash}" in res_recent.text

        # 3. All Books Feed with Pagination
        res_all = await async_client.get("/opds/all.xml?page=1&limit=10")
        assert res_all.status_code == 200
        assert "OPDS Test Eseri" in res_all.text

        # 4. OpenSearch Document
        res_os = await async_client.get("/opds/opensearch.xml")
        assert res_os.status_code == 200
        assert "opensearchdescription+xml" in res_os.headers["content-type"]
        assert "/opds/search.xml?q={searchTerms}" in res_os.text

        # 5. Search Feed
        res_search = await async_client.get("/opds/search.xml?q=Felsefe")
        assert res_search.status_code == 200
        assert "OPDS Test Eseri" in res_search.text

        # 6. Categories Feed
        res_cats = await async_client.get("/opds/categories.xml")
        assert res_cats.status_code == 200
        assert "Felsefe" in res_cats.text

        # 7. Category Specific Feed
        res_cat_books = await async_client.get("/opds/category/Felsefe.xml")
        assert res_cat_books.status_code == 200
        assert "OPDS Test Eseri" in res_cat_books.text

        # 8. Book Download Stream
        res_dl = await async_client.get(f"/opds/download/{self.test_hash}")
        assert res_dl.status_code == 200
        assert res_dl.headers["content-type"] == "application/pdf"
        assert res_dl.content == b"%PDF-1.4 sample content for test"

    @pytest.mark.asyncio
    async def test_opds_auth_protection(self, temp_db, async_client, monkeypatch):
        """Verify OPDS correctly enforces HTTP Basic Auth when remote access is protected."""
        import app.auth as auth_mod

        # Set an access password
        monkeypatch.setattr(auth_mod, "_get_access_password", lambda: "secret123")
        # Simulate remote non-local request
        monkeypatch.setattr(auth_mod, "_is_local_request", lambda req: False)

        # 1. Remote request without auth should receive 401 with WWW-Authenticate header
        res_unauth = await async_client.get("/opds")
        assert res_unauth.status_code == 401
        assert 'Basic realm="Dijital Kutuphane OPDS"' in res_unauth.headers.get(
            "www-authenticate", ""
        )

        # 2. Remote request with invalid HTTP Basic Auth should receive 401
        bad_creds = base64.b64encode(b"admin:wrongpassword").decode("ascii")
        res_bad = await async_client.get("/opds", headers={"Authorization": f"Basic {bad_creds}"})
        assert res_bad.status_code == 401

        # 3. Remote request with valid HTTP Basic Auth should succeed (200)
        good_creds = base64.b64encode(b"admin:secret123").decode("ascii")
        res_good = await async_client.get("/opds", headers={"Authorization": f"Basic {good_creds}"})
        assert res_good.status_code == 200
        assert "urn:dijital-kutuphane:opds:root" in res_good.text
