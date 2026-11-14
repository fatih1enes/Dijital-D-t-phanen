import pytest

pytestmark = pytest.mark.asyncio


class TestDatabaseManager:
    """Test database manager functionality using asynchronous calls."""

    async def test_database_initialization(self, temp_db_conn):
        """Test database table creation."""
        # Check if tables exist by trying to query them
        cursor = await temp_db_conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in await cursor.fetchall()]

        assert "kitaplar" in tables
        assert "koleksiyonlar" in tables
        assert "koleksiyon_kitap" in tables

    async def test_add_book(self, temp_db, sample_book_data):
        """Test adding a book to database."""
        await temp_db.add_book(sample_book_data)

        books_res = await temp_db.get_all_books()
        books = books_res["items"]
        assert len(books) == 1
        assert books[0]["kitap_adi"] == sample_book_data["kitap_adi"]
        assert books[0]["yazar"] == sample_book_data["yazar"]

    async def test_get_all_books_empty(self, temp_db):
        """Test getting books from empty database."""
        books_res = await temp_db.get_all_books()
        books = books_res["items"]
        assert len(books) == 0

    async def test_book_exists(self, temp_db, sample_book_data):
        """Test checking if book exists by hash."""
        # Book doesn't exist initially
        assert not await temp_db.book_exists(sample_book_data["dosya_hash"])

        # Add book
        await temp_db.add_book(sample_book_data)

        # Book should exist now
        assert await temp_db.book_exists(sample_book_data["dosya_hash"])

    async def test_delete_book(self, temp_db, sample_book_data):
        """Test deleting a book."""
        # Add book
        await temp_db.add_book(sample_book_data)
        assert await temp_db.book_exists(sample_book_data["dosya_hash"])

        # Delete book (this will fail due to missing file, but should handle gracefully)
        await temp_db.delete_book(sample_book_data["dosya_hash"])

        # Book should be removed from database
        assert not await temp_db.book_exists(sample_book_data["dosya_hash"])

    async def test_update_book(self, temp_db, sample_book_data):
        """Test updating book metadata."""
        # Add book
        await temp_db.add_book(sample_book_data)

        # Update book
        update_data = {"kitap_adi": "Updated Title", "yazar": "Updated Author"}
        await temp_db.update_book(sample_book_data["dosya_hash"], update_data)

        # Verify update
        books_res = await temp_db.get_all_books()
        books = books_res["items"]
        assert books[0]["kitap_adi"] == "Updated Title"
        assert books[0]["yazar"] == "Updated Author"

    async def test_toggle_favorite(self, temp_db, sample_book_data):
        """Test toggling favorite status."""
        # Add book
        await temp_db.add_book(sample_book_data)

        # Initially not favorite
        books_res = await temp_db.get_all_books()
        books = books_res["items"]
        assert not books[0]["is_favorite"]

        # Toggle to favorite
        result = await temp_db.toggle_favorite(sample_book_data["dosya_hash"])
        assert result

        # Verify
        books_res = await temp_db.get_all_books()
        books = books_res["items"]
        assert books[0]["is_favorite"]

        # Toggle back
        result = await temp_db.toggle_favorite(sample_book_data["dosya_hash"])
        assert not result

        # Verify
        books_res = await temp_db.get_all_books()
        books = books_res["items"]
        assert not books[0]["is_favorite"]

    async def test_collections(self, temp_db):
        """Test collection management."""
        # Add collection
        result = await temp_db.add_collection("Test Collection")
        assert result is not None
        assert result["isim"] == "Test Collection"

        # Get collections
        collections = await temp_db.get_collections()
        assert len(collections) == 1
        assert collections[0]["isim"] == "Test Collection"

        # Try to add duplicate
        result = await temp_db.add_collection("Test Collection")
        assert result is None

        # Delete collection
        await temp_db.delete_collection(collections[0]["id"])
        collections = await temp_db.get_collections()
        assert len(collections) == 0

    async def test_add_book_to_collection(self, temp_db, sample_book_data):
        """Test adding books to collections."""
        # Add book and collection
        await temp_db.add_book(sample_book_data)
        collection = await temp_db.add_collection("Test Collection")

        # Add book to collection
        await temp_db.add_book_to_col(collection["id"], sample_book_data["dosya_hash"])

        # Verify
        books_res = await temp_db.get_all_books()
        books = books_res["items"]
        assert collection["id"] in books[0]["koleksiyonlar"]

    async def test_remove_book_from_collection(self, temp_db, sample_book_data):
        """Test removing books from collections."""
        # Add book and collection
        await temp_db.add_book(sample_book_data)
        collection = await temp_db.add_collection("Test Collection")
        await temp_db.add_book_to_col(collection["id"], sample_book_data["dosya_hash"])

        # Remove from collection
        await temp_db.rm_book_from_col(collection["id"], sample_book_data["dosya_hash"])

        # Verify
        books_res = await temp_db.get_all_books()
        books = books_res["items"]
        assert collection["id"] not in books[0]["koleksiyonlar"]

    async def test_update_reading_progress(self, temp_db, sample_book_data):
        """Test updating reading progress."""
        # Add book
        await temp_db.add_book(sample_book_data)

        # Update progress
        await temp_db.update_reading_progress(sample_book_data["dosya_hash"], 10)

        # Verify
        books_res = await temp_db.get_all_books()
        books = books_res["items"]
        assert books[0]["okunulan_sayfa"] == 10
