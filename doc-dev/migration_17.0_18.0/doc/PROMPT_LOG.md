# Prompt Log — french_business_directory

**Tujuan:** data empiris untuk `ai-doc/ROADMAP.md` Fase 5 (Otomasi Bertahap) — mengukur seberapa sering user harus prompt untuk **flow normal** migrasi vs prompt **tool-fix**, per step.

**Cross-cutting** — hidup di root `doc/`, bukan di satu folder step.

---

## Klasifikasi

- **Normal** — prompt yang menjalankan/melanjutkan salah satu dari 11 step, atau review/verifikasi konten migrasi modul ini.
- **Tool-fix** — prompt yang hasilnya perubahan ke `migration-tool/templates/`, `migration-tool/ai-doc/`, atau proses SOP itu sendiri.
- **Tidak dihitung** — orientasi murni, non-actionable.

## Log per Step

| Step | # Prompt Normal | # Prompt Tool-fix | Catatan |
|---|---|---|---|
| 0 — Bootstrap (sebelum step 1 resmi) | 8 | 0 | Konfirmasi target-codebase, versi 17.0→18.0, migration nature, native-*/Enterprise/OCA, GUI git closed, untracked files, branch bootstrap (target+source), reuse spec lama |
| 1 — Intake & Baseline Spec | 3 | 0 | Intake + baseline spec (cross-check spec backfill lama) + review findings (MF-01, MF-05) — gate lulus, ter-commit |
| 2 — Diff & Compatibility Analysis | 1 | 0 | 2 temuan critical dikonfirmasi (DIFF-01 tree/list, DIFF-02 fetch_mail signature) |
| 3 — Migration Spec | | | |
| 4 — Spec Completeness Review | | | |
| 5 — Acceptance Criteria & Test Plan | | | |
| 6 — Code Migration (semua fase A-G2) | | | |
| 7 — Data Migration Scripts | — | — | N/A, port kode saja |
| 8 — Code Review | | | |
| 9 — Dev Testing | | | |
| 10 — QA Testing | | | |
| 11 — UAT Sign-off | | | |
| **Total** | 9 | 0 | |

## Catatan Definisi

*(belum ada revisi kriteria)*

## Ringkasan Akhir Project (isi setelah step 11 selesai)

- Step dengan rasio Tool-fix tertinggi: ...
- Step yang paling "bersih": ...
