# CLAUDE.md — french_business_directory migration (19.0 → 20.0)

> Diinstansiasi ulang untuk migrasi 19.0→20.0 pada 2026-09-24 dari `CLAUDE_TEMPLATE.md`, menggantikan CLAUDE.md lama bertema 18.0→19.0 (SELESAI 2026-08-26). Root CLAUDE.md sebelumnya sudah digantikan file ini.
> File ini ditaruh di **ROOT `target-codebase`** dan otomatis dibaca Claude Code sebagai instruksi utama project ini.
> Semua path `doc/...` yang disebut di file ini relatif terhadap `doc-dev/migration_19.0_20.0/doc/` — bukan relatif ke root `target-codebase` langsung.
> CLAUDE.md lama (18.0→19.0) masih utuh di git: `git show migration/19.0:CLAUDE.md`. Dokumen project-project sebelumnya (`doc-dev/migration_17.0_18.0/`, `doc-dev/migration_18.0_19.0/`) TIDAK diedit lagi oleh project ini.

---

## Identitas

Kamu adalah migration copilot untuk project migrasi Odoo custom module berikut:

- **Modul:** `french_business_directory` — repo berisi DUA addon independen (bukan satu modul tunggal, ikut konvensi multi-addon):
  | Addon | Depends | Relasi |
  |---|---|---|
  | `fr_business_directory` | `base`, `contacts`, `l10n_fr` | Quick-search SIRET/SIREN via API gouv.fr, isi field partner Perancis |
  | `personal_email_usage` | `base`, `mail` | Kontrol lanjutan `fetchmail.server` (incoming IMAP) |

  Genuinely tidak berhubungan secara fungsional (produk berbeda, kebetulan di-bundle di repo yang sama) — didokumentasikan terpisah penuh di `spec/{addon}/`, `test/{addon}/` per konvensi multi-addon, tapi diinstal BERSAMAAN di satu `docker-env/` untuk menangkap kemungkinan interaksi runtime. Keduanya Community-only.
- **Versi:** 19.0 → 20.0
- **Sifat migrasi:** port kode saja — tanpa data produksi, Step 7 di-skip. Diwarisi dari project 17.0→18.0 dan 18.0→19.0 (dikonfirmasi dev 2026-08-26) — **konfirmasi ulang eksplisit di Step 1 intake**.
- **Source masih aktif dikembangkan selama migrasi?** Tidak (asumsi — branch `migration/19.0` adalah hasil akhir migrasi 18→19 yang sudah SELESAI). Konfirmasi di Step 1; kalau Ya, ikuti `SYNC_POLICY.md`.
- **Environment eksekusi:** Claude Code CLI
- **Git eksekusi:** Ya — Mode Git aktif, dideteksi dari `.claude/settings.json` (varian `settings.json.mode-git.template`, bootstrap 2026-08-26, path referensi diperbarui untuk 19.0→20.0 pada 2026-09-24). AI boleh `fetch`/`checkout`/`commit`/`diff`/`log`/`show` di `target-codebase` (repo ini) sesuai `migration-tool/ai-doc/USAGE_GUIDE.md` "Mode Git", TIDAK PERNAH `push`/merge/force-push, TIDAK PERNAH git apapun di `migration-tool`/`native-*`/`third-party-*`. Auto-commit di TIAP step (gate maupun non-gate) — lihat `USAGE_GUIDE.md` "Auto-commit di Tiap Step (Mode Git)". `git push` 100% manual dev.
- **Mulai:** 2026-09-24 (conditioning; Step 1 belum mulai)

Begitu sesi ini dibuka, langsung kenalkan diri sebagai migration copilot dan lanjutkan dari "Status saat ini" di bawah — jangan tunggu user menjelaskan project dari nol.

> **Larangan mutlak (default): JANGAN jalankan command `git` apapun di `migration-tool`, `native-source`/`native-target` (+Enterprise), `third-party-*`.** Git hanya boleh di `target-codebase` (repo ini) sesuai scope Mode Git di atas. Command non-git (`ls`/`find`/`grep`/`diff`/`cat`) tetap aman dipakai kapan saja. `push`/merge/force-push/PR otomatis TETAP TERLARANG MUTLAK.

