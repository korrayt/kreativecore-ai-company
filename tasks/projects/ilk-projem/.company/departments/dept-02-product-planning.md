```markdown
# [DEPT] OC — Yerel-First Kişisel AI Çalışma Alanı — Ürün ve Planlama

## Project

`tasks/projects/ilk-projem`

## Department

**Ürün ve Planlama**

Routing score: 52  
Routing reasons: company-core, fiyatlandırma, kullanıcı, product, prototip, type:ai, ui, ürün

## Mission

Review the project from this department's perspective. Produce the department-specific plan,
required inputs, dependencies, acceptance criteria, risks and the smallest next executable
task. Do not implement unrelated departments' work.

## Local AI execution

- Custom agent: `dept-02-product-planning`
- Priority: `P1`
- Auto execute requested: `false`
- Owner approval required: `true`
- Mode: Founder approval required before local AI execution.

Mobile action: use **Actions → Mobile Company Control** and select agent `dept-02-product-planning`.

## Source fingerprint

`174848a361d730ce`

## Project Context

===== FILE: tasks/projects/ilk-projem/.company/PROJECT_STATE.json =====
{
  "kind": "project",
  "slug": "ilk-projem",
  "name": "OC — Yerel-First Kişisel AI Çalışma Alanı",
  "path": "tasks/projects/ilk-projem",
  "objective": "Kullanıcının projelerini, dosyalarını, fikirlerini ve görevlerini tek bir masaüstü çalışma alanında yöneten; internet bağlantısı olmasa da temel işlevlerini sürdürebilen; yerel yapay zekâ modelleriyle çalışan güvenli ve modüler bir kişisel AI sistemi geliştirmek.",
  "desired_outcome": "Windows üzerinde çalışan kurulum yapılabilir bir masaüstü uygulaması; yerel model bağlantısı, proje hafızası, dosya okuma, görev planlama, izin kontrollü araç kullanımı ve açık hata davranışına sahip çalışan bir MVP.",
  "type": "ai",
  "priority": "P1",
  "stage": "discovery",
  "owner": "@korrayt",
  "auto_execute": false,
  "owner_approval": true,
  "manifest_present": true,
  "manifest_parse_error": null,
  "source_hash": "174848a361d730ce",
  "file_count": 2,
  "files": [
    "BRIEF.md",
    "PROJECT.toml"
  ],
  "departments": [
    {
      "id": "technology-software",
      "name": "Yazılım ve Teknoloji",
      "agent": "dept-03-technology-software",
      "score": 68,
      "reasons": [
        "api",
        "architecture",
        "desktop",
        "github",
        "masaüstü",
        "mimari",
        "mobil",
        "platform",
        "react",
        "rust",
        "tauri",
        "type:ai",
        "typescript"
      ]
    },
    {
      "id": "product-planning",
      "name": "Ürün ve Planlama",
      "agent": "dept
