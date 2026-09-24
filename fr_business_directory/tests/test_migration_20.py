import logging
from unittest.mock import patch

from lxml import etree

from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tests.common import TransactionCase, tagged

from .test_siret_wizard import _mock_response, _result

_logger = logging.getLogger(__name__)

# Luhn-valid SIRETs: Odoo 20.0's own FR_SIRET placeholder, and a second real-world one.
VALID_SIRET = '33417522101010'
OTHER_VALID_SIRET = '73282932000074'


@tagged('post_install', '-at_install')
class TestMigration20(TransactionCase):
    """Tests added by the 19.0 -> 20.0 migration (doc-dev/migration_19.0_20.0), locking the
    platform-driven adaptations MF-01 (ir.access), MF-02 (company_registry ->
    additional_identifiers) and MF-03 (view_partner_form redesign / computed is_company)."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'ACME',
            'is_company': True,
        })

    def _open_wizard(self, results):
        with patch('requests.get', return_value=_mock_response(results)):
            return self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})

    # --- AC-00-02 / MF-01 --------------------------------------------------------------------

    def test_ir_access_rows_converted(self):
        """AC-00-02 — the 19.0 ir.model.access.csv rows (base.group_user, 1,1,1,1) exist as
        ir.access records with operation 'crud' and no domain."""
        group_user = self.env.ref('base.group_user')
        for model_name in ('siret.wizard', 'siret.wizard.result', 'matching.etablissement'):
            accesses = self.env['ir.access'].sudo().search([('model_id.model', '=', model_name)])
            self.assertEqual(len(accesses), 1, model_name)
            self.assertEqual(accesses.group_id, group_user, model_name)
            self.assertEqual(accesses.operation, 'crud', model_name)
            self.assertFalse(accesses.domain, model_name)

    def test_internal_user_can_use_wizard_models(self):
        """AC-00-02 — an internal user (base.group_user only) has create/read/write/unlink on the
        three transient models, as with the 19.0 ACL."""
        user = self.env['res.users'].create({
            'name': 'Wizard User',
            'login': 'wizard_user_fbd20',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        for model_name in ('siret.wizard', 'siret.wizard.result', 'matching.etablissement'):
            model = self.env[model_name].with_user(user)
            for operation in ('create', 'read', 'write', 'unlink'):
                self.assertTrue(model.has_access(operation), f"{model_name}: {operation}")

    # --- AC-01 / MF-03 -----------------------------------------------------------------------

    def test_partner_form_arch_has_name_and_button(self):
        """AC-01-01 — the combined partner form keeps the (single, 20.0) name field, always
        visible, with the Business Directory button next to it, hidden for non-companies."""
        arch = self.env['res.partner'].get_view(self.env.ref('base.view_partner_form').id, 'form')['arch']
        tree = etree.fromstring(arch)
        buttons = tree.xpath("//button[@name='siret_wizard']")
        self.assertEqual(len(buttons), 1)
        button = buttons[0]
        self.assertEqual(button.get('string'), 'Business Directory')
        self.assertEqual(button.get('invisible'), 'is_company != True')
        wrapper = button.getparent()
        self.assertEqual(wrapper.tag, 'div')
        self.assertIsNone(wrapper.get('invisible'))
        self.assertEqual(wrapper.getparent().tag, 'h1')
        names = wrapper.xpath("./field[@name='name']")
        self.assertEqual(len(names), 1)
        self.assertIsNone(names[0].get('invisible'))
        self.assertEqual(wrapper.index(names[0]), 0, "name field must come before the button")

    def test_new_partner_form_contacts_context_is_company(self):
        """AC-01-02 [characterization, MF-03] — is_company (drives the button visibility) on a new
        partner form opened like the Contacts action (default_is_company=True), no VAT: in the
        form before save, after save, and after a VAT is set then removed."""
        form = Form(self.env['res.partner'].with_context(default_is_company=True))
        form.name = 'NEW FRENCH CO'
        in_form = form.is_company
        partner = form.save()
        after_save = partner.is_company
        partner.vat = 'FR23334175221'
        with_vat = partner.is_company
        partner.vat = False
        vat_removed = partner.is_company
        observed = (in_form, after_save, with_vat, vat_removed)
        _logger.info("MF-03 is_company (form, saved, with VAT, VAT removed) = %s", observed)
        # Observed on 20.0 (G1 #6, 2026-09-24): True in the unsaved form (default_is_company),
        # recomputed to False on save because there is no VAT (has_vat), True once a VAT is set,
        # False again when it is removed -> the button disappears after save for a company
        # without VAT. Recorded as MF-03 decision point, not "fixed" here.
        self.assertEqual(observed, (True, False, True, False))

    def test_siret_wizard_action(self):
        """AC-01-03 — the button action opens siret.wizard in a dialog with active_id in context."""
        action = self.partner.siret_wizard()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'siret.wizard')
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context'], {'active_id': self.partner.id})

    # --- AC-04 / MF-02 -----------------------------------------------------------------------

    def test_select_etablissement_writes_fr_siret(self):
        """AC-04-01 — select_siret() at etablissement level writes the SIRET to FR_SIRET and the
        other fields as in 19.0 (street cut before the postal code, street2 emptied)."""
        etab = {
            'siret': VALID_SIRET, 'adresse': '10 RUE DE LA PAIX 75002 PARIS', 'code_postal': '75002',
            'libelle_commune': 'PARIS', 'latitude': '48.8', 'longitude': '2.3',
            'date_fermeture': False, 'etat_administratif': 'A',
        }
        wizard = self._open_wizard([_result(nom_complet='ETAB CO', matching_etablissements=[etab])])
        matching = wizard.result_ids.matching_etablissements
        self.partner.street2 = 'old street2'
        matching.with_context(active_id=self.partner.id).select_siret()
        self.assertEqual(self.partner._get_additional_identifier('FR_SIRET'), VALID_SIRET)
        self.assertEqual(self.partner.name, 'ETAB CO')
        self.assertEqual(self.partner.street, '10 RUE DE LA PAIX')
        self.assertFalse(self.partner.street2)
        self.assertEqual(self.partner.zip, '75002')
        self.assertEqual(self.partner.city, 'PARIS')

    def test_select_invalid_siret_raises_validation_error(self):
        """AC-04-04 [MF-02 deviation a] — a SIRET rejected by the 20.0 FR_SIRET validator raises
        ValidationError and the whole write is rejected (19.0 stored it as-is)."""
        wizard = self._open_wizard([_result(nom_complet='BAD CO', siret='12345678900012')])
        row = wizard.result_ids[0]
        with self.assertRaises(ValidationError):
            with self.env.cr.savepoint():
                row.with_context(active_id=self.partner.id).select_siret()
        self.assertEqual(self.partner.name, 'ACME')
        self.assertFalse(self.partner._get_additional_identifier('FR_SIRET'))

    def test_select_keeps_other_identifiers_and_deduces_siren(self):
        """AC-04-05 [MF-02 deviation b] — Select overwrites FR_SIRET, FR_SIREN is re-deduced from
        the new SIRET, and other stored identifiers are left untouched."""
        self.partner.additional_identifiers = {'HK_BRN': '12345678', 'FR_SIRET': OTHER_VALID_SIRET}
        self.assertEqual(self.partner.additional_identifiers.get('FR_SIREN'), OTHER_VALID_SIRET[:9])
        wizard = self._open_wizard([_result(nom_complet='NEW CO', siret=VALID_SIRET)])
        wizard.result_ids[0].with_context(active_id=self.partner.id).select_siret()
        identifiers = self.partner.additional_identifiers
        self.assertEqual(identifiers['FR_SIRET'], VALID_SIRET)
        self.assertEqual(identifiers['FR_SIREN'], VALID_SIRET[:9])
        self.assertEqual(identifiers['HK_BRN'], '12345678')

    def test_select_empty_siret_clears_fr_siret(self):
        """AC-04-01 edge (BSL-004) — an etablissement without SIRET clears FR_SIRET, like 19.0
        writing '' to company_registry."""
        self.partner.additional_identifiers = {'FR_SIRET': OTHER_VALID_SIRET}
        etab = {'siret': '', 'adresse': '1 RUE X 75001', 'code_postal': '75001', 'date_fermeture': False}
        wizard = self._open_wizard([_result(matching_etablissements=[etab])])
        wizard.result_ids.matching_etablissements.with_context(active_id=self.partner.id).select_siret()
        self.assertFalse(self.partner._get_additional_identifier('FR_SIRET'))

    def test_result_without_etablissements_uses_siege(self):
        """AC-05-04 (BSL-028) — no matching_etablissements -> one etablissement built from siege."""
        wizard = self._open_wizard([_result(matching_etablissements=[])])
        matching = wizard.result_ids.matching_etablissements
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching.siret, VALID_SIRET)
        self.assertEqual(matching.adresse, '10 rue de la Paix')
