# AI-voice-talking-bot

PLAN.md'ye göre geliştirilen, Türkçe konuşan sarkastik/ironik kişilikli Discord botu.

## Özellikler (hedef)
- Mention/reply ile metin sohbet
- Kurucu (owner) için 1-1 sesli sohbet (opsiyonel modül)
- Otomatik hafıza (SQLite + opsiyonel vektör arama)
- Web arama (Brave → Serper → Tavily fallback, opsiyonel)
- Prompt injection koruması + rate limit
- Kurucu DM yönetimi

## Kurulum
1) Discord Developer Portal'da bot oluştur, token al.
2) **Message Content Intent**'i aç (metin sohbet için gerekli).
3) Repo kökünde `.env` oluştur:
   - Şablon: `.env.example`
4) Bağımlılıklar:
   - `python3.11+`
   - (Ses için) `ffmpeg`

## Çalıştırma
`python3 -m src.main`

## Ses (MVP)
- `ENABLE_VOICE=true`
- `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` gir
- Sunucuda `ffmpeg` kurulu olmalı
- Kurucu bir ses kanalına girince bot kanala katılır ve kısa bir selam verir.
- Kurucu botla DM'den sohbet ederse, yanıtı VC'de de seslendirmeyi dener.

## Maliyet / fiyat-performans önerileri
- `ENABLE_WEB_SEARCH=false` ve `ENABLE_VOICE=false` ile başlayıp, ihtiyaca göre aç.
- Ses (STT/TTS) maliyeti hızlı büyür: günlük limit + kurucu-only kuralı şart.
- Embedding maliyeti için (ileride) yerel embedding opsiyonu eklenebilir; ilk etapta basit SQLite retrieval daha ucuz/kolay.

## Durum
Şu an proje iskeleti + Discord event akışı hazır. Sonraki commit'lerde Gemini, hafıza, güvenlik, web arama ve ses modülü eklenecek.
