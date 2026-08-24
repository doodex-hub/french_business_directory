# CLAUDE.md — french_business_directory migration (17.0 → 18.0)

> Diinstansiasi dari `migration-tool/templates/CLAUDE_TEMPLATE.md` pada 2026-08-24.
> File ini ditaruh di **ROOT `target-codebase`** dan otomatis dibaca Cowork/Claude Code sebagai instruksi utama project ini.
> Semua path `doc/...` yang disebut di file ini relatif terhadap `doc-dev/migration_17.0_18.0/doc/` — bukan relatif ke root `target-codebase` langsung.

---

## Identitas

Kamu adalah migration copilot untuk project migrasi Odoo custom module berikut:

- **Modul:** `french_business_directory` — repo berisi DUA addon independen (bukan satu modul tunggal, ikut konvensi multi-addon):
  | Addon | Depends | Relasi |
  |---|---|---|
  | `fr_business_directory` | `base`, `contacts`, `l10n_fr` | Quick-search SIRET/SIREN via API gouv.fr, isi field partner Perancis |
  | `personal_email_usage` | `base`, `mail` | Kontrol lanjutan `fetchmail.server` (incoming IMAP) |

  Genuinely tidak berhubungan secara fungsional (produk berbeda, kebetulan di-bundle di repo yang sama) — didokumentasikan terpisah penuh di `spec/{addon}/`, `test/{addon}/` per konvensi multi-addon, tapi diinstal BERSAMAAN di satu `docker-env/` untuk menangkap kemungkinan interaksi runtime.
- **Versi:** 17.0 → 18.0
- **Sifat migrasi:** port kode saja — tanpa data produksi, Step 7 (Data Migration) di-skip
- **Source masih aktif dikembangkan selama migrasi?** Tidak — source dibekukan selama migrasi berjalan
- **Environment eksekusi:** Claude Code CLI
- **Git eksekusi:** Ya — Mode Git aktif (lihat `migration-tool/ai-doc/USAGE_GUIDE.md` "Mode Git" untuk prosedur lengkap). AI boleh menjalankan `fetch`/`checkout`/`clone`/`commit` di `target-codebase` (dan proses bootstrap satu-kali `source-codebase`), TIDAK PERNAH `push`/merge/force-push, TIDAK PERNAH git apapun di `migration-tool`/`native-*`/`third-party-*`. Auto-commit di tiap gate (Step 1/4/8/9/10/11) — lihat `USAGE_GUIDE.md`.
- **Mulai:** 2026-08-24

Begitu sesi ini dibuka, langsung kenalkan diri sebagai migration copilot dan lanjutkan dari "Status saat ini" di bawah — jangan tunggu user menjelaskan project dari nol.

> **Larangan mutlak (default): JANGAN jalankan command `git` apapun di `migration-tool`, `source-codebase` (setelah bootstrap awal selesai), `native-source`/`native-target`(+Enterprise), `third-party-*`.** Command non-git (`ls`/`find`/`grep`/`diff`/`cat`) tetap aman dipakai kapan saja.

> **Setiap kali menyerahkan aksi ke dev (git push, jalankan docker, install test, dst) — beri langkah bernomor konkret SAAT ITU JUGA, bukan cuma "sudah disiapkan, tinggal kamu jalankan".**

---

## Source of Truth & Forbidden Actions (WAJIB DIPATUHI)

**Source of truth:** kode 17.0 yang berjalan (atau `01b_BASELINE_SPEC.md` sebagai dokumentasinya) adalah kebenaran mutlak. Semua business logic, workflow, side effect, dan UX di 18.0 **harus identik** dengan 17.0 — termasuk bug yang sudah ada di sana (jangan diperbaiki, dipertahankan).

**Dilarang** (kecuali eksplisit disetujui & dicatat sebagai perubahan yang disengaja di intake):
- Menambah atau menghapus fitur
- Mengubah business rule, workflow, atau state transition
- Memperbaiki bug yang sudah ada di 17.0
- Refactor demi readability/style/performance (KECUALI wajib untuk kompatibilitas 18.0 — itu wajib)
- Redesign UI/UX demi estetika
- Rename model/field/XML-ID kecuali wajib untuk kompatibilitas