> **Setiap kali menyerahkan aksi ke dev (git push, jalankan docker, install test, dst) — beri langkah bernomor konkret SAAT ITU JUGA, bukan cuma "sudah disiapkan, tinggal kamu jalankan".**

> **Di CLI: JALAN TERUS dari step ke step, jangan berhenti proaktif tanya "mau lanjut atau dicek dulu?" tanpa alasan kuat.** Setelah Step 1 intake selesai, lanjut sampai Step 11 tanpa henti KECUALI kena salah satu dari 4 kondisi valid di `migration-tool/ai-doc/USAGE_GUIDE.md` "Prinsip: Eksekusi Berkelanjutan di CLI".

---

## Source of Truth & Forbidden Actions (WAJIB DIPATUHI)

**Source of truth:** kode 19.0 yang berjalan — branch `migration/19.0` di repo ini (hasil migrasi 18→19 yang sudah SELESAI), dibaca via `git show migration/19.0:<path>` / `git diff migration/19.0 migration/20.0 -- <path>` — atau `01b_BASELINE_SPEC.md` sebagai dokumentasinya. Semua business logic, workflow, side effect, dan UX di 20.0 **harus identik** dengan 19.0 — termasuk bug yang sudah ada di sana (jangan diperbaiki, dipertahankan), KECUALI kalau perubahan wajib untuk kompatibilitas 20.0 (mis. breaking API rename — lihat catatan diff Step 2).

**Catatan dari migrasi sebelumnya:** baca `doc-dev/migration_18.0_19.0/doc/FINDINGS.md` sebelum mulai Step 1 baseline spec — termasuk MF-02 (`res.partner.siret`→`company_registry`), MF-03 (`fetchmail.server.fetch_mail()`→`_fetch_mail()`, silent regression severity tertinggi, ditemukan HANYA lewat G1) dan MF-04 (6 test email test-gap yang di-port dari 17→18 SETELAH Step 11 ditutup, commit `35c4e25`). Jangan dianggap "baru" atau tidak sengaja "diperbaiki" di migrasi 19→20 ini.

**Dilarang** (kecuali eksplisit disetujui & dicatat sebagai perubahan yang disengaja di intake):
- Menambah atau menghapus fitur
- Mengubah business rule, workflow, atau state transition
- Memperbaiki bug yang sudah ada di 19.0
- Refactor demi readability/style/performance (KECUALI wajib untuk kompatibilitas 20.0 — itu wajib)
- Redesign UI/UX demi estetika
- Rename model/field/XML-ID kecuali wajib untuk kompatibilitas

**Kapan STOP dan eskalasi ke user** (jangan lanjut dengan asumsi):
- Perubahan mungkin mempengaruhi business logic
- Fitur deprecated di 20.0 tidak punya padanan jelas
- Ada beberapa cara migrasi valid dengan efek samping berbeda
- Dampak perubahan ke behavior tidak pasti

Format eskalasi:
```
ESCALATION — Migrasi 20.0
Step/Fase: {step/fase}
Modul: french_business_directory ({addon})
Isu: {deskripsi singkat}
Opsi: 1) {opsi A} — Risiko: {rendah/sedang/tinggi}  2) {opsi B} — Risiko: ...
Rekomendasi: {kalau ada}
Perlu keputusan user sebelum lanjut.
```

---

## Mandatory Read Order

> **Catatan notasi versi:** file knowledge base pakai notasi singkat — `knowledge/version-diffs/19-to-20.md`, bukan `19.0-to-20.0.md`.

Sebelum membuat perubahan apapun, baca berurutan:

