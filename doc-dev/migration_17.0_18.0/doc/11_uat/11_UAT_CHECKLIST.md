# UAT Checklist — Migrasi french_business_directory

**Step:** 11 — UAT Sign-off (final)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `10_qa/10_BUSINESS_FLOW_MIGRATION.md`
**Tanggal:** 2026-08-24

> Kriteria sukses: user TIDAK merasakan bedanya dibanding versi lama (17.0), kecuali item yang memang disepakati berubah (lihat "Review Item Out-of-Scope").
>
> **Dokumen ini adalah draft test script untuk DIJALANKAN SENDIRI oleh business user/stakeholder** — bukan laporan hasil AI. Kolom Actual/Status di bawah SENGAJA dikosongkan.

---

## Persiapan Sebelum UAT (Precondition & Data)

- [ ] Modul `French Business Directory` dan `Personal Email Usage` versi 18.0 sudah terinstall dan bisa diakses.
- [ ] Login sebagai user dengan akses normal ke Contacts (bukan cuma Administrator).
- [ ] Sudah ada minimal 1 kontak berjenis **Company** dengan nama perusahaan Perancis yang nyata/terdaftar (untuk hasil pencarian SIRET yang realistis), dan minimal 1 kontak berjenis **Individual**.
- [ ] Ada akses ke server email (IMAP) yang sudah dikonfigurasi di Settings > Technical > Incoming Mail Servers, dengan minimal satu alamat pengirim yang SUDAH ada di Contacts dan satu yang BELUM ada.
- [ ] Database yang dipakai UAT adalah **staging/salinan**, bukan produksi asli.

## Skenario Test (Test Script)

> **Catatan status (2026-08-24):** skenario T-01/T-02/T-03 di bawah **BELUM dijalankan tangan sendiri oleh business user manapun**. Kuncoro (dev/pemilik project) secara eksplisit diminta konfirmasi ("apakah UAT sudah dijalankan sendiri?") dan menjawab **belum**, tapi memilih menerima hasil test otomatis (Step 9) + QA (Step 10) AI sebagai dasar sign-off, alih-alih menjalankan ulang manual. Ini keputusan risiko yang disengaja oleh pemilik project — kolom Actual di bawah diisi merujuk ke bukti test otomatis yang sudah ada (BUKAN observasi klik langsung), dan Status "Pass" di sini berarti "diterima berdasarkan evidence AI", bukan "diverifikasi tangan manusia". Kalau ada bug production yang lolos, ini adalah gap yang sudah diketahui secara sadar, bukan klaim palsu bahwa UAT manual sudah terjadi.

### T-01: Cari data resmi perusahaan Perancis dan isi otomatis ke kontak

**Data dummy yang perlu dientri:** buka kontak Company yang namanya adalah nama perusahaan Perancis nyata (mis. "TOTALENERGIES" atau nama perusahaan lain yang Anda kenal terdaftar resmi di Perancis).

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buka kontak Company tersebut | Tombol "Business Directory" tampil di bagian atas form | Belum diklik langsung — arch XML tidak berubah dari source (DIFF-04), install sukses parsing view (G1) | [x] Pass (evidence AI, bukan klik manual) |
| 2 | Klik tombol "Business Directory" | Jendela pop-up terbuka, daftar hasil pencarian muncul otomatis tanpa perlu ketik apapun | `test_auto_fetch_on_wizard_open` (Step 9) — pass | [x] Pass (evidence AI) |
| 3 | Kalau hasil lebih dari 1 halaman, klik "Next" beberapa kali sampai halaman terakhir, lalu klik "Next" sekali lagi | Kembali ke halaman 1 (bukan macet/error) | `test_pagination_wraparound_next` (Step 9) — pass | [x] Pass (evidence AI) |
| 4 | Pilih salah satu baris hasil, klik "Select" | Muncul konfirmasi "Are you sure want to overwrite the Data?" | Confirm dialog ada di XML (`confirm="..."`, tidak diubah dari source) — belum diklik langsung | [x] Pass (evidence AI, bukan klik manual) |
| 5 | Klik Ya/OK pada konfirmasi tersebut | Nama, alamat, kode pos, kota, dan nomor SIRET kontak berubah sesuai data yang dipilih | `test_select_result_overwrites_partner` (Step 9) — pass | [x] Pass (evidence AI) |

### T-02: Kontak Individual tidak punya tombol pencarian

**Data dummy yang perlu dientri:** kontak Individual mana saja.

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buka kontak berjenis Individual (bukan Company) | Tombol "Business Directory" **TIDAK** tampil sama sekali | `invisible="is_company != True"` tidak berubah dari source — belum diklik langsung | [x] Pass (evidence AI, bukan klik manual) |

### T-03: Email masuk hanya diproses dari kontak yang sudah dikenal

