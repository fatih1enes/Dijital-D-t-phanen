"""Pydantic models for Dijital Kütüphane."""

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Yapay zeka asistanına gönderilecek sohbet mesajı. En az 1, en fazla 2000 karakterden oluşmalıdır.",
    )
    target_book_hash: str | None = Field(
        None,
        description="Eğer mesaj spesifik bir kitap okuma ekranından (Workspace Reader) atılıyorsa o kitabın hash kimliği.",
    )
    load_full_book: bool = Field(
        False,
        description="Eğer True ise, yapay zeka hafızasına o kitabın TAM metnini (PDF text) tek seferde yükler.",
    )

    @field_validator("message", mode="before")
    @classmethod
    def strip_message(cls, v: str) -> str:
        """Kullanıcının gönderdiği mesajın başındaki ve sonundaki gereksiz boşlukları kırpar."""
        if isinstance(v, str):
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Mesaj sadece boşluklardan oluşamaz.")
            return trimmed
        return v


class BookUpdateRequest(BaseModel):
    """Request model for book update."""

    kitap_adi: str | None = Field(
        None,
        max_length=255,
        description="Güncellenecek kitabın tam adı. En fazla 255 karakter uzunluğunda olabilir.",
    )
    yazar: str | None = Field(
        None,
        max_length=255,
        description="Güncellenecek yazar adı veya yazarlar listesi. En fazla 255 karakter uzunluğunda olabilir.",
    )
    kategori: str | None = Field(
        None,
        max_length=100,
        description="Kitabın ana kategorisi (Tarih, Bilim vb.). En fazla 100 karakter uzunluğunda olabilir.",
    )
    alt_kategori: str | None = Field(
        None,
        max_length=100,
        description="Kitabın alt kategorisi (Kültür Tarihi, Teorik Fizik vb.). En fazla 100 karakter uzunluğunda olabilir.",
    )
    ozet: str | None = Field(
        None,
        max_length=5000,
        description="Kitabın içeriğini detaylandıran özet metni. En fazla 5000 karakter uzunluğunda olabilir.",
    )
    anahtar_kelimeler: str | None = Field(
        None,
        max_length=500,
        description="Kitabı niteleyen anahtar kelimeler (virgülle ayrılmış). En fazla 500 karakter uzunluğunda olabilir.",
    )

    @field_validator(
        "kitap_adi",
        "yazar",
        "kategori",
        "alt_kategori",
        "ozet",
        "anahtar_kelimeler",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, v: str | None) -> str | None:
        """Güncellenecek metinsel alanlardaki gereksiz baş/son boşlukları otomatik kırpar."""
        if isinstance(v, str):
            return v.strip()
        return v


class SaveProgressRequest(BaseModel):
    """Request model for saving reading progress."""

    page: int = Field(
        ...,
        ge=1,
        le=100000,
        description="Okunulan son sayfa numarası. 1 ile 100.000 arasında geçerli bir tam sayı olmalıdır.",
    )
    total_pages: int | None = Field(
        None,
        ge=1,
        le=100000,
        description="Kitabın toplam sayfa sayısı (opsiyonel, ilerleme yüzdesi senkronu için).",
    )


class BookOrderRequest(BaseModel):
    """Request model for updating book order."""

    order: list[str] = Field(
        ...,
        description="Kitapların grid üzerindeki yeni sıralamasını temsil eden dosya hash'leri dizisi.",
    )

    @field_validator("order")
    @classmethod
    def validate_order_list(cls, v: list[str]) -> list[str]:
        """Sıralama listesinin sınırlarını ve içerisindeki elemanların geçerliliğini denetler."""
        if len(v) > 10000:
            raise ValueError("Sıralama listesi en fazla 10000 eleman içerebilir.")

        cleaned_list = []
        for idx, item in enumerate(v):
            if not isinstance(item, str):
                raise ValueError(f"Liste içerisindeki {idx}. eleman bir metin (string) olmalıdır.")

            trimmed = item.strip()
            if not trimmed:
                raise ValueError(f"Liste içerisindeki {idx}. eleman boş bırakılamaz.")
            cleaned_list.append(trimmed)
        return cleaned_list


