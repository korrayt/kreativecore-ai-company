# Kreative Core — GitHub AI Company

Tamamı GitHub üzerinde çalışan, kişisel bilgisayar gerektirmeyen ve ücretli bir yapay zekâ
API'sine bağlanmayan şirket işletim sistemi.

## Sistem ne yapar?

- `tasks/projects/` altındaki her klasörü proje kabul eder.
- `tasks/inbox/` altındaki her klasör veya Markdown dosyasını görev kabul eder.
- Günlük tarama; portföy, görev kuyruğu, departman dağılımı ve GitHub issue'ları üretir.
- Analiz, planlama, kodlama ve PR incelemesi GitHub-hosted runner üzerinde çalışır.
- Aynı reponun private GitHub Release alanında saklanan açık model ve `llama.cpp` kullanılır.
- Copilot, OpenAI, Anthropic veya token başına ücretli başka bir model servisi kullanılmaz.
- AI ana dala doğrudan yazmaz; ayrı branch ve pull request açar.

## İlk kurulum

1. Yeni bir **private** GitHub repo oluştur.
2. Bu paketteki `UPLOAD_TO_NEW_REPO` klasörünün içeriğini repo köküne yükle.
3. `QUICKSTART.md` adımlarını uygula.
4. Önce **Bootstrap AI Engine**, ardından **Engine Health Check** workflow'unu çalıştır.

## Akış

```text
Telefon / GitHub
      ↓
Project ve task klasörleri
      ↓
Daily Intake & Routing
      ↓
20 departman + 33 ajan profili
      ↓
Mobile Company Control
      ↓
GitHub-hosted runner
      ↓
Repo Release içindeki açık model + llama.cpp
      ↓
Analiz / kod / test / PR
      ↓
Telefondan inceleme ve merge
```

## Gerçekçi sınır

Standart private GitHub runner küçük bir CPU modeline uygundur. Bu sistem, güçlü ticari coding
agent'lar kadar tutarlı olmayabilir. Güvenli JSON protokolü, sabit test komutları ve PR onayı bu
nedenle zorunludur.
