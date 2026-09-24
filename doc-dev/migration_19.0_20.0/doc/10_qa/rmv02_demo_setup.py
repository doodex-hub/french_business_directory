# RMV-02 demo data (Step 10, 2026-09-24) — dijalankan lewat `odoo-bin shell` (stdin), idempoten.
# Membuat/menyetel ulang dua kontak dan menyetel sequence siret.wizard supaya wizard BERIKUTNYA
# yang tersimpan mendapat id = id kontak "KORBAN". Tujuannya: bug RMV-02 langsung kelihatan di
# kontak yang jelas namanya, bukan menimpa "My Company".
Partner = env['res.partner']

asal = Partner.search([('ref', '=', 'RMV02-ASAL')], limit=1) or Partner.create({'name': 'LA POSTE', 'ref': 'RMV02-ASAL'})
asal.write({
    # 'LA POSTE': halaman 1, 2 dan 400 terbukti aman; 'CARREFOUR' halaman 2 crash (RMV-05)
    'name': 'LA POSTE',
    'street': '(alamat asal - belum diisi)', 'street2': False, 'zip': False, 'city': False,
    'additional_identifiers': {},
    'parent_id': False,
})

korban = Partner.search([('ref', '=', 'RMV02-KORBAN')], limit=1) or Partner.create({'name': 'x', 'ref': 'RMV02-KORBAN'})
korban.write({
    'name': 'KONTAK KORBAN - JANGAN BERUBAH',
    'street': 'Jl. Sudirman No. 1', 'street2': False, 'zip': '10220', 'city': 'Jakarta',
    'phone': '+62 21 000000',
    'additional_identifiers': {},
    'parent_id': False,
})

env['siret.wizard'].search([]).unlink()
env.cr.execute("SELECT setval('siret_wizard_id_seq', %s, false)", [korban.id])
env.cr.commit()
print(f"RMV02 READY asal_id={asal.id} korban_id={korban.id} next_wizard_id={korban.id}")