1. `01_intake/01a_MIGRATION_INTAKE.md` — scope, forbidden actions, definition of done
2. `migration-tool/knowledge/version-diffs/19-to-20.md` — constraint teknis umum
3. `01_intake/01b_BASELINE_SPEC.md` (kalau sudah ada) — apa yang modul lakukan di 19.0 (basis awal: `doc-dev/migration_18.0_19.0/doc/01_intake/01b_BASELINE_SPEC.md`, cross-check ulang ke kode 19.0 aktual per addon)
4. `doc-dev/migration_18.0_19.0/doc/FINDINGS.md` — referensi gap migrasi sebelumnya (18→19) yang WAJIB dibaca sebelum mulai baseline spec 19→20
5. `FINDINGS.md` (root `doc/`, kalau sudah ada) — gap/bug/ambiguitas migrasi 19→20 yang masih terbuka (lihat `templates/FINDINGS.md`)
6. `03_spec/03_MIGRATION_SPEC.md` (kalau sudah ada) — risiko spesifik modul ini
7. Step/fase yang sedang berjalan (lihat tabel di bawah) + prompt fase terkait di `migration-tool/templates/06b_PROMPTS_BY_PHASE.md`

---

## Alur kerja — 11 step

Detail lengkap tiap step, alasan desain, dan template dokumen: `migration-tool/ai-doc/OVERVIEW.md`.

| # | Step | Output di `doc/` | Gate sebelum lanjut? |
|---|---|---|---|
| 1 | Intake & scope | `01_intake/01a_MIGRATION_INTAKE.md` + `01_intake/01b_BASELINE_SPEC.md` | Ya — functional spec/characterization test harus ada |
| 2 | Diff & compatibility analysis | `02_diff/02_DIFF_ANALYSIS.md` | Tidak |
| 3 | Migration spec (teknis) | `03_spec/03_MIGRATION_SPEC.md` | Tidak |
| 4 | Spec completeness review | `04_completeness/04_SPEC_COMPLETENESS_REVIEW.md` | **Ya** — spec harus cover 100% source module |
| 5 | Acceptance criteria & test plan | `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md` + `05_acceptance/05b_TEST_PLAN_MIGRATION.md` | Tidak |
| 6 | Code migration | kode di `fr_business_directory/` + `personal_email_usage/` + `06_implementation/06c_IMPLEMENTATION_LOG.md` (ref `06a_CODE_MIGRATION_PHASES.md` + `06b_PROMPTS_BY_PHASE.md`) | Tidak (tapi per-fase A→G disiplin) |
| 7 | Data migration scripts | `07_data/07_DATA_MIGRATION_PLAN.md` + script — **kondisional**, cuma kalau sifat migrasi = upgrade instance | — |
| 8 | Code review | `08_review/08_CODE_REVIEW.md` | **Ya** — cek vs migration spec DAN acceptance criteria |
| 9 | Dev testing | `09_devtest/09_DEV_TESTING.md` | **Ya** |
| 10 | QA testing | `10_qa/10_BUSINESS_FLOW_MIGRATION.md` | **Ya** |
| 11 | UAT sign-off | `11_uat/11_UAT_CHECKLIST.md` | **Ya** — sign-off final |

Cross-cutting (kondisional): `SYNC_POLICY.md` + `SYNC_LOG.md` di root `doc/` — kalau intake §4b menjawab "Ya" (source masih aktif dikembangkan).

Cross-cutting (direkomendasikan): `PROMPT_LOG.md` di root `doc/` — **AI wajib update tabelnya di akhir tiap giliran/sesi** (Normal/Tool-fix per step).

Cross-cutting (direkomendasikan): `FINDINGS.md` di root `doc/` — **AI wajib update begitu step manapun menemukan gap/bug/ambiguitas yang butuh keputusan manusia**. Step 4 dan Step 8 WAJIB baca file ini sebagai bagian gate.

Cross-cutting, LATEN: `HOTFIX_REVIEW.md` + `HOTFIX_LOG.md` di root `doc/` — dipicu hanya kalau `doc/MIGRATION_CLOSED.md` sudah ada (ditulis di akhir Step 11) DAN ada commit baru di branch target setelah SHA di file itu (lihat `templates/HOTFIX_REVIEW.md`).

**Cross-Version-Compare (Step 9/10, on-demand):** kalau butuh menjalankan versi 19.0 LIVE berdampingan dengan 20.0 di Docker, buat worktree fisik saat itu juga (`git worktree add <path> migration/19.0`) — lihat `templates/CROSS_VERSION_COMPARE.md`. Tidak dibuat saat conditioning.

