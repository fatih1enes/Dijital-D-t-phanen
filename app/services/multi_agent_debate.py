"""Dialectic Multi-Agent Debate Engine for cross-book intellectual exploration."""

import asyncio
import logging
import re
from typing import Any

from app.database import DatabaseManager
from app.logger import log_event
from app.prompts import (
    build_debate_agent_instruction,
    build_debate_synthesis_instruction,
)
from app.services.hybrid_search import hybrid_search_engine

logger = logging.getLogger(__name__)

DEFAULT_AI_PROVIDER = "gemini"
ROLE_THESIS = "Tez"
ROLE_ANTITHESIS = "Antitez"
DEFAULT_CITATION = "[Sayfa 1]"
LOG_CATEGORY_AI = "ai"


def _extract_citations(text: str) -> list[int]:
    """Extract all [Sayfa X] citation page numbers from a text block."""
    matches = re.findall(r"\[Sayfa\s+(\d+)\]", text, flags=re.IGNORECASE)
    pages: set[int] = set()
    for m in matches:
        try:
            pages.add(int(m))
        except ValueError:
            continue
    return sorted(pages)


def _is_ai_error(text: str | None) -> bool:
    """Check if AI response represents an unhandled error string."""
    if not text:
        return True
    t = text.strip()
    return t.startswith("Error:") or t.startswith("Error from") or t.startswith("Hata:")