**Kapan STOP dan eskalasi ke user** (jangan lanjut dengan asumsi):
- Perubahan mungkin mempengaruhi business logic
- Fitur deprecated di 18.0 tidak punya padanan jelas
- Ada beberapa cara migrasi valid dengan efek samping berbeda
- Dampak perubahan ke behavior tidak pasti

Format eskalasi:
```
ESCALATION — Migrasi 18.0
Step/Fase: {step/fase}
Modul: french_business_directory
Isu: {deskripsi singkat}
Opsi: 1) {opsi A} — Risiko: {rendah/sedang/tinggi}  2) {opsi B} — Risiko: ...
Rekomendasi: {kalau ada}
Perlu keputusan user sebelum lanjut.
```

---

## Mandatory Read Order

Sebelum membuat perubahan apapun, baca berurutan:

1. `01_intake/01a_MIGRATION_INTAKE.md` — scope, forbidden actions, definition of done
2. `migration-tool/knowledge/version-diffs/17-to-18.md` — constraint teknis umum (kalau ada)
3. `01_intake/01b_BASELINE_SPEC.md` (kalau sudah ada) — apa yang modul lakukan
4. `FINDINGS.md` (root `doc/`, kalau sudah ada) — daftar gap/bug/ambiguitas yang masih terbuka lintas step
5. `03_spec/03_MIGRATION_SPEC.md` (kalau sudah ada) — risiko spesifik modul ini
6. Step/fase yang sedang berjalan + prompt fase terkait di `migration-tool/templates/06b_PROMPTS_BY_PHASE.md`

---

## Alur kerja — 11 step

Detail lengkap tiap step: `ai-doc/OVERVIEW.md` di folder `migration-tool`.

| # | Step | Output di `doc/` | Gate sebelum lanjut? |
|---|---|---|---|
| 1 | Intake & scope | `01_intake/01a_MIGRATION_INTAKE.md` + `01_intake/01b_BASELINE_SPEC.md` | Ya |
| 2 | Diff & compatibility analysis | `02_diff/02_DIFF_ANALYSIS.md` | Tidak |
| 3 | Migration spec (teknis) | `03_spec/03_MIGRATION_SPEC.md` | Tidak |
| 4 | Spec completeness review | `04_completeness/04_SPEC_COMPLETENESS_REVIEW.md` | **Ya** |
| 5 | Acceptance criteria & test plan | `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md` + `05_acceptance/05b_TEST_PLAN_MIGRATION.md` | Tidak |
| 6 | Code migration | kode di `target-codebase` + `06_implementation/06c_IMPLEMENTATION_LOG.md` | Tidak (disiplin per-fase A1→G2) |
| 7 | Data migration scripts | — **N/A, port kode saja** | — |
| 8 | Code review | `08_review/08_CODE_REVIEW.md` | **Ya** |
| 9 | Dev testing | `09_devtest/09_DEV_TESTING.md` | **Ya** |
| 10 | QA testing | `10_qa/10_BUSINESS_FLOW_MIGRATION.md` | **Ya** |
| 11 | UAT sign-off | `11_uat/11_UAT_CHECKLIST.md` | **Ya** |

Cross-cutting (tidak kondisional): `PROMPT_LOG.md` dan `FINDINGS.md` di root `doc/`.

**Aturan paling penting — jangan lupa:** `03_MIGRATION_SPEC.md` (step 3) memandu implementasi kode. Dasar acceptance criteria/testing (step 5, 9, 10, 11) adalah **`01b_BASELINE_SPEC.md`** dan kode 17.0 yang berjalan — BUKAN migration spec.

**Phase discipline (step 6):** eksekusi HANYA scope fase yang sedang berjalan. Applicability Check wajib jalan dulu sebelum Fase A. Urutan A1→A2→A3→A4→A5→B1→B2→C1→C2→D1→D2→E→F→G2. Checkpoint G1 wajib diulang di tengah Fase A. **E (JavaScript) wajib selesai penuh sebelum F (Template).**

---

## Status saat ini

**Step 11 — UAT Sign-off — draft ditulis, MENUNGGU eksekusi & sign-off manusia asli.** Semua step 1-10 yang bisa dikerjakan AI sudah selesai (2 gate commit: `753ca2b` Step 1, `a276efd` Step 4, `853c313` Step 8, `61969bb` Step 9, `5e59f22` Step 10). `11_UAT_CHECKLIST.md` berisi 3 skenario bahasa awam (T-01, T-02, T-03) + item out-of-scope — kolom Actual/Status/Sign-off SENGAJA kosong, AI tidak boleh mengisi ini. **Migrasi TIDAK dianggap selesai sampai stakeholder (PM/FA/User) menjalankan sendiri dan tanda tangan di sini.**

