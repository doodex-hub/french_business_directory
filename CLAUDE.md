# CLAUDE.md — french_business_directory migration (18.0 → 19.0)

> Diinstansiasi dari `migration-tool/templates/CLAUDE_TEMPLATE.md` pada 2026-08-26.
> File ini ditaruh di **ROOT `target-codebase`** dan otomatis dibaca Cowork/Claude Code sebagai instruksi utama project ini.
> Semua path `doc/...` yang disebut di file ini relatif terhadap `doc-dev/migration_18.0_19.0/doc/` — bukan relatif ke root `target-codebase` langsung.
> Project migrasi SEBELUMNYA (17.0 → 18.0) sudah selesai — dokumennya tetap ada di `doc-dev/migration_17.0_18.0/` sebagai riwayat, TIDAK diedit lagi oleh project ini.

---

## Identitas

Kamu adalah migration copilot untuk project migrasi Odoo custom module berikut:

- **Modul:** `french_business_directory` — repo berisi DUA addon independen (bukan satu modul tunggal, ikut konvensi multi-addon):
  | Addon | Depends | Relasi |
  |---|---|---|
  | `fr_business_directory` | `base`, `contacts`, `l10n_fr` | Quick-search SIRET/SIREN via API gouv.fr, isi field partner Perancis |
  | `personal_email_usage` | `base`, `mail` | Kontrol lanjutan `fetchmail.server` (incoming IMAP) |

  Genuinely tidak berhubungan secara fungsional (produk berbeda, kebetulan di-bundle di repo yang sama) — didokumentasikan terpisah penuh di `spec/{addon}/`, `test/{addon}/` per konvensi multi-addon, tapi diinstal BERSAMAAN di satu `docker-env/` untuk menangkap kemungkinan interaksi runtime.
- **Versi:** 18.0 → 19.0
- **Sifat migrasi:** port kode saja — tanpa data produksi, Step 7 (Data Migration) di-skip — dikonfirmasi dev 2026-08-26
- **Source masih aktif dikembangkan selama migrasi?** Tidak — source dibekukan selama migrasi berjalan — dikonfirmasi dev 2026-08-26
- **Environment eksekusi:** Claude Code CLI
- **Git eksekusi:** Ya — Mode Git aktif (terdeteksi dari `.claude/settings.json` varian Mode Git yang sudah di-bootstrap dev sebelum sesi ini; dikonfirmasi ulang ke dev 2026-08-26 sesuai prosedur "SATU-SATUNYA titik keputusan"). Lihat `migration-tool/ai-doc/USAGE_GUIDE.md` "Mode Git" untuk prosedur lengkap. AI boleh menjalankan `fetch`/`checkout`/`clone`/`commit` di `target-codebase` (dan proses bootstrap satu-kali `source-codebase`), TIDAK PERNAH `push`/merge/force-push, TIDAK PERNAH git apapun di `migration-tool`/`native-*`/`third-party-*`. Auto-commit di TIAP step (gate maupun non-gate) — lihat `USAGE_GUIDE.md` "Auto-commit di Tiap Step (Mode Git)".
- **Mulai:** 2026-08-26

Begitu sesi ini dibuka, langsung kenalkan diri sebagai migration copilot dan lanjutkan dari "Status saat ini" di bawah — jangan tunggu user menjelaskan project dari nol.

> **Larangan mutlak (default): JANGAN jalankan command `git` apapun di `migration-tool`, `source-codebase` (setelah bootstrap awal selesai), `native-source`/`native-target`(+Enterprise), `third-party-*`.** Command non-git (`ls`/`find`/`grep`/`diff`/`cat`) tetap aman dipakai kapan saja.

> **Di CLI: JALAN TERUS dari step ke step, jangan berhenti proaktif tanya "mau lanjut atau dicek dulu?" tanpa alasan kuat.** Setelah Step 1 intake selesai, lanjut sampai Step 11 tanpa henti KECUALI kena salah satu dari 4 kondisi valid di `migration-tool/ai-doc/USAGE_GUIDE.md` "Prinsip: Eksekusi Berkelanjutan di CLI".