class MultiAgentDebateEngine:
    """Engine that coordinates dialectic debates between two or more books with page citations."""

    @classmethod
    async def _gather_book_grounding(
        cls, db: DatabaseManager, file_hash: str, topic: str
    ) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
        """Fetch book metadata and top grounding chunk passages with page citations."""
        book_row = await db.get_book_by_hash(file_hash)
        if not book_row:
            book_dict = {
                "dosya_hash": file_hash,
                "baslik": f"Kitap ({file_hash[:8]})",
                "yazar": "Bilinmeyen Yazar",
                "ozet": "",
            }
        else:
            book_dict = dict(book_row)

        passages = await hybrid_search_engine.hybrid_search(
            db, query=topic, file_hash=file_hash, limit=5
        )

        evidence_lines = []
        if passages:
            for p in passages:
                pg = p.get("sayfa_no", 1)
                txt = p.get("metin", "").strip()
                evidence_lines.append(f"[Sayfa {pg}]: {txt}")
        else:
            ozet = book_dict.get("ozet") or ""
            if ozet:
                evidence_lines.append(f"[Genel Özet]: {ozet}")
            else:
                b_name = book_dict.get("kitap_adi") or book_dict.get("baslik", "")
                evidence_lines.append(f"[Kitap]: {b_name} ({book_dict.get('yazar', '')})")

        return book_dict, passages, "\n\n".join(evidence_lines)

    @classmethod
    async def _build_round_1(
        cls,
        has_ai: bool,
        topic: str,
        book_meta_a: tuple[str, str, str, list[dict]],
        book_meta_b: tuple[str, str, str, list[dict]],
        ai_params: dict[str, Any],
    ) -> tuple[dict[str, Any], list[str], list[str]]:
        """Generate Round 1 (Thesis and Antithesis) with grounded citations."""
        hash_a, title_a, author_a, chunks_a = (
            book_meta_a[0],
            book_meta_a[1],
            book_meta_a[2],
            book_meta_a[3],
        )
        hash_b, title_b, author_b, chunks_b = (
            book_meta_b[0],
            book_meta_b[1],
            book_meta_b[2],
            book_meta_b[3],
        )
        evidence_a, evidence_b = ai_params["evidence_a"], ai_params["evidence_b"]

        if has_ai:
            from app.ai_router import generate_ai_response

            inst_a = build_debate_agent_instruction(title_a, author_a, role="Tez Savunucusu")
            prompt_a = f"Konu: {topic}\n\nKitabındaki İlgili Pasajlar ve Kanıtlar:\n{evidence_a}\n\nGörevin: '{title_a}' kitabının bakış açısıyla '{topic}' konusundaki ana tezini sun. Argümanlarını mutlaka metindeki sayfa referansları ([Sayfa X]) ile gerekçelendir."
            try:
                thesis_text = await asyncio.to_thread(
                    generate_ai_response,
                    prompt=prompt_a,
                    provider=ai_params.get("provider") or DEFAULT_AI_PROVIDER,
                    api_key=ai_params.get("api_key") or "",
                    model=ai_params.get("model"),
                    base_url=ai_params.get("base_url"),
                    system_instruction=inst_a,
                )
                if _is_ai_error(thesis_text):
                    raise ValueError(thesis_text)
            except Exception as err:
                log_event(LOG_CATEGORY_AI, "WARNING", f"Debate round 1 Thesis AI error: {err}")
                thesis_text = f"[{title_a}] perspektifinden '{topic}': Metindeki pasajlar çerçevesinde ana fikir ele alınmaktadır."

            inst_b = build_debate_agent_instruction(title_b, author_b, role="Antitez Savunucusu")
            prompt_b = f"Konu: {topic}\n\nKarşı Tarafın Tezi ({title_a}):\n{thesis_text}\n\nSenin Kitabındaki Pasajlar ve Kanıtlar ({title_b}):\n{evidence_b}\n\nGörevin: Karşı tarafın tezini eleştir, kitabın '{title_b}' perspektifinden antitezi sun ve iddialarını [Sayfa X] referanslarıyla destekle."
            try:
                antithesis_text = await asyncio.to_thread(
                    generate_ai_response,
                    prompt=prompt_b,
                    provider=ai_params.get("provider") or DEFAULT_AI_PROVIDER,
                    api_key=ai_params.get("api_key") or "",
                    model=ai_params.get("model"),
                    base_url=ai_params.get("base_url"),
                    system_instruction=inst_b,
                )
                if _is_ai_error(antithesis_text):
                    raise ValueError(antithesis_text)
            except Exception as err:
                log_event(LOG_CATEGORY_AI, "WARNING", f"Debate round 1 Antithesis AI error: {err}")
                antithesis_text = f"[{title_b}] perspektifinden karşı tez: '{title_a}' tezine alternatif bir yaklaşım sunulmaktadır."
        else:
            cite_a_str = (
                " ".join(f"[Sayfa {c['sayfa_no']}]" for c in chunks_a[:3]) or DEFAULT_CITATION
            )
            cite_b_str = (
                " ".join(f"[Sayfa {c['sayfa_no']}]" for c in chunks_b[:3]) or DEFAULT_CITATION
            )
            thesis_text = f"'{title_a}' ({author_a}), '{topic}' meselesini temel olarak şu odak üzerinden ele alır: {evidence_a[:350]}... Bu yaklaşım konunun köklerini ve pratik sonuçlarını aydınlatmaktadır {cite_a_str}."
            antithesis_text = f"'{title_b}' ({author_b}) ise bu bakış açısına eleştirel yaklaşarak şu alternatif boyuta dikkat çeker: {evidence_b[:350]}... Dolayısıyla tek taraflı bir kabul yerine bu dinamik hesaba katılmalıdır {cite_b_str}."

        cites_a = [f"{hash_a}:{p}" for p in _extract_citations(thesis_text)]
        cites_b = [f"{hash_b}:{p}" for p in _extract_citations(antithesis_text)]

        round_data = {
            "round": 1,
            "agent_a": {
                "role": ROLE_THESIS,
                "book_hash": hash_a,
                "book_title": title_a,
                "response": thesis_text,
                "citations": cites_a,
            },
            "agent_b": {
                "role": ROLE_ANTITHESIS,
                "book_hash": hash_b,
                "book_title": title_b,
                "response": antithesis_text,
                "citations": cites_b,
            },
        }
        return round_data, cites_a, cites_b

    @classmethod
    async def _build_round_2(
        cls,
        has_ai: bool,
        topic: str,
        book_meta_a: tuple[str, str, str, list[dict]],
        book_meta_b: tuple[str, str, str, list[dict]],
        antithesis_text: str,
        ai_params: dict[str, Any],
    ) -> tuple[dict[str, Any], list[str], list[str]]:
        """Generate Round 2 (Rebuttal and Cross-Examination) with grounded citations."""
        hash_a, title_a, author_a, chunks_a = (
            book_meta_a[0],
            book_meta_a[1],
            book_meta_a[2],
            book_meta_a[3],
        )
        hash_b, title_b, author_b, chunks_b = (
            book_meta_b[0],
            book_meta_b[1],
            book_meta_b[2],
            book_meta_b[3],
        )
        evidence_a, evidence_b = ai_params["evidence_a"], ai_params["evidence_b"]

        if has_ai:
            from app.ai_router import generate_ai_response

            inst_a = build_debate_agent_instruction(title_a, author_a, role="Tez Savunucusu")
            rebut_prompt_a = f"Konu: {topic}\nAntitez ({title_b}): {antithesis_text}\nKitabın Kanıtları ({title_a}): {evidence_a}\nGörevin: Antiteze cevap ver, kitabının savını derinleştir ve [Sayfa X] referansı kullan."
            try:
                rebuttal_a = await asyncio.to_thread(
                    generate_ai_response,
                    prompt=rebut_prompt_a,
                    provider=ai_params.get("provider") or DEFAULT_AI_PROVIDER,
                    api_key=ai_params.get("api_key") or "",
                    model=ai_params.get("model"),
                    base_url=ai_params.get("base_url"),
                    system_instruction=inst_a,
                )
                if _is_ai_error(rebuttal_a):
                    raise ValueError(rebuttal_a)
            except Exception as err:
                log_event(LOG_CATEGORY_AI, "WARNING", f"Debate round 2 rebuttal A error: {err}")
                rebuttal_a = f"'{title_a}', '{title_b}' tarafından getirilen itirazı metindeki argümanlarıyla yanıtlamaktadır."

            inst_b = build_debate_agent_instruction(title_b, author_b, role="Antitez Savunucusu")
            rebut_prompt_b = f"Konu: {topic}\nTez Sahibinin Cevabı ({title_a}): {rebuttal_a}\nKitabın Kanıtları ({title_b}): {evidence_b}\nGörevin: Son karşı değerlendirmeni yap ve [Sayfa X] referansı kullan."
            try:
                rebuttal_b = await asyncio.to_thread(
                    generate_ai_response,
                    prompt=rebut_prompt_b,
                    provider=ai_params.get("provider") or DEFAULT_AI_PROVIDER,
                    api_key=ai_params.get("api_key") or "",
                    model=ai_params.get("model"),
                    base_url=ai_params.get("base_url"),
                    system_instruction=inst_b,
                )
                if _is_ai_error(rebuttal_b):
                    raise ValueError(rebuttal_b)
            except Exception as err:
                log_event(LOG_CATEGORY_AI, "WARNING", f"Debate round 2 rebuttal B error: {err}")
                rebuttal_b = f"'{title_b}', karşılıklı argümanları değerlendirerek pozisyonunu pekiştirmektedir."
        else:
            cite_a_str = f"[Sayfa {chunks_a[0]['sayfa_no']}]" if chunks_a else DEFAULT_CITATION
            cite_b_str = f"[Sayfa {chunks_b[0]['sayfa_no']}]" if chunks_b else DEFAULT_CITATION
            rebuttal_a = f"'{title_a}' cephesinden yanıt: Karşı tarafın vurguladığı hususlar geçerli olmakla birlikte, temel nedensellik bağlamında bizim savımız önceliklidir {cite_a_str}."
            rebuttal_b = f"'{title_b}' cephesinden son değerlendirme: Her iki argümanın metodolojisi farklıdır; ancak bizim vurguladığımız boyut göz ardı edilemez {cite_b_str}."

        cites_a = [f"{hash_a}:{p}" for p in _extract_citations(rebuttal_a)]
        cites_b = [f"{hash_b}:{p}" for p in _extract_citations(rebuttal_b)]

        round_data = {
            "round": 2,
            "agent_a": {
                "role": "Müzakere / Rebuttal",
                "book_hash": hash_a,
                "book_title": title_a,
                "response": rebuttal_a,
                "citations": cites_a,
            },
            "agent_b": {
                "role": "Müzakere / Karşı-Cevap",
                "book_hash": hash_b,
                "book_title": title_b,
                "response": rebuttal_b,
                "citations": cites_b,
            },
        }
        return round_data, cites_a, cites_b

    @classmethod
    async def _build_synthesis(
        cls,
        has_ai: bool,
        topic: str,
        title_a: str,
        title_b: str,
        debate_rounds: list[dict[str, Any]],
        ai_params: dict[str, Any],
    ) -> dict[str, Any]:
        """Synthesize dialectic positions into higher-order conceptual harmony."""
        if has_ai:
            from app.ai_router import generate_ai_response

            all_debate_text = "\n\n".join(
                f"--- RAUND {r['round']} ---\n[TEZ - {r['agent_a']['book_title']}]:\n{r['agent_a']['response']}\n\n[ANTİTEZ - {r['agent_b']['book_title']}]:\n{r['agent_b']['response']}"
                for r in debate_rounds
            )
            synth_prompt = f"Tartışılan Konu: {topic}\n\n{all_debate_text}\n\nGörevin:\n1. Ortak Paydalar: İki eserin uyuştuğu 2 temel noktayı belirt.\n2. Çatışma Noktaları: İki eserin birbirini dışlayan ya da çatışan temel farkını açıkla.\n3. Üst Sentez (Aufhebung): Bu iki eseri okuyan bir araştırmacının kazanacağı birleşik perspektifi özetle."
            try:
                summary_text = await asyncio.to_thread(
                    generate_ai_response,
                    prompt=synth_prompt,
                    provider=ai_params.get("provider") or DEFAULT_AI_PROVIDER,
                    api_key=ai_params.get("api_key") or "",
                    model=ai_params.get("model"),
                    base_url=ai_params.get("base_url"),
                    system_instruction=build_debate_synthesis_instruction(),
                )
                if _is_ai_error(summary_text):
                    raise ValueError(summary_text)
            except Exception as err:
                log_event(LOG_CATEGORY_AI, "WARNING", f"Debate synthesis AI error: {err}")
                summary_text = f"'{title_a}' ve '{title_b}' eserleri '{topic}' konusunda tamamlayıcı iki eksen oluşturmaktadır."
        else:
            summary_text = (
                f"'{title_a}' ve '{title_b}' eserlerinin '{topic}' konusundaki diyalektik karşılaşması, "
                f"konunun hem teorik temellerini hem de pratik sonuçlarını bütünsel olarak kavramayı sağlar."
            )

        return {
            "agreements": [
                f"Her iki eser de '{topic}' konusunun çok boyutlu ve kritik önem taşıdığında birleşmektedir.",
                f"Gerek '{title_a}' gerekse '{title_b}' tek boyutlu indirgemeci yaklaşımları aşmayı amaçlar.",
            ],
            "contradictions": [
                f"'{title_a}' nedensellik ve ilkeler üzerinde dururken, '{title_b}' etki ve bağlamsal süreçleri öne çıkarır.",
            ],
            "unifying_principle": (
                f"'{topic}' meselesi, '{title_a}' eserinin yapısal kavrayışı ile '{title_b}' eserinin "
                f"dinamik perspektifinin birleşimiyle eksiksiz anlaşılabilir."
            ),
            "summary": summary_text,
        }

    @classmethod
    async def conduct_debate(
        cls,
        db: DatabaseManager,
        book_hashes: list[str],
        topic: str,
        rounds: int = 2,
        provider: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        """Conduct a dialectic debate between books on a given topic with grounded citations."""
        if len(book_hashes) < 2:
            raise ValueError("Diyalektik tartışma için en az iki kitap seçilmelidir.")

        rounds_clamped = max(1, min(3, int(rounds)))
        hash_a, hash_b = book_hashes[0], book_hashes[1]

        book_a, chunks_a, evidence_a = await cls._gather_book_grounding(db, hash_a, topic)
        book_b, chunks_b, evidence_b = await cls._gather_book_grounding(db, hash_b, topic)

        title_a = (
            book_a.get("kitap_adi") or book_a.get("baslik") or book_a.get("dosya_adi") or hash_a[:8]
        )
        author_a = book_a.get("yazar") or "Yazar"
        title_b = (
            book_b.get("kitap_adi") or book_b.get("baslik") or book_b.get("dosya_adi") or hash_b[:8]
        )
        author_b = book_b.get("yazar") or "Yazar"

        has_ai = bool(api_key or provider in ["ollama", "lmstudio"])
        debate_rounds: list[dict[str, Any]] = []
        collected_citations: set[str] = set()

        meta_a = (hash_a, title_a, author_a, chunks_a)
        meta_b = (hash_b, title_b, author_b, chunks_b)
        ai_params = {
            "evidence_a": evidence_a,
            "evidence_b": evidence_b,
            "provider": provider,
            "api_key": api_key,
            "model": model,
            "base_url": base_url,
        }

        # Round 1
        r1_data, r1_cites_a, r1_cites_b = await cls._build_round_1(
            has_ai, topic, meta_a, meta_b, ai_params
        )
        debate_rounds.append(r1_data)
        collected_citations.update(r1_cites_a)
        collected_citations.update(r1_cites_b)

        # Round 2
        if rounds_clamped >= 2:
            antithesis_text = r1_data["agent_b"]["response"]
            r2_data, r2_cites_a, r2_cites_b = await cls._build_round_2(
                has_ai, topic, meta_a, meta_b, antithesis_text, ai_params
            )
            debate_rounds.append(r2_data)
            collected_citations.update(r2_cites_a)
            collected_citations.update(r2_cites_b)

        # Final Synthesis
        synthesis_data = await cls._build_synthesis(
            has_ai, topic, title_a, title_b, debate_rounds, ai_params
        )

        log_event(
            LOG_CATEGORY_AI,
            "INFO",
            f"Diyalektik tartışma tamamlandı: '{topic}' ({title_a} vs {title_b})",
        )

        return {
            "topic": topic,
            "books": [
                {
                    "hash": hash_a,
                    "title": title_a,
                    "author": author_a,
                    "passages_count": len(chunks_a),
                },
                {
                    "hash": hash_b,
                    "title": title_b,
                    "author": author_b,
                    "passages_count": len(chunks_b),
                },
            ],
            "rounds": debate_rounds,
            "synthesis": synthesis_data,
            "citations": sorted(collected_citations),
        }


# Global singleton instance
multi_agent_debate_engine = MultiAgentDebateEngine()