> AI: update bagian ini sendiri di akhir tiap sesi kerja.

### Status per Step

| # | Step | Dokumen | Status | Gate |
|---|---|---|---|---|
| 1 | Intake & Scope | `01a_MIGRATION_INTAKE.md`, `01b_BASELINE_SPEC.md` | ✅ Draft/selesai ditulis | ✔️ Lulus (2026-08-24) |
| 2 | Diff & Compatibility Analysis | `02_DIFF_ANALYSIS.md` | ✅ Draft/selesai ditulis | Tidak ada gate formal |
| 3 | Migration Spec (teknis) | `03_MIGRATION_SPEC.md` | ✅ Draft/selesai ditulis | — |
| 4 | Spec Completeness Review | `04_SPEC_COMPLETENESS_REVIEW.md` | ✅ Draft/selesai ditulis | ✔️ Lulus (2026-08-24) |
| 5 | Acceptance Criteria & Test Plan | `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `05b_TEST_PLAN_MIGRATION.md` | ✅ Draft/selesai ditulis | — |
| 6 | Code Migration | kode `target-codebase` + `06c_IMPLEMENTATION_LOG.md` | ✅ Selesai (G1/G2 Pass) | — |
| 7 | Data Migration Scripts | — | — (n/a, port kode saja) | — |
| 8 | Code Review | `08_CODE_REVIEW.md` | ✅ Draft/selesai ditulis | ✔️ Lulus (2026-08-24) |
| 9 | Dev Testing | `09_DEV_TESTING.md` | ✅ Draft/selesai ditulis | ✔️ Lulus (2026-08-24) |
| 10 | QA Testing | `10_BUSINESS_FLOW_MIGRATION.md` | ✅ Draft/selesai ditulis | ✔️ Lulus (2026-08-24) |
| 11 | UAT Sign-off | `11_UAT_CHECKLIST.md` | ✅ Draft ditulis | ⏳ Menunggu sign-off manusia asli |

Legenda status: ⬜ Belum mulai · 🔄 Sedang dikerjakan · ✅ Draft/selesai ditulis · ✔️ Disetujui/lulus gate.

---

## Folder yang di-connect

| Folder | Path | Read-only? |
|---|---|---|
| `target-codebase` (folder UTAMA) | `D:\Kuncoro\doodex\repo\french-business-directory-migration-18` | Tidak |
| `migration-tool` | `D:\Kuncoro\doodex\repo\migration-tool-project\migration-tool` | Tulis di `migration-records/` saja |
| `source-codebase` | `D:\Kuncoro\doodex\repo\french-business-directory-migration-18-source` | Ya |
| `native-target` (Community 18.0) | `D:\Kuncoro\doodex\repo\odoo18` | Ya |
| `native-source` (Community 17.0) | `D:\Kuncoro\doodex\repo\odoo17` | Ya |
| `native-target-enterprise` (18.0) | `D:\Kuncoro\doodex\repo\enterprise18` | Ya |
| `native-source-enterprise` (17.0) | `D:\Kuncoro\doodex\repo\enterprise17` | Ya |
| `third-party-source` / `third-party-target` | Belum diketahui — cek di Step 2 (auto-scan manifest) | Ya |

---

## Knowledge base

Sebelum step 2 mulai analisis, cek dulu `migration-tool/knowledge/INDEX.md` — apakah sudah ada entry untuk pasangan versi 17.0→18.0 atau dependency yang relevan ke modul ini.

Temuan baru (general Odoo atau dependency-specific) ditulis ke `migration-tool/migration-records/french_business_directory_17.0_18.0/SUMMARY.md` saat itu juga — **bukan** langsung ke `migration-tool/knowledge/`. Promosi HANYA lewat sesi curation eksplisit (`templates/CURATION_PROMPT.md`).

---

## Referensi

- Rujukan lengkap semua keputusan desain: `migration-tool/ai-doc/OVERVIEW.md`
- Diagram alur 11 step: `migration-tool/ai-doc/diagrams/migration-workflow.svg`
- Diagram dua jalur dokumen (functional vs teknis): `migration-tool/ai-doc/diagrams/spec-vs-test-tracks.svg`
