import logging
from unittest.mock import MagicMock, patch

import requests

from lxml import etree

from odoo.exceptions import UserError, ValidationError
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
        # MF-03 workaround (dev-approved 2026-09-24): 19.0 'is_company != True' -> 'parent_id'
        self.assertEqual(button.get('invisible'), 'parent_id')
        wrapper = button.getparent()
        self.assertEqual(wrapper.tag, 'div')
        self.assertIsNone(wrapper.get('invisible'))
        self.assertEqual(wrapper.getparent().tag, 'h1')
        names = wrapper.xpath("./field[@name='name']")
        self.assertEqual(len(names), 1)
        self.assertIsNone(names[0].get('invisible'))
        self.assertEqual(wrapper.index(names[0]), 0, "name field must come before the button")

    def test_no_font_awesome_icons_rmv01(self):
        """RMV-01 (Step 10 Cross-Version Compare) — 20.0 dropped Font Awesome: ViewButton renders
        every `icon` as an `oi` ligature, so `icon="fa-..."` shows as a broken glyph and
        `<i class="fa ...">` shows nothing. The module's views must use ligature icon names."""
        partner_arch = self.env['res.partner'].get_view(self.env.ref('base.view_partner_form').id, 'form')['arch']
        button = etree.fromstring(partner_arch).xpath("//button[@name='siret_wizard']")[0]
        self.assertEqual(button.get('icon'), 'search')
        wizard_arch = self.env['siret.wizard'].get_view(self.env.ref('fr_business_directory.view_siret_wizard_form').id, 'form')['arch']
        wizard_tree = etree.fromstring(wizard_arch)
        self.assertEqual(wizard_tree.xpath("//button[@name='fetch_previous_page']")[0].get('icon'), 'arrow_back')
        self.assertTrue(wizard_tree.xpath("//button[@name='fetch_next_page']/i[@data-icon='arrow_forward']"))
        for arch in (partner_arch, wizard_arch):
            tree = etree.fromstring(arch)
            module_nodes = tree.xpath("//button[@name='siret_wizard'] | //button[starts-with(@name, 'fetch_')]//descendant-or-self::*")
            for node in module_nodes:
                self.assertFalse((node.get('icon') or '').startswith('fa-'), etree.tostring(node))
                self.assertNotIn('fa ', (node.get('class') or '') + ' ', etree.tostring(node))

    def test_new_partner_form_contacts_context_is_company(self):
        """AC-01-02 [characterization, MF-03] — is_company (drives the button visibility) on a new
        partner form opened like the Contacts action (default_is_company=True), no VAT: in the
        form after save, and after a VAT is set then removed (kept as evidence for MF-03, which
        still documents WHY the 19.0 condition could not be kept)."""
        form = Form(self.env['res.partner'].with_context(default_is_company=True))
        form.name = 'NEW FRENCH CO'
        partner = form.save()
        after_save = partner.is_company
        partner.vat = 'FR23334175221'
        with_vat = partner.is_company
        partner.vat = False
        vat_removed = partner.is_company
        observed = (after_save, with_vat, vat_removed)
        _logger.info("MF-03 is_company (saved, with VAT, VAT removed) = %s", observed)
        # Observed on 20.0 (G1 #6, 2026-09-24): True in the unsaved form (default_is_company) —
        # no longer readable here since the MF-03 workaround view does not reference is_company —
        # recomputed to False on save because there is no VAT (has_vat), True once a VAT is set,
        # False again when it is removed -> the button disappears after save for a company
        # without VAT. Recorded as MF-03 decision point, not "fixed" here.
        self.assertEqual(observed, (False, True, False))

    def test_button_visibility_workaround_mf03(self):
        """AC-01-01 [MF-03 workaround] — the button condition `invisible="parent_id"` keeps the
        button for a SAVED company without VAT (is_company False in 20.0, the blocker case) and
        still hides it for child contacts, as 19.0 did."""
        form = Form(self.env['res.partner'].with_context(default_is_company=True))
        form.name = 'SAVED CO WITHOUT VAT'
        company = form.save()
        self.assertFalse(company.is_company, "20.0 computes is_company False without VAT")
        self.assertFalse(company.parent_id, "button visible: invisible='parent_id' is falsy")
        child = self.env['res.partner'].create({'name': 'Employee', 'parent_id': company.id})
        self.assertTrue(child.parent_id, "button hidden for child contacts")
        # the wizard itself opens from the saved VAT-less company
        action = company.siret_wizard()
        self.assertEqual(action['context'], {'active_id': company.id})

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


