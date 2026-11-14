"""Tests for Smart Collections (auto-cluster) endpoint."""

import pytest

pytestmark = pytest.mark.asyncio


class TestSmartCollectionsEndpoint:
    """Validate auto-cluster collections functionality."""

    async def test_auto_cluster_empty_library(self, async_client):
        """When no books exist, returns empty status gracefully."""
        res = await async_client.post("/api/collections/auto-cluster?apply=false")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "empty"
        assert data["clusters"] == []

    async def test_auto_cluster_with_books_fallback(self, async_client, temp_db):
        """When books exist, clusters are generated even without external AI."""
        # Insert sample books into db
        await temp_db.add_book(
            {
                "dosya_hash": "hash_ml_1" + "0" * 55,
                "dosya_yolu": "/mock/ml1.pdf",
                "dosya_adi": "ml1.pdf",
                "kitap_adi": "Derin Öğrenme",
                "yazar": "Ian Goodfellow",
                "kategori": "Yapay Zeka",
                "ozet": "Yapay sinir ağları ve derin öğrenme temelleri.",
                "anahtar_kelimeler": "derin öğrenme, yapay zeka, nöron",
                "has_cover": False,
            }
        )
        await temp_db.add_book(
            {
                "dosya_hash": "hash_ml_2" + "0" * 55,
                "dosya_yolu": "/mock/ml2.pdf",
                "dosya_adi": "ml2.pdf",
                "kitap_adi": "Makine Öğrenmesi",
                "yazar": "Tom Mitchell",
                "kategori": "Yapay Zeka",
                "ozet": "Gözetimli ve gözetimsiz makine öğrenmesi teknikleri.",
                "anahtar_kelimeler": "makine öğrenmesi, veri",
                "has_cover": False,
            }
        )
        await temp_db.add_book(
            {
                "dosya_hash": "hash_hist_1" + "0" * 53,
                "dosya_yolu": "/mock/hist1.pdf",
                "dosya_adi": "hist1.pdf",
                "kitap_adi": "Devlet-i Aliyye",
                "yazar": "Halil İnalcık",
                "kategori": "Tarih",
                "ozet": "Osmanlı İmparatorluğu klasik dönem araştırmaları.",
                "anahtar_kelimeler": "osmanlı, tarih",
                "has_cover": False,
            }
        )

        # Test preview clustering (apply=False)
        res = await async_client.post("/api/collections/auto-cluster?apply=false")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert len(data["clusters"]) >= 2
        categories = [c["name"] for c in data["clusters"]]
        assert "Yapay Zeka" in categories or any("Zeka" in name for name in categories)

        # Test applying collections (apply=True)
        res_apply = await async_client.post("/api/collections/auto-cluster?apply=true")
        assert res_apply.status_code == 200
        apply_data = res_apply.json()
        assert apply_data["applied"] is True
        assert apply_data["created_count"] >= 1

        # Verify created collections in DB
        cols = await temp_db.get_collections()
        assert len(cols) >= 1
