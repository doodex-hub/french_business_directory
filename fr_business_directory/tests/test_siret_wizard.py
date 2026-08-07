# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase, tagged


def _fake_api_response(page=1, total_pages=2, with_matching=True):
    """Build a canned recherche-entreprises.api.gouv.fr response, shaped like the real payload."""
    matching = [{
        'activite_principale': '68.20A',
        'adresse': '10 rue de la Paix',
        'code_postal': '75002',
        'date_creation': '2010-01-01',
        'date_debut_activite': '2010-01-01',
        'date_fermeture': False,
        'latitude': '48.8',
        'libelle_commune': 'Paris',
        'longitude': '2.3',
        'siret': '12345678900011',
        'etat_administratif': 'A',
    }] if with_matching else []
    return {
        'results': [{
            'nom_complet': 'ACME SARL',
            'nom_raison_sociale': 'ACME',
            'siege': {
                'siret': '12345678900010',
                'etat_administratif': 'A',
                'numero_voie': '1',
                'libelle_voie': 'rue de la Paix',
                'complement_adresse': '',
                'libelle_commune': 'Paris',
                'departement': '75',
                'code_postal': '75002',
                'region': 'Ile-de-France',
                'latitude': '48.8',
                'longitude': '2.3',
                'date_creation': '2010-01-01',
                'date_debut_activite': '2010-01-01',
                'date_fermeture': False,
                'activite_principale': '68.20A',
            },
            'matching_etablissements': matching,
        }],
        'total_results': 1,
        'total_pages': total_pages,
    }


class TestSiretWizardBase(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'ACME SARL',
            'is_company': True,
        })


@tagged('post_install', '-at_install')
class TestSiretWizardFetch(TestSiretWizardBase):
    """AC-02, AC-03 — default_get auto-fetch + pagination."""

    def test_default_get_auto_fetches_first_page(self):
        """AC-02-01: opening the wizard from a partner auto-fetches page 1 and fills result_ids."""
        fake_resp = MagicMock()
        fake_resp.json.return_value = _fake_api_response()
        fake_resp.raise_for_status.return_value = None
        with patch('odoo.addons.fr_business_directory.models.siret_wizard.requests.get',
                   return_value=fake_resp) as mock_get:
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})

        self.assertEqual(wizard.partner_name, 'ACME SARL')
        self.assertEqual(wizard.result_count, 1)
        self.assertEqual(wizard.total_pages, 2)
        self.assertEqual(len(wizard.result_ids), 1)
        self.assertEqual(wizard.result_ids[0].siret, '12345678900010')
        self.assertEqual(len(wizard.result_ids[0].matching_etablissements), 1)
        called_url = mock_get.call_args[0][0]
        self.assertIn('q=ACME%20SARL', called_url)
        self.assertIn('page=1', called_url)

    def test_fetch_next_page_advances_and_calls_api_with_limite_param(self):
        """AC-03-01: Next advances page_number and requests the new page, including
        limite_matching_etablissements (present in fetch_next_page's URL)."""
        wizard = self.env['siret.wizard'].create({
            'partner_name': 'ACME SARL',
            'page_number': 1,
            'total_pages': 3,
        })
        fake_resp = MagicMock()
        fake_resp.json.return_value = _fake_api_response(page=2, total_pages=3)
        fake_resp.raise_for_status.return_value = None
        with patch('odoo.addons.fr_business_directory.models.siret_wizard.requests.get',
                   return_value=fake_resp) as mock_get:
            wizard.fetch_next_page()

        self.assertEqual(wizard.page_number, 2)
        called_url = mock_get.call_args[0][0]
        self.assertIn('page=2', called_url)
        self.assertIn('limite_matching_etablissements=100', called_url)

    def test_fetch_next_page_wraps_to_first_page_after_last(self):
        """AC-03-02: clicking Next on the last page wraps back to page 1 (not disabled)."""
        wizard = self.env['siret.wizard'].create({
            'partner_name': 'ACME SARL',
            'page_number': 3,
            'total_pages': 3,
        })
        fake_resp = MagicMock()
        fake_resp.json.return_value = _fake_api_response(page=1, total_pages=3)
        fake_resp.raise_for_status.return_value = None
        with patch('odoo.addons.fr_business_directory.models.siret_wizard.requests.get',
                   return_value=fake_resp):
            wizard.fetch_next_page()

        self.assertEqual(wizard.page_number, 1)

    def test_fetch_previous_page_wraps_to_last_page_before_first(self):
        """AC-03-03: clicking Prev on page 1 wraps to the last page."""
        wizard = self.env['siret.wizard'].create({
            'partner_name': 'ACME SARL',
            'page_number': 1,
            'total_pages': 3,
        })
        fake_resp = MagicMock()
        fake_resp.json.return_value = _fake_api_response(page=3, total_pages=3)
        fake_resp.raise_for_status.return_value = None
        with patch('odoo.addons.fr_business_directory.models.siret_wizard.requests.get',
                   return_value=fake_resp):
            wizard.fetch_previous_page()

        self.assertEqual(wizard.page_number, 3)

    def test_fetch_previous_page_missing_limite_param_F02(self):
        """F-02 / AC-03-04: fetch_previous_page's URL does NOT include
        limite_matching_etablissements, unlike fetch_next_page's — documenting the
        inconsistency found in models/siret_wizard.py (not asserting it is correct)."""
        wizard = self.env['siret.wizard'].create({
            'partner_name': 'ACME SARL',
            'page_number': 2,
            'total_pages': 3,
        })
        fake_resp = MagicMock()
        fake_resp.json.return_value = _fake_api_response(page=1, total_pages=3)
        fake_resp.raise_for_status.return_value = None
        with patch('odoo.addons.fr_business_directory.models.siret_wizard.requests.get',
                   return_value=fake_resp) as mock_get:
            wizard.fetch_previous_page()

        called_url = mock_get.call_args[0][0]
        self.assertNotIn('limite_matching_etablissements', called_url,
                          "fetch_previous_page currently omits this param (F-02) — "
                          "this assertion documents the bug, update it once F-02 is fixed")

    def test_fetch_next_page_noop_when_partner_name_empty_F03(self):
        """F-03 / AC-03-05: with an empty partner_name, fetch_next_page silently no-ops
        (returns None, no API call, no state change)."""
        wizard = self.env['siret.wizard'].create({
            'partner_name': False,
            'page_number': 1,
            'total_pages': 3,
        })
        with patch('odoo.addons.fr_business_directory.models.siret_wizard.requests.get') as mock_get:
            result = wizard.fetch_next_page()

        self.assertIsNone(result)
        mock_get.assert_not_called()
        self.assertEqual(wizard.page_number, 1)