def _mock_429(retry_after='0'):
    resp = MagicMock()
    resp.status_code = 429
    resp.headers = {'Retry-After': retry_after}

    def _raise():
        raise requests.HTTPError('429 Client Error: Too Many Requests', response=resp)
    resp.raise_for_status = _raise
    return resp


@tagged('post_install', '-at_install')
class TestDirectoryApiFixes(TransactionCase):
    """Post-migration fixes approved by the dev on 2026-09-24 (FINDINGS.md RMV-02, RMV-03, RMV-06):
    behavior intentionally differs from 19.0 here."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'ACME', 'is_company': True})
        self.Wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id)

    # --- RMV-03: HTTP 429 / API errors ------------------------------------------------------

    def test_429_is_retried_then_succeeds(self):
        """A 429 is retried (honouring Retry-After, capped) and the next success is used."""
        with patch('requests.get', side_effect=[_mock_429('3'), _mock_response([_result()])]) as mock_get, \
             patch('time.sleep') as mock_sleep:
            wizard = self.Wizard.create({})
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(3.0)
        self.assertEqual(len(wizard.result_ids), 1)

    def test_retry_after_is_capped(self):
        with patch('requests.get', side_effect=[_mock_429('120'), _mock_response([_result()])]), \
             patch('time.sleep') as mock_sleep:
            self.Wizard.create({})
        mock_sleep.assert_called_once_with(5)

    def test_429_persisting_shows_english_busy_message(self):
        """Still 429 after the retries -> readable English UserError, no traceback/NameError."""
        with patch('requests.get', side_effect=[_mock_429(), _mock_429(), _mock_429()]) as mock_get, \
             patch('time.sleep'), \
             self.assertRaises(UserError) as ctx, \
             self.assertLogs('odoo.addons.fr_business_directory.models.siret_wizard', level='ERROR'):
            self.Wizard.create({})
        self.assertEqual(mock_get.call_count, 3)
        self.assertIn('is busy right now', str(ctx.exception))

    def test_connection_error_shows_english_unreachable_message(self):
        with patch('requests.get', side_effect=requests.ConnectionError('no route')), \
             self.assertRaises(UserError) as ctx, \
             self.assertLogs('odoo.addons.fr_business_directory.models.siret_wizard', level='ERROR'):
            self.Wizard.create({})
        self.assertIn('could not be reached', str(ctx.exception))

    def test_429_on_next_page_keeps_wizard_state(self):
        """A failure on Next raises the readable error; the page is not changed."""
        with patch('requests.get', return_value=_mock_response([_result()], total_pages=3)):
            wizard = self.Wizard.create({})
        with patch('requests.get', side_effect=[_mock_429(), _mock_429(), _mock_429()]), patch('time.sleep'), \
             self.assertRaises(UserError), \
             self.assertLogs('odoo.addons.fr_business_directory.models.siret_wizard', level='ERROR'):
            with self.env.cr.savepoint():
                wizard.fetch_next_page()
        self.assertEqual(wizard.page_number, 1)

    # --- RMV-06: no duplicate API call when the wizard is saved -------------------------------

    def test_open_calls_api_once_and_save_does_not_call_it_again(self):
        """Opening the dialog (default_get with result_ids) calls the API once; saving it like the
        20.0 web client does (result_ids + force_save'd counters sent) does not call it again."""
        with patch('requests.get', return_value=_mock_response([_result()], total_results=40, total_pages=2)) as mock_get:
            defaults = self.Wizard.default_get(['result_ids', 'result_count', 'page_number', 'total_pages', 'partner_name'])
        self.assertEqual(mock_get.call_count, 1)
        with patch('requests.get') as mock_get:
            wizard = self.Wizard.create({
                'result_ids': [(6, 0, defaults['result_ids'][0][2])],
                'result_count': defaults['result_count'],
                'page_number': 1,
                'total_pages': defaults['total_pages'],
            })
        mock_get.assert_not_called()
        self.assertEqual(wizard.partner_name, 'ACME')
        self.assertEqual(wizard.total_pages, 2)
        self.assertEqual(len(wizard.result_ids), 1)

    def test_wizard_view_sends_readonly_counters(self):
        """The read-only counters are force_save'd so they reach create()."""
        arch = self.env['siret.wizard'].get_view(self.env.ref('fr_business_directory.view_siret_wizard_form').id, 'form')['arch']
        tree = etree.fromstring(arch)
        for fname in ('result_count', 'page_number', 'total_pages'):
            node = tree.xpath(f"//field[@name='{fname}']")[0]
            self.assertEqual(node.get('force_save'), '1', fname)

    # --- RMV-02: Select after pagination writes to the original partner -----------------------

    def test_pagination_actions_keep_active_id(self):
        with patch('requests.get', return_value=_mock_response([_result()], total_pages=3)):
            wizard = self.Wizard.create({})
            actions = [wizard.fetch_next_page(), wizard.fetch_previous_page(), wizard.fetch_previous_page()]
            wizard.page_number = wizard.total_pages
            actions.append(wizard.fetch_next_page())
        for action in actions:
            self.assertEqual(action['context'].get('active_id'), self.partner.id)

    def test_select_after_pagination_writes_original_partner(self):
        """Replays the web client: the reloaded dialog uses the returned action's context."""
        other = self.env['res.partner'].create({'name': 'MUST NOT CHANGE', 'street': 'Jl. Sudirman 1'})
        with patch('requests.get', return_value=_mock_response([_result(nom_complet='PAGE TWO CO')], total_pages=3)):
            wizard = self.Wizard.create({})
            action = wizard.fetch_next_page()
        reloaded = self.env['siret.wizard'].with_context(**action['context']).browse(action['res_id'])
        row = reloaded.result_ids[0]
        row.with_context(**action['context']).select_siret()
        self.assertEqual(self.partner.name, 'PAGE TWO CO')
        self.assertEqual(other.name, 'MUST NOT CHANGE')

    # --- RMV-05: null values from the API must not crash the wizard ---------------------------

    def test_null_libelle_voie_does_not_crash(self):
        """RMV-05 — the API sends `"libelle_voie": null` for some companies (e.g. "CARREFOUR" page
        2): 16.0-19.0 raised TypeError ("can only concatenate str (not NoneType)")."""
        with patch('requests.get', return_value=_mock_response([_result(libelle_voie=None, matching_etablissements=[])])):
            wizard = self.Wizard.create({})
        self.assertEqual(len(wizard.result_ids), 1)
        self.assertEqual(wizard.result_ids.street, '10 ')
        self.assertEqual(wizard.result_ids.matching_etablissements.adresse, '10 ')

    def test_select_etablissement_without_postal_code_does_not_crash(self):
        """RMV-05 — an etablissement without postal code (or address) can be selected."""
        etab = {'siret': '33417522101010', 'adresse': '1 RUE X', 'code_postal': None, 'date_fermeture': False}
        with patch('requests.get', return_value=_mock_response([_result(matching_etablissements=[etab])])):
            wizard = self.Wizard.create({})
        wizard.result_ids.matching_etablissements.with_context(active_id=self.partner.id).select_siret()
        self.assertEqual(self.partner.street, '1 RUE X')
        self.assertFalse(self.partner.zip)
