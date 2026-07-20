# Autonomous Company Orchestration

Bu sistemin temel fikri basit:

- `tasks/projects/` altına bırakılan her klasör bir **proje** kabul edilir.
- `tasks/inbox/` altına bırakılan her klasör veya Markdown dosyası bir **görev** kabul edilir.
- Günlük workflow klasörleri tarar.
- Deterministik analiz motoru ilk portföy kaydını, yol haritasını ve departman planını üretir.
- GitHub issue'ları idempotent olarak açılır; aynı iş ikinci kez çoğaltılmaz.
- Her issue uygun özel ajanın adı ve departman etiketiyle hazırlanır.
- Copilot ataması varsayılan olarak kurucu tarafından mobilde yapılır.
- İsteğe bağlı `LOCAL_AI_ENGINE` secret'ı eklenirse `auto_execute = true` işleri
  otomatik olarak ilgili Copilot özel ajanına atanabilir.

## Neden iki katman var?

GitHub Actions güvenilir ve deterministik şirket katmanıdır. Dosya tarar, kayıt tutar, yol
haritası şablonu üretir, issue açar ve işi doğru departmana yönlendirir.

Copilot özel ajanları ise yorumlama ve üretim katmanıdır. Projeyi gerçekten okuyup araştırma,
tasarım, kod, test veya belge değişikliği yapar ve pull request açar.

Bu ayrım, şirket otomasyonunun bir model hatası yüzünden kayıt veya görev kaybetmesini önler.
