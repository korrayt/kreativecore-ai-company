# Hızlı Kurulum

## 1. Yeni repo

GitHub'da boş ve **private** bir repo aç. Önerilen isim:

`kreativecore-ai-company`

## 2. Dosyaları yükle

ZIP'i çıkart. `UPLOAD_TO_NEW_REPO` klasörünün **içindeki bütün dosyaları** yeni reponun köküne
yükle.

İlk commit:

`chore: install Kreative Core GitHub AI Company`

## 3. Actions yetkileri

**Settings → Actions → General → Workflow permissions**

- **Read and write permissions**
- **Allow GitHub Actions to create and approve pull requests**
- Save

## 4. AI motorunu hazırla

**Actions → Bootstrap AI Engine → Run workflow**

Bu tek seferlik iş:

1. Qwen'in resmî Q4 GGUF modelini indirir.
2. `llama.cpp` resmî Ubuntu CPU paketini indirir.
3. SHA-256 manifesti oluşturur.
4. Modeli ve motoru aynı reponun private `ai-engine-v1` Release alanına yükler.

## 5. Test

**Actions → Engine Health Check → Run workflow**

Başarılıysa model, GitHub runner üzerinde yerel JSON yanıtı üretir.

## 6. İlk proje

`tasks/projects/_template` klasörünü kopyala ve örneğin:

`tasks/projects/ilk-projem`

olarak yükle. `PROJECT.toml`, `BRIEF.md` ve `input/` klasörünü doldur.

## 7. Mobilden çalıştır

**Actions → Mobile Company Control → Run workflow**

Örnek analiz:

- Operation: `analyze-project`
- Target: `ilk-projem`
- Agent: `analyst`
- Confirm: `RUN`

Örnek kod görevi:

- Operation: `execute-task`
- Target: görev klasörü veya GitHub issue numarası
- Agent: `coder`
- Confirm: `RUN`

## 8. Ücret güvenliği

Model API ücreti yoktur. Private repo Actions çalışmaları GitHub planındaki aylık dakikalardan
düşebilir. GitHub Billing bölümünde Actions için sıfır dolarlık hard-stop bütçe belirle.