@tagged('post_install', '-at_install')
class TestSiretWizardErrorHandling(TestSiretWizardBase):
    """F-01 / AC-02-02 — _logger is used but never imported in siret_wizard.py."""

    def test_fetch_siret_data_request_exception_raises_nameerror_F01(self):
        """When the external API call fails, _fetch_siret_data tries to log the error via
        _logger, which does not exist in this module -> NameError instead of a clean log.
        This test documents the current (buggy) behavior; it should be updated to assert
        a clean log (no exception) once F-01 is fixed."""
        import requests as requests_module
        with patch('odoo.addons.fr_business_directory.models.siret_wizard.requests.get',
                   side_effect=requests_module.RequestException('boom')):
            with self.assertRaises(NameError):
                self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})

    def test_fetch_siret_data_missing_siret_in_valid_siege_raises_nameerror_F01(self):
        """Same root cause (F-01), different trigger: verified against the real code (not
        just a read) that the `else` at line 112-113 is paired with `if name and siret:`
        (line 57), NOT with `if isinstance(siege, dict):` (line 51) -- so _logger.warning
        only fires when `siege` IS a valid dict but `nom_complet`/`siege.siret` is missing.
        A `siege` that is not a dict at all takes a different, silent path (see
        test_fetch_siret_data_siege_not_a_dict_is_silently_skipped below)."""
        fake_resp = MagicMock()
        fake_resp.raise_for_status.return_value = None
        fake_resp.json.return_value = {
            'results': [{'nom_complet': '', 'siege': {'siret': ''}, 'matching_etablissements': []}],
            'total_results': 1,
            'total_pages': 1,
        }
        with patch('odoo.addons.fr_business_directory.models.siret_wizard.requests.get',
                   return_value=fake_resp):
            with self.assertRaises(NameError):
                self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})

    def test_fetch_siret_data_siege_not_a_dict_is_silently_skipped(self):
        """AC-02-03: when 'siege' is not a dict at all, there is no `else` branch for that
        `isinstance` check -- the result is silently dropped, with no NameError, no log,
        no indication at all (a separate, quieter gap from F-01's NameError path)."""
        fake_resp = MagicMock()
        fake_resp.raise_for_status.return_value = None
        fake_resp.json.return_value = {
            'results': [{'nom_complet': 'X', 'siege': 'not-a-dict', 'matching_etablissements': []}],
            'total_results': 1,
            'total_pages': 1,
        }
        with patch('odoo.addons.fr_business_directory.models.siret_wizard.requests.get',
                   return_value=fake_resp):
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})

        self.assertEqual(len(wizard.result_ids), 0,
                          "the malformed result is dropped silently, not surfaced as an error")