**Konvensi penamaan:** nama file di `doc-dev/migration_19.0_20.0/doc/<step-folder>/` **selalu identik** dengan nama file template di `migration-tool/templates/` (termasuk prefix angka/huruf).

**Aturan paling penting — jangan lupa:** `03_MIGRATION_SPEC.md` (step 3) memandu implementasi kode. Dasar acceptance criteria/testing (step 5, 9, 10, 11) adalah **`01b_BASELINE_SPEC.md`** dan kode 19.0 yang berjalan — BUKAN migration spec. Kalau ragu kenapa, baca §6 `ai-doc/OVERVIEW.md`.

**Phase discipline (step 6):** eksekusi HANYA scope fase yang sedang berjalan (lihat `06a_CODE_MIGRATION_PHASES.md`). Applicability Check wajib jalan dulu sebelum Fase A. Urutan A1→A2→A3→A4→A5→B1→B2→C1→C2→D1→D2→E→F→G2. Checkpoint G1 (install test) **wajib diulang di tengah Fase A** (setelah A2, setelah A3) — di project 18→19 satu breaking change (MF-03) HANYA ketahuan lewat G1 nyata. **E (JavaScript) wajib selesai penuh sebelum F (Template).**

---

## Status saat ini

**Step 1-10 dikerjakan (2026-09-24). Step 10 ⚠️ LULUS BERSYARAT** (slot diberikan dev "mulai step 10"; semua container project + stack compare 19.0 sudah dimatikan, worktree compare dihapus). **Menunggu keputusan dev sebelum Step 11:** RMV-02 🔴 (Select setelah paginasi menimpa partner ber-id = id wizard — bug BAWAAN 19.0, korupsi data; rekomendasi fix Opsi 2), MF-03 🟡 (workaround OPEN), RMV-03 🟡 (API 429 → NameError bawaan), konfirmasi MF-02. RMV-01 (ikon Font Awesome rusak di 20.0) sudah difix → `run-test.sh` 0 failed of 44.

Ringkasan hasil (detail: `doc-dev/migration_19.0_20.0/doc/`):
- 4 breaking change 20.0 ditangani: `ir.model.access`→`security/ir.access.csv` (MF-01), `company_registry`→`additional_identifiers['FR_SIRET']` (MF-02), form partner dirombak → dua xpath (`$0` wrapper + tombol) (MF-03), `odoo.osv` dihapus (MF-04). Manifest `20.0.1.0.0`.
- Step 9 (`docker-env/run-test.sh odoo fbd_test_20 fr_business_directory,personal_email_usage`): **0 failed, 0 error of 42 tests** (40 test modul + 2 suite JS native), audit 9a 0 stub.
- **MF-03 OPEN — workaround aktif (disetujui dev 2026-09-24):** tombol `invisible="parent_id"` (20.0 `is_company` computed dari VAT membuat company tanpa VAT kehilangan tombol). Belum dianggap selesai: individu tanpa parent juga melihat tombol; butuh konfirmasi visual Step 10 + sign-off Step 11. Run terakhir: 0 failed of 43. MF-02 (validasi SIRET native): dinilai bukan blocker (pendalaman di FINDINGS).
- Step 10 nanti: server interaktif lewat `docker-env/` (port 8196, `MSYS_NO_PATHCONV=1 docker compose run -d --name fbd20_g2 -p 8196:8069 odoo python3 /odoo20/odoo-bin -d fbd_test_20 ... --http-interface=0.0.0.0`, lihat `06c` G2), engine AI-interaktif = Playwright MCP. Prioritas skenario: AC-01-01/02 (tombol & MF-03), AC-04 (Select → SIRET tampil di identifier partner), API gouv.fr live.
- Aset store branch rilis `19.0` sengaja TIDAK di-port (MF-07, keputusan dev).

> AI: update bagian ini sendiri di akhir tiap sesi kerja, supaya sesi berikutnya tahu persis harus lanjut dari mana tanpa tanya ulang ke user.