class AnnotationCreateRequest(BaseModel):
    """Request model for creating or updating a book annotation."""

    id: str = Field(..., min_length=1, max_length=128, description="Benzersiz not/vurgu kimliği.")
    sayfa_no: int = Field(..., ge=1, le=100000, description="Notun alındığı sayfa numarası.")
    secilen_metin: str | None = Field(default="", max_length=10000, description="Vurgulanan metin.")
    not_metni: str | None = Field(
        default="", max_length=10000, description="Kullanıcının yazdığı not."
    )
    renk_hex: str = Field(default="#fef08a", max_length=32, description="Vurgu rengi hex kodu.")
    renk_sinif: str = Field(default="yellow", max_length=32, description="Vurgu rengi css sınıfı.")
    koordinatlar: str | None = Field(default="[]", description="JSON formatında koordinat dizisi.")


class AnnotationBatchRequest(BaseModel):
    """Request model for batch saving annotations."""

    annotations: list[AnnotationCreateRequest] = Field(
        ..., max_length=2000, description="Toplu senkronize edilecek notlar listesi."
    )


class LoginRequest(BaseModel):
    """Request model for login authentication."""

    password: str = Field(default="", max_length=255, description="Erişim şifresi.")


class CollectionCreateRequest(BaseModel):
    """Request model for creating a collection."""

    isim: str = Field(..., min_length=1, max_length=120, description="Koleksiyon adı.")
    is_dynamic: bool = Field(default=False, description="Dinamik akıllı koleksiyon mu?")
    rule_json: str | None = Field(default=None, description="Dinamik kural JSON tanımı.")

    @field_validator("isim", mode="before")
    @classmethod
    def clean_name(cls, v: str) -> str:
        import re

        if isinstance(v, str):
            cleaned = re.sub(r"\s+", " ", v).strip()
            if not cleaned:
                raise ValueError("Koleksiyon adı boş olamaz.")
            return cleaned
        return v


class CollectionAddBookRequest(BaseModel):
    """Request model for adding a book to a collection."""

    kitap_hash: str = Field(..., description="Kitap dosya hash kimliği.")


class SettingsUpdateRequest(BaseModel):
    """Request model for updating application settings."""

    max_pages: int | None = Field(None, ge=1, le=100)
    ocr_pages: int | None = Field(None, ge=0, le=60)
    vision_pages: int | None = Field(None, ge=0, le=60)
    vision_max_image_dim: int | None = Field(None, ge=256, le=2400)
    vision_jpeg_quality: int | None = Field(None, ge=40, le=95)
    ai_max_chars: int | None = Field(None, ge=1000, le=250000)
    tesseract_cmd: str | None = Field(None, max_length=500)
    ai_provider: str | None = Field(None, max_length=50)
    ai_api_key: str | None = Field(None, max_length=500)
    ai_base_url: str | None = Field(None, max_length=500)
    gemini_model: str | None = Field(None, max_length=100)
    ollama_model: str | None = Field(None, max_length=100)
    lmstudio_model: str | None = Field(None, max_length=100)
    google_search_grounding: bool | None = None
    gemini_cascade_mode: bool | None = None
    gemini_cascade_models: list[str] | None = None
    access_password: str | None = Field(None, max_length=100)
    watchfolder_enabled: bool | None = None
    watchfolder_path: str | None = None
    watchfolder_interval: int | None = None

    model_config = {"extra": "allow"}


class TelegramSendCodeRequest(BaseModel):
    """Request model for requesting Telegram auth code."""

    api_id: str | int = Field(..., description="Telegram API ID")
    api_hash: str = Field(..., min_length=10, max_length=100, description="Telegram API Hash")
    phone_number: str = Field(
        ..., min_length=7, max_length=30, description="Telegram phone number (+90...)"
    )
    chat_target: str | None = Field(
        None, max_length=100, description="Telegram target chat/channel (default 'me')"
    )