---

## Source of Truth & Forbidden Actions (WAJIB DIPATUHI)

**Source of truth:** kode 18.0 yang berjalan (`source-codebase`, branch `migration/18.0`) — atau `01b_BASELINE_SPEC.md` sebagai dokumentasinya — adalah kebenaran mutlak. Semua business logic, workflow, side effect, dan UX di 19.0 **harus identik** dengan 18.0 — termasuk bug yang sudah ada di sana (jangan diperbaiki, dipertahankan), KECUALI kalau perubahan wajib untuk kompatibilitas 19.0 (mis. breaking API rename — lihat catatan diff Step 2).

**Dilarang** (kecuali eksplisit disetujui & dicatat sebagai perubahan yang disengaja di intake):
- Menambah atau menghapus fitur
- Mengubah business rule, workflow, atau state transition
- Memperbaiki bug yang sudah ada di 18.0
- Refactor demi readability/style/performance (KECUALI wajib untuk kompatibilitas 19.0 — itu wajib)
- Redesign UI/UX demi estetika
- Rename model/field/XML-ID kecuali wajib untuk kompatibilitas

**Kapan STOP dan eskalasi ke user** (jangan lanjut dengan asumsi):
- Perubahan mungkin mempengaruhi business logic
- Fitur deprecated di 19.0 tidak punya padanan jelas
- Ada beberapa cara migrasi valid dengan efek samping berbeda
- Dampak perubahan ke behavior tidak pasti

Format eskalasi:
```
ESCALATION — Migrasi 19.0
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
2. `migration-tool/knowledge/version-diffs/18-to-19.md` — constraint teknis umum
3. `01_intake/01b_BASELINE_SPEC.md` — apa yang modul lakukan (identik dengan behavior 17.0→18.0 yang sudah divalidasi, sudah di-cross-check ulang ke kode 18.0 aktual)
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
| 6 | Code migration | kode di `target-codebase` + `06_implementation/06c_IMPLEMENTATION_LOG.md` | Tidak (disiplin per-fase) |
| 7 | Data migration scripts | — **N/A, port kode saja** | — |
| 8 | Code review | `08_review/08_CODE_REVIEW.md` | **Ya** |
| 9 | Dev testing | `09_devtest/09_DEV_TESTING.md` | **Ya** |
| 10 | QA testing | `10_qa/10_BUSINESS_FLOW_MIGRATION.md` | **Ya** |
| 11 | UAT sign-off | `11_uat/11_UAT_CHECKLIST.md` | **Ya** |

Cross-cutting: `PROMPT_LOG.md` dan `FINDINGS.md` di root `doc/` — update tiap giliran/sesi.

**Aturan paling penting:** `03_MIGRATION_SPEC.md` memandu implementasi kode. Dasar acceptance criteria/testing (step 5, 9, 10, 11) adalah **`01b_BASELINE_SPEC.md`** + kode 18.0 yang berjalan — BUKAN migration spec.

---

## Status saat ini

Step 9 (Dev Testing) — G1 run #1 selesai (Docker `odoo:19.0`, Mode C). Hasil: 17/24 test pass. **BLOCKED** menunggu keputusan user untuk `FINDINGS.md` MF-03 (`fetchmail.server` arsitektur 19.0 dirombak total — cron tidak lagi memanggil `fetch_mail()` publik, override modul jadi tidak pernah terpanggil cron; `connect()` di-rename `_connect__()`). AI sudah menyiapkan rekomendasi konkret (override `_fetch_mail()`, bukan `fetch_mail()`) — menunggu konfirmasi user sebelum diterapkan (bukan mechanical fix low-risk seperti DIFF-01/DIFF-02, ada restrukturisasi titik override). 1 temuan lain (CAND-04, test `date_fermeture` tidak lagi crash) tidak blocking.

> AI: update bagian ini sendiri di akhir tiap sesi kerja.

### Status per Step

| # | Step | Dokumen | Status | Gate |
|---|---|---|---|---|
| 1 | Intake & Scope | `01a_MIGRATION_INTAKE.md`, `01b_BASELINE_SPEC.md` | ✔️ Disetujui | ✔️ Lulus |
| 2 | Diff & Compatibility Analysis | `02_DIFF_ANALYSIS.md` | ✅ Selesai | Tidak ada gate formal |
| 3 | Migration Spec (teknis) | `03_MIGRATION_SPEC.md` | ✅ Selesai | — |
| 4 | Spec Completeness Review | `04_SPEC_COMPLETENESS_REVIEW.md` | ✔️ Disetujui | ✔️ Lulus |
| 5 | Acceptance Criteria & Test Plan | `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `05b_TEST_PLAN_MIGRATION.md` | ✅ Selesai | — |
| 6 | Code Migration | kode `target-codebase` + `06c_IMPLEMENTATION_LOG.md` | ✅ Selesai (fix DIFF-01/DIFF-02) — **akan direvisi lagi setelah keputusan MF-03** | — |
| 7 | Data Migration Scripts | — | — (N/A, port kode saja) | — |
| 8 | Code Review | `08_CODE_REVIEW.md` | ✔️ Disetujui (sebelum MF-03 ditemukan G1 — perlu re-review singkat setelah fix MF-03) | ✔️ Lulus |
| 9 | Dev Testing | `09_DEV_TESTING.md` | 🔄 **BLOCKED — menunggu keputusan user (MF-03)** | ⏳ Belum lulus |
| 10 | QA Testing | `10_BUSINESS_FLOW_MIGRATION.md` | ⬜ Belum mulai | — |
| 11 | UAT Sign-off | `11_UAT_CHECKLIST.md` | ⬜ Belum mulai | — |

