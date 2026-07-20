# Görev ve Proje Girişi

## Proje klasörü

`tasks/projects/` altındaki `_` veya `.` ile başlamayan her klasör projedir.

Önerilen yapı:

```text
tasks/projects/proje-slug/
├── PROJECT.toml
├── BRIEF.md
└── input/
```

Projeye ait kod, belge, görsel, araştırma veya eski ZIP dosyaları `input/` altına konabilir.
Sistem `.company/` klasörünü kendisi üretir; burayı elle düzenlemek gerekmez.

## Tek görev

Önerilen yapı:

```text
tasks/inbox/gorev-slug/
├── TASK.toml
├── REQUEST.md
└── attachments/
```

Basit görevler için doğrudan `tasks/inbox/gorev-adi.md` dosyası da kullanılabilir.

## Durum dosyaları

Otomasyon şunları üretir:

- `tasks/.company/PORTFOLIO.md`
- `tasks/.company/QUEUE.md`
- `tasks/.company/registry.json`
- proje içinde `.company/ANALYSIS.md`
- proje içinde `.company/ROADMAP.md`
- proje içinde `.company/DEPARTMENT_PLAN.md`
- görev içinde `.company/ROUTING.md`

Üretilen dosyalar şirket hafızasıdır.
