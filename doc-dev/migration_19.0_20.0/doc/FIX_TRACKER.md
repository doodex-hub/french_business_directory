# Fix Tracker — french_business_directory (19.0 → 20.0)

**Tujuan:** mengontrol penyelesaian item yang masih terbuka setelah Step 10, sebelum Step 11 (UAT).
**Dibuat:** 2026-09-25 · **Sumber detail:** `FINDINGS.md` (satu-satunya sumber analisis — file ini hanya urutan + status).
**Aturan:** satu item dikerjakan sampai ✅ sebelum item berikutnya. Status HANYA diubah setelah buktinya ada.

## Alur status (wajib dilewati berurutan)

| Status | Artinya | Syarat pindah ke status berikutnya |
|---|---|---|
| ⏳ Menunggu keputusan | Opsi sudah dijelaskan, belum dipilih dev | Dev memilih opsi di chat (dicatat tanggal + kutipan) |
| 🔧 Dikerjakan | Kode/test/dokumen sedang diubah AI | Test baru ditulis + `run-test.sh` 0 failed |
| 🧪 Verifikasi | Dicek live di browser (Playwright) dan/atau dev | Bukti live tercatat (screenshot/query DB/log) |
| ✅ Selesai | FINDINGS + dokumen step ter-update, di-commit | — |
| ➖ Tidak dikerjakan | Diputuskan dibiarkan | Alasan + keputusan dicatat |

Item yang hanya butuh keputusan (tanpa perubahan kode) langsung ⏳ → ✅ setelah dev memilih.

## Urutan kerja & status

| # | ID | Masalah (ringkas) | Jenis | Butuh kode? | Opsi & rekomendasi AI | Status | Bukti / catatan |
|---|---|---|---|---|---|---|---|
| 1 | **RMV-05** | Halaman hasil crash ("Oops", `TypeError`) kalau API mengirim `libelle_voie: null` (mis. "CARREFOUR" hal. 2) | Bug bawaan 16–19, berdampak ke user | Ya (kecil) | A) **Perbaiki** — nilai kosong/`None` dari API diperlakukan sebagai teks kosong di susunan alamat (rekomendasi, sekelas RMV-03 yang sudah disetujui) · B) Biarkan | ⏳ Menunggu keputusan | — |
| 2 | **MF-02** | SIRET kini disimpan di identifier tervalidasi Odoo 20 (SIRET tak valid ditolak, SIREN terisi otomatis) | Perubahan platform 20.0 | Tidak (kode sudah jadi) | A) **Terima validasi bawaan Odoo** (rekomendasi — sudah terbukti live dengan SIRET La Poste) · B) Matikan validasi seperti 19.0 (risiko error tersembunyi saat edit kontak) | ⏳ Menunggu keputusan | Live Pass S-07 (Step 10) |
| 3 | **MF-03** | Aturan tombol "Business Directory": sekarang tampil untuk semua kontak tanpa parent (workaround), termasuk individu | Perubahan platform 20.0 (`is_company` dari VAT) | Mungkin | A) **Sign-off workaround sekarang** (`invisible="parent_id"`) · B) Aturan lain yang dev tentukan (mis. sembunyikan untuk kontak yang jelas individu) | ⏳ Menunggu keputusan + cek visual dev | Live Pass S-03 (Step 10) |
| 4 | **RMV-04** | Kosmetik: alamat tampil "None …" bila nomor jalan kosong; judul wizard jadi "Odoo" setelah Next/Prev | Bug bawaan 16–19, kosmetik | Ya (kecil) | A) Perbaiki keduanya · B) **Biarkan** (rekomendasi kalau ingin perubahan minimal — tidak mengganggu fungsi) | ⏳ Menunggu keputusan | — |
| — | **MF-05** | `self._cr` / `self._context` deprecated (masih jalan, hanya warning log) | Deprecation 19.0 | — | Dibiarkan; cek ulang di migrasi 20→21 | ➖ Tidak dikerjakan | Keputusan dev 2026-09-25 |

**Kenapa urutannya begini:**
1. **RMV-05 dulu** — satu-satunya item yang masih bisa memunculkan traceback "Oops" ke user; perbaikannya kecil dan sekelas perbaikan RMV-03 yang sudah disetujui.
2. **MF-02** — cukup keputusan, tanpa kode; menutupnya membuat baseline UAT jelas.
3. **MF-03** — keputusan aturan bisnis; paling baik diputuskan setelah dev melihat sendiri tombolnya di browser.
4. **RMV-04** — kosmetik, prioritas terendah.

## Definisi "selesai" untuk item yang butuh kode

- [ ] Perubahan kode minimal + komentar alasan (rujuk ID finding)
- [ ] Test baru yang gagal tanpa perbaikan dan lulus dengan perbaikan
- [ ] `docker-env/run-test.sh odoo fbd_test_20 fr_business_directory,personal_email_usage` → 0 failed, 0 error
- [ ] Cek live (Playwright) + bukti di `10_qa/evidence/`
- [ ] `FINDINGS.md`, AC (`05a`), `10_BUSINESS_FLOW_MIGRATION.md` diperbarui
- [ ] Commit (satu commit per item)

## Gate ke Step 11

Step 11 (UAT) boleh dimulai setelah item #1–#4 berstatus ✅ atau ➖.

## Log perubahan status

| Tanggal | ID | Dari → Ke | Oleh | Catatan |
|---|---|---|---|---|
| 2026-09-25 | MF-05 | — → ➖ | Dev | "Dibiarkan" |
| 2026-09-25 | RMV-05, MF-02, MF-03, RMV-04 | — → ⏳ | AI | Tracker dibuat |
