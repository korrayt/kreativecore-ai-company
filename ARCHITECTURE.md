# Mimari

## 1. Company OS

20 departman, 13 çekirdek ajan, uzmanlık promptları, onay kapıları ve yönlendirme kuralları.

## 2. Deterministik orchestrator

Model kullanmadan proje ve görevleri tarar. Aynı işi ikinci kez açmamak için registry tutar.

## 3. GitHub-hosted inference

Bootstrap sonrasında model ve motor aynı reponun private GitHub Release alanında durur. Her AI
workflow'u bu varlıkları indirir, SHA-256 doğrulaması yapar ve `llama-server` başlatır.

## 4. Agent runtime

- İlgili repo dosyalarını seçer.
- Seçilen ajan promptunu yükler.
- Yerel modele istek gönderir.
- Sadece tanımlı JSON protokolünü kabul eder.
- Korunan dosya yollarını reddeder.
- Sabit testleri çalıştırır.
- Değişiklikleri ayrı branch ve PR olarak sunar.

## Korunan alanlar

Coder varsayılan olarak şunları değiştiremez:

- `.github/workflows/`
- `engine/`
- `company/`
- `models/`
- `LICENSES/`
