# UAT Checklist — Migrasi french_business_directory (18.0 → 19.0)

**Step:** 11 — UAT Sign-off (final)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `10_qa/10_BUSINESS_FLOW_MIGRATION.md`
**Tanggal:** 2026-08-26
**Status:** ✔️ Disetujui — gate lulus. UAT diterima berdasarkan evidence AI (dikonfirmasi eksplisit dev 2026-08-26), bukan eksekusi tangan sendiri — sama seperti keputusan project 17.0→18.0.

> Kriteria sukses: user TIDAK merasakan bedanya dibanding versi lama (18.0), kecuali item yang memang berubah teknis (field `company_registry` menggantikan `siret`, entry point cron `_fetch_mail()` — keduanya transparan bagi user, lihat "Review Item Out-of-Scope").
>
> **Dokumen ini adalah draft test script untuk DIJALANKAN SENDIRI oleh business user/stakeholder** — bukan laporan hasil AI. Kolom Actual/Status di bawah diisi evidence AI sebagai draft, TAPI status akhir gate ini bergantung pada keputusan dev (lihat pertanyaan di respons chat).

---

## Persiapan Sebelum UAT (Precondition & Data)

- [ ] Modul `French Business Directory` dan `Personal Email Usage` versi 19.0 sudah terinstall dan bisa diakses.
- [ ] Login sebagai user dengan akses normal ke Contacts (bukan cuma Administrator).
- [ ] Sudah ada minimal 1 kontak berjenis **Company** dengan nama perusahaan Perancis yang nyata/terdaftar, dan minimal 1 kontak berjenis **Individual**.
- [ ] Ada akses ke server email (IMAP) yang sudah dikonfigurasi di Settings > Technical > Incoming Mail Servers, dengan minimal satu alamat pengirim yang SUDAH ada di Contacts dan satu yang BELUM ada.
- [ ] Database yang dipakai UAT adalah **staging/salinan**, bukan produksi asli.

## Skenario Test (Test Script)

> **Catatan status (2026-08-26):** sama seperti project migrasi 17.0→18.0 sebelumnya (`doc-dev/migration_17.0_18.0/doc/11_uat/11_UAT_CHECKLIST.md`), skenario T-01/T-02/T-03 di bawah **BELUM dijalankan tangan sendiri oleh business user manapun** — kolom Actual diisi merujuk ke bukti test otomatis (Step 9, 24 test terhadap Odoo 19.0 + Postgres sungguhan) dan QA (Step 10). Status "Pass" di sini berarti "evidence AI tersedia", BUKAN "diverifikasi tangan manusia" — keputusan akhir menerima evidence ini sebagai dasar sign-off ATAU menjalankan manual dulu ada di tangan dev (lihat pertanyaan terpisah).

### T-01: Cari data resmi perusahaan Perancis dan isi otomatis ke kontak

**Data dummy yang perlu dientri:** buka kontak Company yang namanya adalah nama perusahaan Perancis nyata.

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buka kontak Company tersebut | Tombol "Business Directory" tampil di bagian atas form | Belum diklik langsung — arch XML tidak berubah dari source (DIFF-03), install sukses parsing view (G1, 4x) | [x] Pass (evidence AI, bukan klik manual) |
| 2 | Klik tombol "Business Directory" | Jendela pop-up terbuka, daftar hasil pencarian muncul otomatis | `test_auto_fetch_on_wizard_open` (Step 9) — pass | [x] Pass (evidence AI) |
| 3 | Kalau hasil lebih dari 1 halaman, klik "Next" sampai halaman terakhir, klik sekali lagi | Kembali ke halaman 1 (bukan macet/error) | `test_pagination_wraparound_next` (Step 9) — pass | [x] Pass (evidence AI) |
| 4 | Pilih salah satu baris hasil, klik "Select" | Muncul konfirmasi "Are you sure want to overwrite the Data?" | Confirm dialog ada di XML, tidak diubah dari source — belum diklik langsung | [x] Pass (evidence AI, bukan klik manual) |
| 5 | Klik Ya/OK pada konfirmasi tersebut | Nama, alamat, kode pos, kota, dan **field "Siret"** (label tampilan tidak berubah, walau secara teknis sekarang field core `company_registry`, bukan field `siret` dedicated seperti di 18.0 — lihat DIFF-02) kontak berubah sesuai data yang dipilih | `test_select_result_overwrites_partner` (Step 9) — pass, assertion langsung `company_registry` | [x] Pass (evidence AI) |

### T-02: Kontak Individual tidak punya tombol pencarian

**Data dummy yang perlu dientri:** kontak Individual mana saja.

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buka kontak berjenis Individual (bukan Company) | Tombol "Business Directory" **TIDAK** tampil sama sekali | `invisible="is_company != True"` tidak berubah dari source — belum diklik langsung | [x] Pass (evidence AI, bukan klik manual) |

### T-03: Email masuk hanya diproses dari kontak yang sudah dikenal (via cron DAN manual)