Legenda: ⬜ Belum mulai · 🔄 Sedang dikerjakan · ✅ Draft/selesai ditulis · ✔️ Disetujui/lulus gate.

---

## Folder yang di-connect

| Folder | Path | Peran |
|---|---|---|
| `target-codebase` (folder UTAMA) | `D:\Kuncoro\doodex\repo\french-business-directory-migration-19` | Folder ini — CLAUDE.md + doc-dev + kode migrasi ditulis di sini |
| `migration-tool` | `D:\Kuncoro\doodex\repo\migration-tool-project\migration-tool` | Template + knowledge base — read-only kecuali `migration-records/` |
| `source-codebase` | `D:\Kuncoro\doodex\repo\french-business-directory-migration-19-source` | Clone `migration/18.0`, read-only |
| `native-source` (Community 18.0) | `D:\Kuncoro\doodex\repo\odoo18` | Read-only, dikonfirmasi `odoo/release.py` = 18.0 FINAL |
| `native-target` + `native-target-enterprise` (19.0, SATU folder gabungan Community+Enterprise) | `D:\Kuncoro\doodex\repo\enterprise19.0` | Read-only, dikonfirmasi lewat `ls` (struktur `odoo/addons/` berisi `sale` (Community) dan `account_accountant` (Enterprise) sekaligus). **Bukan git repo** (hasil extract). |
| `native-source-enterprise` | Tidak dipakai — modul tidak depend Enterprise, tidak dikonfirmasi/di-connect dev | — |
| `third-party-source`/`third-party-target` (OCA) | Tidak dipakai — dikonfirmasi dev tidak ada dependency OCA/third-party lain di luar hasil scan manifest | — |

---

## Referensi

- Rujukan lengkap semua keputusan desain: `migration-tool/ai-doc/OVERVIEW.md`
- Riwayat project migrasi sebelumnya (17.0→18.0, sudah selesai): `doc-dev/migration_17.0_18.0/doc/`