class TelegramVerifyRequest(BaseModel):
    """Request model for verifying Telegram auth code and 2FA password."""

    code: str = Field(..., min_length=3, max_length=10, description="SMS or app verification code")
    password: str | None = Field(
        None, max_length=100, description="Two-step verification (2FA) cloud password"
    )


class TelegramSyncRequest(BaseModel):
    """Request model for triggering Telegram sync."""

    chat_target: str | None = Field(
        None,
        max_length=100,
        description="Target chat/channel ID or username (default 'me')",
    )
    api_key: str | None = Field(None, max_length=500, description="AI API key")
    provider: str | None = Field(
        None, max_length=50, description="AI provider (gemini, ollama, etc.)"
    )
    model_name: str | None = Field(None, max_length=100, description="AI model name")
    base_url: str | None = Field(None, max_length=500, description="AI base URL")
    reset_cursor: bool = Field(
        default=False,
        description="Whether to reset message ID cursor to scan from beginning",
    )


class TelegramSettingsRequest(BaseModel):
    """Request model for updating Telegram settings."""

    chat_target: str = Field(
        ..., min_length=1, max_length=100, description="Telegram target chat or channel"
    )


class DebateRequest(BaseModel):
    """Request model for Dialectic Multi-Agent Debate."""

    book_hashes: list[str] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Tartışmaya dahil edilecek en az 2 kitap hash'i.",
    )
    topic: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="Kitaplar arasında tartışılacak felsefi veya kavramsal konu.",
    )
    rounds: int = Field(
        default=2, ge=1, le=3, description="Diyalektik tartışma tur sayısı (1-3 arası)."
    )


class EntityUpsertRequest(BaseModel):
    """Request model for creating/updating a knowledge graph entity node."""

    id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    entity_type: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=2000)
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class RelationCreateRequest(BaseModel):
    """Request model for creating a directed edge between two entities."""

    source_id: str = Field(..., min_length=1, max_length=255)
    relation_type: str = Field(..., min_length=1, max_length=100)
    target_id: str = Field(..., min_length=1, max_length=255)
    weight: float = Field(default=1.0, ge=0.0, le=10.0)
    source_evidence: str = Field(default="", max_length=2000)


class BookmarkToggleRequest(BaseModel):
    """Request model for adding or toggling a page bookmark."""

    sayfa_no: int = Field(..., ge=1, le=100000, description="Yer imi konulacak sayfa numarası.")
    etiket: str = Field(default="", max_length=240, description="İsteğe bağlı yer imi etiketi.")
    toggle: bool = Field(default=True, description="Zaten varsa kaldırılsın mı?")


class TTSSynthesizeRequest(BaseModel):
    """Request model for neural Turkish TTS synthesis with word boundary timestamps."""

    text: str = Field(..., min_length=1, max_length=3500, description="Seslendirilecek Türkçe/çok dilli metin.")
    voice: str = Field(default="tr-TR-EmelNeural", max_length=80, description="Sinirsel ses kimliği.")
    rate: float = Field(default=1.0, ge=0.5, le=2.2, description="Konuşma hızı çarpanı.")


class ReadingHeartbeatRequest(BaseModel):
    """Request model for recording active focused reading duration and page progression."""

    dosya_hash: str = Field(..., min_length=16, max_length=128)
    delta_seconds: int = Field(..., ge=1, le=600)
    current_page: int = Field(default=1, ge=1, le=100000)
    pages_read_delta: int = Field(default=0, ge=0, le=500)


class SRSCardCreateRequest(BaseModel):
    """Request model for creating an FSRS v5 flashcard manually or from an annotation."""

    dosya_hash: str = Field(..., min_length=16, max_length=128)
    sayfa_no: int = Field(default=1, ge=1, le=100000)
    not_id: str | None = Field(default=None, max_length=128)
    on_yuz: str = Field(..., min_length=1, max_length=4000)
    arka_yuz: str = Field(..., min_length=1, max_length=6000)
    baglam: str = Field(default="", max_length=2000)


class SRSReviewRequest(BaseModel):
    """Request model for grading an FSRS v5 flashcard (1=Again, 2=Hard, 3=Good, 4=Easy)."""

    rating: int = Field(..., ge=1, le=4)