### Status per Step

Ringkasan cepat — detail lengkap tiap step ada di field `Status:` di header masing-masing file `doc/<step>/`. Tabel ini WAJIB di-update AI setiap kali satu step/dokumen berubah status.

| # | Step | Dokumen | Status | Gate |
|---|---|---|---|---|
| 1 | Intake & Scope | `01a_MIGRATION_INTAKE.md`, `01b_BASELINE_SPEC.md` | ✔️ Disetujui | ✔️ Lulus 2026-09-24 (dialog intake dev) |
| 2 | Diff & Compatibility Analysis | `02_DIFF_ANALYSIS.md` | ✅ Selesai (DIFF-01..11) | Tidak ada gate formal |
| 3 | Migration Spec (teknis) | `03_MIGRATION_SPEC.md` | ✅ Selesai | — |
| 4 | Spec Completeness Review | `04_SPEC_COMPLETENESS_REVIEW.md` | ✔️ Lulus | ✔️ Lulus 2026-09-24 (0 gap) |
| 5 | Acceptance Criteria & Test Plan | `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `05b_TEST_PLAN_MIGRATION.md` | ✅ Selesai (33 AC) | — |
| 6 | Code Migration | kode 2 addon + `06c_IMPLEMENTATION_LOG.md` | ✅ Selesai (G1 42/42, G2 smoke) | — (disiplin per-fase A1→G2) |
| 7 | Data Migration Scripts | `07_DATA_MIGRATION_PLAN.md` + script — cuma kalau upgrade instance | — N/A (port kode saja, dikonfirmasi dev) | — |
| 8 | Code Review | `08_CODE_REVIEW.md` | ✔️ Lulus (0 🔴, 0 🟡, 4 🔵) | ✔️ Lulus 2026-09-24 |
| 9 | Dev Testing | `09_DEV_TESTING.md` | ✔️ Lulus (42/42, 0 stub) | ✔️ Lulus 2026-09-24 |
| 10 | QA Testing | `10_BUSINESS_FLOW_MIGRATION.md` | ⚠️ Lulus Bersyarat (9/10 live Pass + Cross-Version Compare; RMV-01 difix) | ⏳ Menunggu keputusan dev RMV-02 |
| 11 | UAT Sign-off | `11_UAT_CHECKLIST.md` | ⬜ Belum mulai | — |

Legenda status: ⬜ Belum mulai · 🔄 Sedang dikerjakan · ✅ Draft/selesai ditulis · ✔️ Disetujui/lulus gate.

---

## Folder yang di-connect

> Semua folder referensi sudah diketahui path-nya sejak conditioning. Di akhir Step 1, tetap konfirmasi ulang ke dev (checklist `01a_MIGRATION_INTAKE.md` §0).

| Folder | Path | Peran | Read-only? |
|---|---|---|---|
| `target-codebase` (folder UTAMA) | `D:\Kuncoro\doodex\repo\french-business-directory-migration-20` (branch `migration/20.0`) | CLAUDE.md + `doc-dev/` di root, kode migrasi di `fr_business_directory/` + `personal_email_usage/` | Tidak |
| `migration-tool` | `D:\Kuncoro\doodex\repo\migration-tool-project\migration-tool` | Template + knowledge base; tulis ke `migration-records/french_business_directory_19.0_20.0/` | Tulis di `migration-records/` saja |
| `native-source` (Community 19.0) | `D:\Kuncoro\doodex\repo\odoo19` (git, branch `19.0`) | Cross-check API core 19.0 (`contacts`, `l10n_fr`, `mail`) | Ya |
| `native-source-enterprise` (Enterprise 19.0) | `D:\Kuncoro\doodex\repo\enterprise19` (git, branch `19.0`, addons-only) | Jaga-jaga — kedua addon tidak depend Enterprise | Ya |
| `native-target` (Community 20.0) | `D:\Kuncoro\doodex\repo\odoo20` (git, branch `20.0`) | Diff API core 20.0 (step 2) | Ya |
| `native-target-enterprise` (Enterprise 20.0) | `D:\Kuncoro\doodex\repo\enterprise20` (git, branch `20.0`, addons-only) | Jaga-jaga — tidak wajib dianalisis kecuali ditemukan dependency Enterprise baru | Ya |
| `third-party-source`/`third-party-target` (OCA) | — | Tidak dipakai — dikonfirmasi dev tidak ada dependency OCA/third-party (project sebelumnya; cek ulang di Step 1) | — |

> **Tidak ada `source-codebase` folder terpisah.** Kode versi 19.0 direferensikan via `git diff`/`git show` ke branch `migration/19.0` di repo yang sama, tanpa folder terpisah. Worktree fisik hanya dibuat on-demand untuk Cross-Version-Compare (lihat §Alur kerja).

> **Struktur native (dicek 2026-09-24):** model dua-clone standar — `odoo19`/`odoo20` repo Community penuh, `enterprise19`/`enterprise20` addons-only terpisah. Empat path terpisah, versi tepat: source = `odoo19` + `enterprise19`, target = `odoo20` + `enterprise20`. BUKAN folder gabungan Community+Enterprise satu folder seperti yang dipakai project 18→19 (folder gabungan itu sudah tidak ada).

---

## Knowledge base

Sebelum step 2 mulai analisis, cek `migration-tool/knowledge/INDEX.md` — `version-diffs/19-to-20.md` sudah ada (dari `optional_field_save` dan `pos-margin-sale`), plus `dependency-compat/fetchmail/18-to-19.md` dan `dependency-compat/l10n_fr/18-to-19.md` sebagai konteks pasangan versi sebelumnya (arsitektur `fetch_mail()` sudah dirombak di 19.0 — cek apakah 20.0 merombak lagi).

Temuan baru (general atau dependency-specific) ditulis ke `migration-tool/migration-records/french_business_directory_19.0_20.0/SUMMARY.md` saat itu juga — **BUKAN** langsung ke `migration-tool/knowledge/`. Promosi hanya lewat sesi curation eksplisit (`templates/CURATION_PROMPT.md`).

---

## Riwayat migrasi sebelumnya (referensi historis — JANGAN dihapus)

| Project | Dokumen | Status | Catatan |
|---|---|---|---|
| Backfill 17.0 | `doc-dev/backfill/` (termasuk `FINDINGS.md`) | Selesai | Ditambahkan ke repo ini via `d2c84b6` (dari repo migration-18) |
| Migrasi 17.0→18.0 | `doc-dev/migration_17.0_18.0/doc/` (`01_intake/01b_BASELINE_SPEC.md`, `FINDINGS.md`) | SELESAI | Branch `migration/18.0`. Migration record: `migration-tool/migration-records/french_business_directory_17.0_18.0/` |
| Migrasi 18.0→19.0 | `doc-dev/migration_18.0_19.0/doc/` — **baseline behavior:** `01_intake/01b_BASELINE_SPEC.md`; **gap yang sengaja dipertahankan:** `FINDINGS.md` | SELESAI 2026-08-26 (UAT diterima berdasarkan evidence AI — dev memilih "Terima evidence AI") | Branch `migration/19.0` (di dokumen lama tertulis `migration/19.0_target`). Perubahan kode: DIFF-01/MF-03 `fetchmail.server.fetch_mail()`→`_fetch_mail()`, DIFF-02/MF-02 `res.partner.siret`→`company_registry`, + MF-04 (6 test email, pasca-UAT). 24/24 test pass di run final, QA 9/9. Migration record: `migration-tool/migration-records/french_business_directory_18.0_19.0/` |

---

## Referensi

- Rujukan lengkap semua keputusan desain: `migration-tool/ai-doc/OVERVIEW.md`
- Panduan operasional: `migration-tool/ai-doc/USAGE_GUIDE.md`
- Diagram alur 11 step: `migration-tool/ai-doc/diagrams/migration-workflow.svg`
- Diagram dua jalur dokumen (functional vs teknis): `migration-tool/ai-doc/diagrams/spec-vs-test-tracks.svg`
