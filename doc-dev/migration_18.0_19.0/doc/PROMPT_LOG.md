# Prompt Log — french_business_directory (18.0 → 19.0)

**Tujuan:** data empiris untuk `ai-doc/ROADMAP.md` Fase 5 (Otomasi Bertahap) — mengukur seberapa sering user harus prompt untuk flow normal vs tool-fix, per step.

---

## Klasifikasi

- **Normal** — prompt yang menjalankan/melanjutkan salah satu dari 11 step, atau review/verifikasi konten migrasi modul ini.
- **Tool-fix** — prompt yang hasilnya perubahan ke `migration-tool/templates/`, `migration-tool/ai-doc/`, atau proses SOP itu sendiri.
- **Tidak dihitung** — orientasi murni.

## Log per Step

| Step | # Prompt Normal | # Prompt Tool-fix | Catatan |
|---|---|---|---|
| 0 — Bootstrap (sebelum step 1 resmi) | 5 | 0 | Kickoff, 2 batch konfirmasi intake (GUI git/sifat migrasi/source paralel/folder referensi; deadline/owner/dokumen lain/Enterprise-OCA), 2 dialog approval edit `.claude/settings.json` (diblokir classifier permission dulu, dev klarifikasi "apa saja folder readonly itu?" lalu approve) |
| 1 — Intake & Baseline Spec | 0 | 0 | Bagian dari batch Step 0 di atas |
| 2 — Diff & Compatibility Analysis | 0 | 0 | 0 interupsi |
| 3 — Migration Spec | 0 | 0 | 0 interupsi |
| 4 — Spec Completeness Review | 0 | 0 | 0 interupsi |
| 5 — Acceptance Criteria & Test Plan | 0 | 0 | 0 interupsi |
| 6 — Code Migration (semua fase A-G2) | 0 | 0 | 0 interupsi |
| 7 — Data Migration Scripts | — | — | N/A, port kode saja |
| 8 — Code Review | 0 | 0 | 0 interupsi |
| 9 — Dev Testing | 2 | 0 | Checkpoint G1 (Mode A vs C, didesain untuk tanya), eskalasi MF-03 (keputusan risiko tinggi — pindah titik override `fetch_mail()`→`_fetch_mail()`) |
| 10 — QA Testing | 0 | 0 | 0 interupsi |
| 11 — UAT Sign-off | 1 | 0 | Keputusan sign-off (evidence AI vs eksekusi manual) |
| **Total** | 8 | 0 | 0 prompt tool-fix — semua interupsi genuinely butuh keputusan dev (checkpoint desain, eskalasi risiko tinggi, sign-off final), bukan gangguan proses |

## Catatan Definisi

*(belum ada revisi kriteria di project ini)*

## Ringkasan Akhir Project (isi setelah step 11 selesai)

- Step dengan rasio Tool-fix tertinggi: tidak ada (0 prompt tool-fix sepanjang project).
- Step yang paling "bersih" (0 interupsi): Step 1-8, 10 (9 dari 11 step) — konsisten dengan validasi M2 (`ai-doc/CLI_DIALOG_CHECKLIST.md`) di project `advanced_sales_analysis` sebelumnya.
- **Data point baru untuk `ROADMAP.md` §5:** project ini membuktikan checkpoint G1 (Step 9) BUKAN cuma administratif — G1 run #1 menemukan MF-03 (breaking change arsitektur `fetchmail.server` 19.0) yang SAMA SEKALI TIDAK terdeteksi review statis Step 2, walau Step 2 sudah membaca penuh source file terkait (`fetchmail.py`). Ini memperkuat argumen BUKAN mengotomasi/skip G1 di fase otomasi mendatang — nilai G1 justru di titik ini (menangkap gap yang review manusia/AI statis lewatkan).
