"""Tests for the enhanced logging system."""

import logging

import pytest

from app.logger import (
    LOG_BUFFER,
    clear_log_buffer,
    get_logs_snapshot,
    log_event,
    normalize_category,
)


class TestLoggingSystem:
    """Test backend logging functions and ring buffer."""

    def test_normalize_category(self):
        """Test category normalization."""
        assert normalize_category("pdf_processing") == "pdf"
        assert normalize_category("ocr") == "pdf"
        assert normalize_category("task") == "upload"
        assert normalize_category("system") == "system"
        assert normalize_category("security") == "security"
        assert normalize_category(None) == "system"

    def test_log_event_and_snapshot(self):
        """Test logging events and getting snapshot."""
        clear_log_buffer()

        e1 = log_event("system", "INFO", "System initialized", version="2.0")
        assert e1["category"] == "system"
        assert e1["level"] == "INFO"
        assert "id" in e1
        assert "iso" in e1
        assert e1["context"]["version"] == "2.0"

        e2 = log_event("pdf_processing", "WARNING", "OCR fallback needed", file="test.pdf")
        assert e2["category"] == "pdf"
        assert e2["level"] == "WARNING"

        e3 = log_event("security", "ERROR", "Invalid access attempt", ip="192.168.1.50")
        assert e3["category"] == "security"
        assert e3["level"] == "ERROR"

        # Check snapshot without filter
        snap = get_logs_snapshot(limit=10)
        assert snap["total"] == 3
        assert len(snap["logs"]) == 3
        assert snap["counts"]["levels"]["INFO"] >= 1
        assert snap["counts"]["levels"]["WARNING"] >= 1
        assert snap["counts"]["levels"]["ERROR"] >= 1

        # Check category filter
        snap_cat = get_logs_snapshot(category="pdf")
        assert snap_cat["total"] == 1
        assert snap_cat["logs"][0]["message"] == "OCR fallback needed"

        # Check level filter
        snap_lvl = get_logs_snapshot(level="ERROR")
        assert snap_lvl["total"] == 1
        assert snap_lvl["logs"][0]["category"] == "security"

        # Check query search filter
        snap_q = get_logs_snapshot(query="192.168.1.50")
        assert snap_q["total"] == 1
        assert snap_q["logs"][0]["level"] == "ERROR"

    def test_clear_log_buffer(self):
        """Test clearing logs buffer."""
        log_event("system", "INFO", "Sample log")
        assert len(LOG_BUFFER) > 0
        cleared = clear_log_buffer()
        assert cleared >= 1
        assert len(LOG_BUFFER) == 0

    def test_unified_python_logger_capture(self):
        """Test that standard python logging warnings and errors are captured in LOG_BUFFER."""
        clear_log_buffer()
        py_logger = logging.getLogger("app.security.test")
        py_logger.warning("Standard python warning message for testing")

        snap = get_logs_snapshot(query="Standard python warning message")
        assert snap["total"] >= 1
        assert snap["logs"][0]["level"] == "WARNING"


class TestLoggingAPIEndpoints:
    """Test HTTP API endpoints for logs."""

    @pytest.mark.asyncio
    async def test_get_logs_endpoint(self, async_client):
        """Test GET /api/logs."""
        log_event("system", "INFO", "Endpoint test entry")
        response = await async_client.get("/api/logs?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert "counts" in data
        assert isinstance(data["logs"], list)

    @pytest.mark.asyncio
    async def test_get_logs_query_filter(self, async_client):
        """Test GET /api/logs with text query."""
        log_event("system", "INFO", "UniqueSearchToken12345")
        response = await async_client.get("/api/logs?q=UniqueSearchToken12345")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("UniqueSearchToken12345" in log_item["message"] for log_item in data["logs"])

    @pytest.mark.asyncio
    async def test_clear_logs_endpoint(self, async_client):
        """Test POST /api/logs/clear."""
        log_event("system", "INFO", "Log to be cleared")
        response = await async_client.post("/api/logs/clear")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @pytest.mark.asyncio
    async def test_export_logs_endpoint(self, async_client):
        """Test GET /api/logs/export in JSON and text format."""
        log_event("system", "INFO", "Log to export")

        # JSON export
        res_json = await async_client.get("/api/logs/export?format=json")
        assert res_json.status_code == 200
        assert "application/json" in res_json.headers.get("content-type", "")
        assert "attachment;" in res_json.headers.get("content-disposition", "")

        # Text/Log export
        res_txt = await async_client.get("/api/logs/export?format=log")
        assert res_txt.status_code == 200
        assert "text/plain" in res_txt.headers.get("content-type", "")
        assert "attachment;" in res_txt.headers.get("content-disposition", "")