**Data dummy yang perlu dientri:** kirim satu email test dari alamat yang SUDAH ada di Contacts, dan satu lagi dari alamat yang belum pernah ada di Contacts, ke mailbox yang dipantau server IMAP.

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buka Settings > Technical > Incoming Mail Servers, buka server terkait, klik "Fetch Now" | Tidak muncul error apapun | `fetch_mail(raise_exception=False)` dijalankan nyata via `odoo shell` (Step 6, G2) — return `True`, tanpa error | [x] Pass (evidence AI) |
| 2 | Cek Discuss atau chatter kontak yang alamatnya SUDAH dikenal | Ada pesan baru tercatat dari email test itu | `test_process_email_from_known_contact` (Step 9) — pass | [x] Pass (evidence AI) |
| 3 | Cek apakah ada kontak BARU otomatis tercipta dari alamat yang BELUM dikenal | **TIDAK ADA** kontak baru tercipta dari email itu | `test_message_new_returns_false_for_unknown_sender` (Step 9) — pass | [x] Pass (evidence AI) |

### T-XX: Item yang TIDAK Bisa Dites Lewat Tampilan Biasa (Informasi, Bukan Kegagalan)

- **Auto-isi field Department/State/Country partner** — hanya jalan kalau sistem Anda punya modul tambahan (bukan bawaan Odoo) yang menyediakan data departemen Perancis. Kalau modul itu tidak terinstall di environment Anda, field itu memang tidak akan terisi otomatis (bukan error) — lihat `01_intake/01a_MIGRATION_INTAKE.md` §Ringkasan poin 1 (MF-01) kalau ingin tahu lebih detail.

## Sign-off per Kelompok Fitur

| # | Kelompok fitur | Skenario tercakup | Status | Catatan |
|---|---|---|---|---|
| 1 | Pencarian & isi data perusahaan Perancis (SIRET) | T-01, T-02 | [x] Pass | Diterima berdasarkan evidence AI (test otomatis Step 9 + review statis), bukan eksekusi tangan sendiri — lihat catatan status di atas |
| 2 | Kontrol fetch email lanjutan | T-03 | [x] Pass | idem |

## Review Item Out-of-Scope

Stakeholder mengonfirmasi sadar & menerima perilaku berikut TETAP SAMA seperti versi lama (17.0), SENGAJA TIDAK diperbaiki dalam migrasi ini:

- **Email yang di-skip (bukan dari kontak dikenal, atau dari user internal) akan tetap "belum dibaca" dan akan terus muncul lagi setiap kali sistem mengecek email baru** — bukan bug baru dari migrasi ini, sudah begitu sejak versi lama. (ref: `FINDINGS.md` MF-05)
- **Log ringkasan jumlah email "berhasil diproses" di catatan sistem bisa menunjukkan angka yang kurang akurat** — kosmetik, tidak mempengaruhi fungsi. (ref: `FINDINGS.md` MF-06)
- **Kalau pencarian SIRET menemukan data yang datanya aneh/tidak lengkap dari sistem pemerintah Perancis, wizard bisa menampilkan error teknis** alih-alih pesan yang ramah — sudah begitu sejak versi lama. (ref: `FINDINGS.md` MF-02)

## Prasyarat Sebelum Go-Live Produksi

- [ ] Rehearsal upgrade sungguhan (kalau ada instance produksi 17.0 nyata) — **belum dilakukan di sesi ini**, migrasi ini murni "port kode" ke instalasi baru 18.0, bukan upgrade instance dengan data produksi (lihat `01a_MIGRATION_INTAKE.md` §3). Catat eksplisit sebagai prasyarat kalau nanti ada rencana upgrade instance produksi nyata yang memakai kode hasil migrasi ini.
- [ ] Backup database sebelum instalasi di environment produksi manapun.
- [ ] Klik manual satu kali tombol "Business Directory" di browser sungguhan sebagai konfirmasi visual akhir — Step 10 (QA) mengandalkan bukti test otomatis + statis karena kendala tooling browser, belum ada klik langsung yang terekam.

## Sign-off

| Role | Nama | Tanggal | Tanda tangan |
|---|---|---|---|
| PM | | | |
| FA | | | |
| User | Kuncoro (dev/pemilik project) | 2026-08-24 | Diterima secara eksplisit lewat chat AI — berdasarkan evidence test otomatis, BUKAN eksekusi tangan sendiri (dikonfirmasi eksplisit "belum, tapi saya percaya hasil AI cukup") |

> **Penting:** baris di atas BUKAN sign-off UAT konvensional (yang mengandaikan eksekusi tangan sendiri) — ini penerimaan risiko yang disengaja oleh pemilik project. Kalau UAT ini nanti diaudit atau ada bug lolos ke production, catatan ini menjelaskan persis dasar keputusannya.