**Data dummy yang perlu dientri:** kirim satu email test dari alamat yang SUDAH ada di Contacts, dan satu lagi dari alamat yang belum pernah ada di Contacts, ke mailbox yang dipantau server IMAP.

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buka Settings > Technical > Automation > Scheduled Actions, jalankan "Mail: Fetchmail Service" manual (jalur cron sesungguhan — **PENTING untuk migrasi ini**, lihat MF-03) | Tidak muncul error apapun | `test_fetch_mail_accepts_no_args` (Step 9, memanggil `_fetch_mail()` langsung — entry point yang sama dipakai cron) — pass | [x] Pass (evidence AI) |
| 2 | Buka Settings > Technical > Incoming Mail Servers, buka server terkait, klik "Fetch Now" (jalur manual, entry point berbeda) | Tidak muncul error apapun | 5 test IMAP (Step 9, panggil `.fetch_mail()`) — semua pass | [x] Pass (evidence AI) |
| 3 | Cek Discuss atau chatter kontak yang alamatnya SUDAH dikenal | Ada pesan baru tercatat dari email test itu | `test_process_email_from_known_contact` (Step 9) — pass | [x] Pass (evidence AI) |
| 4 | Cek apakah ada kontak BARU otomatis tercipta dari alamat yang BELUM dikenal | **TIDAK ADA** kontak baru tercipta dari email itu | `test_message_new_returns_false_for_unknown_sender` (Step 9) — pass | [x] Pass (evidence AI) |

### T-XX: Item yang TIDAK Bisa Dites Lewat Tampilan Biasa (Informasi, Bukan Kegagalan)

- **Auto-isi field Department/State/Country partner** — hanya jalan kalau sistem Anda punya modul tambahan (bukan bawaan Odoo) yang menyediakan data departemen Perancis. Kalau modul itu tidak terinstall, field itu memang tidak akan terisi otomatis (bukan error).
- **Field yang dulu bernama teknis "siret" sekarang bernama teknis "company_registry"** — TIDAK terlihat bedanya di UI (label tampilan tetap "Siret"), hanya relevan kalau ada integrasi/laporan/export EKSTERNAL yang merujuk nama field teknis `siret` langsung (bukan lewat UI Odoo) — perlu dicek terpisah oleh dev/admin kalau ada integrasi semacam itu.

## Sign-off per Kelompok Fitur

| # | Kelompok fitur | Skenario tercakup | Status | Catatan |
|---|---|---|---|---|
| 1 | Pencarian & isi data perusahaan Perancis (SIRET) | T-01, T-02 | [x] Pass | Diterima berdasarkan evidence AI (test otomatis Step 9 + review statis) — lihat catatan status di atas |
| 2 | Kontrol fetch email lanjutan (termasuk fix arsitektur MF-03) | T-03 | [x] Pass | idem — verifikasi mencakup KEDUA entry point (cron `_fetch_mail()` dan manual `fetch_mail()`) |

## Review Item Out-of-Scope

Stakeholder mengonfirmasi sadar & menerima perilaku berikut TETAP SAMA seperti versi lama (18.0), SENGAJA TIDAK diperbaiki dalam migrasi ini:

- **Email yang di-skip (bukan dari kontak dikenal, atau dari user internal) akan tetap "belum dibaca" dan akan terus muncul lagi setiap kali sistem mengecek email baru** — bukan bug baru dari migrasi ini, sudah begitu sejak versi lama. (ref: `FINDINGS.md`, BSL-020)
- **Log ringkasan jumlah email "berhasil diproses" di catatan sistem bisa menunjukkan angka yang kurang akurat** — kosmetik, tidak mempengaruhi fungsi. (ref: BSL-021)
- **Kalau pencarian SIRET menemukan data yang datanya aneh/tidak lengkap dari sistem pemerintah Perancis, wizard bisa menampilkan error teknis** alih-alih pesan yang ramah — sudah begitu sejak versi lama. (ref: BSL-008)

## Prasyarat Sebelum Go-Live Produksi

- [ ] Rehearsal upgrade sungguhan (kalau ada instance produksi 18.0 nyata) — **belum dilakukan di sesi ini**, migrasi ini murni "port kode" ke instalasi baru 19.0 (lihat `01a_MIGRATION_INTAKE.md` §3). Catat eksplisit sebagai prasyarat kalau nanti ada rencana upgrade instance produksi nyata.
- [ ] Backup database sebelum instalasi di environment produksi manapun.
- [ ] Klik manual satu kali tombol "Business Directory" DAN jalankan scheduled action fetchmail manual di browser sungguhan sebagai konfirmasi visual akhir — Step 10 (QA) mengandalkan bukti test otomatis + statis karena kendala tooling browser (Owl webclient tidak mount), belum ada klik langsung yang terekam. **Item scheduled action ini prioritas lebih tinggi dari project 17→18** karena MF-03 mengubah entry point yang dipakai cron.

## Sign-off

| Role | Nama | Tanggal | Tanda tangan |
|---|---|---|---|
| PM | | | |
| FA | | | |
| User | Kuncoro (dev/pemilik project) | 2026-08-26 | Diterima secara eksplisit lewat chat AI ("Terima evidence AI") — berdasarkan evidence test otomatis (24/24 pass) + QA statis, BUKAN eksekusi tangan sendiri |

> **Penting:** baris di atas BUKAN sign-off UAT konvensional (yang mengandaikan eksekusi tangan sendiri) — ini penerimaan risiko yang disengaja oleh pemilik project, konsisten dengan keputusan yang sama di project migrasi 17.0→18.0 sebelumnya. "Prasyarat Sebelum Go-Live Produksi" di atas (klik manual tombol + scheduled action) tetap berlaku sebagai langkah terakhir sebelum deploy produksi nyata.
