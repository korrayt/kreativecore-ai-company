# Kreative Core — Autonomous Company OS

Bu repo, yeni fikirleri yalnızca saklayan bir arşiv değil; onları proje ve iş akışına dönüştüren
bir şirket sistemi olarak çalışır.

## Yeni proje eklemek

En kolay yol:

```text
tasks/projects/proje-adi/
├── PROJECT.toml
├── BRIEF.md
└── input/
    └── elindeki-dosyalar
```

`PROJECT.toml` yoksa klasör yine proje olarak algılanır. Sistem ilk analiz issue'sunu açar ve
hangi bilgilerin eksik olduğunu gösterir.

## Yeni görev eklemek

```text
tasks/inbox/gorev-adi/
├── TASK.toml
├── REQUEST.md
└── attachments/
```

Tek bir `.md` dosyası da doğrudan `tasks/inbox/` içine bırakılabilir.

## Günlük akış

Her gün Türkiye saatiyle yaklaşık 08:00'de:

1. Yeni proje ve görevler bulunur.
2. Portföy kaydı güncellenir.
3. İlk analiz ve yol haritası dosyaları oluşturulur.
4. Gerekli departmanlar belirlenir.
5. GitHub issue'ları açılır.
6. Uygun özel ajan adı issue içine yazılır.
7. Otomatik çalışma açıksa ve güvenli token mevcutsa Copilot göreve atanır.
8. Aksi halde mobilde issue içinden Copilot ve özel ajan seçilir.

## Şirketin iki çalışma modu

### Güvenli varsayılan

Planlama ve yönlendirme tamamen otomatik; kod ajanına görev verme kurucu onaylıdır.

### Tam otomatik

Projede veya görevde `auto_execute = true` yazılır ve repo secret'ına
`LOCAL_AI_ENGINE` eklenir. Hassas departmanlar yine kurucu onayı olmadan otomatik
çalıştırılmaz.