@tagged('post_install', '-at_install')
class TestSiretWizardSelectSiret(TestSiretWizardBase):
    """AC-04 — select_siret writes the chosen candidate onto res.partner."""

    def test_select_siret_from_result_writes_partner_F05_no_department_model(self):
        """AC-04-01 + AC-04-03: writing from the result-level record overwrites the partner
        fields; country_department_id/state_id/country_id are left untouched because
        res.country.department does not exist in a vanilla odoo:17.0 + base/contacts/l10n_fr
        install (F-05)."""
        wizard = self.env['siret.wizard'].create({'partner_name': 'ACME SARL'})
        result = self.env['siret.wizard.result'].create({
            'wizard_id': wizard.id,
            'name': 'ACME SARL',
            'social_reason': 'ACME',
            'siret': '12345678900010',
            'street': '1 rue de la Paix',
            'street2': '',
            'post_code': '75002',
            'department': '75',
            'city': 'Paris',
            'latitude': '48.8',
            'longitude': '2.3',
        })

        has_department_model = bool(self.env['ir.model'].search([('model', '=', 'res.country.department')]))
        self.assertFalse(has_department_model,
                          "This test documents the F-05 branch (model absent); if a future "
                          "environment installs the department addon, AC-04-04 applies instead.")

        result.with_context(active_id=self.partner.id).select_siret()

        self.assertEqual(self.partner.name, 'ACME SARL')
        self.assertEqual(self.partner.siret, '12345678900010')
        self.assertEqual(self.partner.street, '1 rue de la Paix')
        self.assertEqual(self.partner.zip, '75002')
        self.assertEqual(self.partner.city, 'Paris')
        self.assertEqual(self.partner.social_reason, 'ACME')
        self.assertFalse(self.partner.state_id)

    def test_select_siret_from_etablissement_splits_address(self):
        """AC-04-02: the etablissement-level select_siret splits the address on the postal
        code (_split_address) instead of using separate street/street2 fields."""
        wizard = self.env['siret.wizard'].create({'partner_name': 'ACME SARL'})
        result = self.env['siret.wizard.result'].create({'wizard_id': wizard.id, 'name': 'ACME SARL'})
        etab = self.env['matching.etablissement'].create({
            'result_id': result.id,
            'siret': '12345678900011',
            'adresse': '10 rue de la Paix 75002 Paris',
            'code_postal': '75002',
            'city': 'Paris',
            'latitude': 48.8,
            'longitude': 2.3,
        })

        etab.with_context(active_id=self.partner.id).select_siret()

        self.assertEqual(self.partner.siret, '12345678900011')
        self.assertEqual(self.partner.street, '10 rue de la Paix')
        self.assertEqual(self.partner.zip, '75002')
        self.assertEqual(self.partner.city, 'Paris')


@tagged('post_install', '-at_install')
class TestMatchingEtablissementCompute(TransactionCase):
    """AC-05 — computed display fields."""

    def test_etat_administratif_display_open(self):
        result = self.env['siret.wizard.result'].create({'name': 'ACME'})
        etab = self.env['matching.etablissement'].create({
            'result_id': result.id,
            'etat_administratif': 'en activité',
        })
        self.assertEqual(etab.etat_administratif_display, 'en activité')

    def test_etat_administratif_display_closed_includes_date(self):
        result = self.env['siret.wizard.result'].create({'name': 'ACME'})
        etab = self.env['matching.etablissement'].create({
            'result_id': result.id,
            'etat_administratif': 'fermé le',
            'date_fermeture': '2020-01-01',
        })
        self.assertIn('fermé le', etab.etat_administratif_display)
        self.assertIn('2020-01-01', etab.etat_administratif_display)

    def test_activite_principale_known_letter_translated(self):
        result = self.env['siret.wizard.result'].create({'name': 'ACME', 'activite_principale': '68.20A'})
        etab = self.env['matching.etablissement'].create({'result_id': result.id})
        self.assertIn('Location de logements', etab.computed_activite_principale)
        self.assertIn('68.20A', etab.computed_activite_principale)

    def test_activite_principale_unmapped_letter_passthrough(self):
        """Codes ending in a letter not in {A, B, Z, D} are shown raw, untranslated
        (documented gap, not a bug — see BR-07)."""
        result = self.env['siret.wizard.result'].create({'name': 'ACME', 'activite_principale': '68.20C'})
        etab = self.env['matching.etablissement'].create({'result_id': result.id})
        self.assertEqual(etab.computed_activite_principale, '68.20C')
