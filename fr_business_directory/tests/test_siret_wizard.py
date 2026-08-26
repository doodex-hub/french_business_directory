from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase, tagged


def _mock_response(results, total_results=None, total_pages=1):
    resp = MagicMock()
    resp.raise_for_status = lambda: None
    resp.json.return_value = {
        'results': results,
        'total_results': total_results if total_results is not None else len(results),
        'total_pages': total_pages,
    }
    return resp


def _siege(**overrides):
    base = {
        'siret': '12345678900012',
        'etat_administratif': 'A',
        'numero_voie': '10',
        'libelle_voie': 'rue de la Paix',
        'complement_adresse': '',
        'libelle_commune': 'Paris',
        'departement': '75',
        'code_postal': '75002',
        'region': 'Ile-de-France',
        'latitude': '48.8',
        'longitude': '2.3',
        'date_creation': '2000-01-01',
        'date_debut_activite': '2000-01-01',
        'date_fermeture': False,
        'activite_principale': '68.20Z',
    }
    base.update(overrides)
    return base


def _result(nom_complet='ACME SAS', nom_raison_sociale='ACME', matching_etablissements=None, **siege_overrides):
    return {
        'nom_complet': nom_complet,
        'nom_raison_sociale': nom_raison_sociale,
        'siege': _siege(**siege_overrides),
        'matching_etablissements': matching_etablissements or [],
    }


@tagged('post_install', '-at_install')
class TestSiretWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'ACME',
            'is_company': True,
        })

    def test_auto_fetch_on_wizard_open(self):
        """AC-02-01 — default_get() auto-fetches page 1 from partner name."""
        with patch('requests.get', return_value=_mock_response([_result()])) as mock_get:
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
        self.assertTrue(mock_get.called)
        called_url = mock_get.call_args[0][0]
        self.assertIn('q=ACME', called_url)
        self.assertIn('page=1', called_url)
        self.assertIn('per_page=25', called_url)
        self.assertIn('limite_matching_etablissements=100', called_url)
        self.assertEqual(len(wizard.result_ids), 1)
        self.assertEqual(wizard.result_ids.name, 'ACME SAS')

    def test_pagination_wraparound_next(self):
        """AC-03-01 — Next on last page wraps to page 1."""
        with patch('requests.get', return_value=_mock_response([_result()], total_pages=3)):
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
        wizard.page_number = 3
        wizard.total_pages = 3
        with patch('requests.get', return_value=_mock_response([_result()], total_pages=3)):
            wizard.fetch_next_page()
        self.assertEqual(wizard.page_number, 1)

    def test_pagination_wraparound_prev(self):
        """AC-03-02 — Prev on page 1 wraps to last page."""
        with patch('requests.get', return_value=_mock_response([_result()], total_pages=3)):
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
        wizard.page_number = 1
        wizard.total_pages = 3
        with patch('requests.get', return_value=_mock_response([_result()], total_pages=3)):
            wizard.fetch_previous_page()
        self.assertEqual(wizard.page_number, 3)

    def test_prev_page_missing_limite_param_preserved_bug(self):
        """AC-03-03 [PRESERVE-BUG] BSL-009 — limite_matching_etablissements absent on Prev URL."""
        with patch('requests.get', return_value=_mock_response([_result()], total_pages=3)):
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
        wizard.page_number = 2
        wizard.total_pages = 3
        with patch('requests.get', return_value=_mock_response([_result()], total_pages=3)) as mock_get:
            wizard.fetch_previous_page()
        called_url = mock_get.call_args[0][0]
        self.assertNotIn('limite_matching_etablissements', called_url)

    def test_next_page_has_limite_param(self):
        """Control case for AC-03-03 — Next URL DOES include the param."""
        with patch('requests.get', return_value=_mock_response([_result()], total_pages=3)):
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
        wizard.page_number = 1
        wizard.total_pages = 3
        with patch('requests.get', return_value=_mock_response([_result()], total_pages=3)) as mock_get:
            wizard.fetch_next_page()
        called_url = mock_get.call_args[0][0]
        self.assertIn('limite_matching_etablissements=100', called_url)

    def test_empty_partner_name_is_noop(self):
        """AC-03-04 [PRESERVE-BUG] BSL-010 — empty partner_name -> implicit None, no crash."""
        with patch('requests.get', return_value=_mock_response([])):
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
        wizard.partner_name = False
        wizard.page_number = 1
        wizard.total_pages = 3
        result = wizard.fetch_next_page()
        self.assertIsNone(result)

    def test_select_result_overwrites_partner(self):
        """AC-04-01 — select_siret() on a result row overwrites partner fields.

        `res.partner.siret` (dedicated l10n_fr field in 18.0) was removed in 19.0 and
        consolidated into the generic core field `company_registry` (see DIFF-02, MF-02) —
        assert against `company_registry`, not `siret`.
        """
        with patch('requests.get', return_value=_mock_response([_result(nom_complet='NEW CO')])):
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
        row = wizard.result_ids[0]
        row.with_context(active_id=self.partner.id).select_siret()
        self.assertEqual(self.partner.name, 'NEW CO')
        self.assertEqual(self.partner.company_registry, '12345678900012')
        self.assertEqual(self.partner.city, 'Paris')

    def test_select_department_field_untouched_when_model_absent(self):
        """AC-04-03 — res.country.department not installed -> department/state/country untouched, no crash."""
        self.assertFalse(self.env['ir.model'].search([('model', '=', 'res.country.department')]))
        with patch('requests.get', return_value=_mock_response([_result()])):
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
        state_before = self.partner.state_id
        row = wizard.result_ids[0]
        row.with_context(active_id=self.partner.id).select_siret()
        self.assertEqual(self.partner.state_id, state_before)

    def test_select_department_field_filled_when_model_present(self):
        """AC-04-02 — only runs if res.country.department is actually installed (third-party, see MF-01)."""
        if not self.env['ir.model'].search([('model', '=', 'res.country.department')]):
            self.skipTest("res.country.department not installed in this environment (MF-01, third-party OCA dependency not connected)")

    def test_status_label_active(self):
        """AC-05-01 — etat_administratif 'A' -> 'en activité'."""
        with patch('requests.get', return_value=_mock_response([_result(etat_administratif='A')])):
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
        self.assertEqual(wizard.result_ids.etat_administratif, 'en activité')

    def test_status_label_closed(self):
        """AC-05-02 — etat_administratif != 'A' -> 'fermé le'."""
        with patch('requests.get', return_value=_mock_response([_result(etat_administratif='F')])):
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
        self.assertEqual(wizard.result_ids.etat_administratif, 'fermé le')

    def test_activite_principale_translation_known_code(self):
        """AC-05-03 — last letter 'A' translated to French label.

        Note: `_compute_activite_principale` on `matching.etablissement` reads
        `result_id.activite_principale` (the parent siret.wizard.result / siege-level value),
        NOT the etablissement's own `activite_principale` field — confirmed by direct testing,
        not obvious from the old backfill spec wording (BR-07). Vary `_siege()` here, not the
        etablissement dict, to exercise the real dependency.
        """
        etab = {'siret': '99988877700011', 'adresse': '', 'code_postal': '', 'date_fermeture': False}
        with patch('requests.get', return_value=_mock_response([_result(matching_etablissements=[etab], activite_principale='68.20A')])):
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
        matching = wizard.result_ids.matching_etablissements
        self.assertIn('Location de logements', matching.computed_activite_principale)

    def test_activite_principale_translation_unknown_code_passthrough(self):
        """AC-05-03 — code not in {A,B,Z,D} is shown raw, not a bug."""
        etab = {'siret': '99988877700022', 'adresse': '', 'code_postal': '', 'date_fermeture': False}
        with patch('requests.get', return_value=_mock_response([_result(matching_etablissements=[etab], activite_principale='68.20X')])):
            wizard = self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
        matching = wizard.result_ids.matching_etablissements
        self.assertEqual(matching.computed_activite_principale, '68.20X')

    def test_matching_etablissement_missing_date_fermeture_key_crashes(self):
        """MF-09 [new finding] — if 'date_fermeture' key is entirely ABSENT from an API
        matching_etablissements entry (not just empty/false), the code's `.get('date_fermeture', '')`
        fallback writes an empty string to a Date field, which Postgres rejects. Reproduces with
        unmodified source logic (not caused by this migration) — documented, not fixed (P1)."""
        etab_missing_key = {'activite_principale': '68.20A', 'siret': '99988877700033', 'adresse': '', 'code_postal': ''}
        with self.assertRaises(Exception):
            with patch('requests.get', return_value=_mock_response([_result(matching_etablissements=[etab_missing_key])])):
                self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})

    def test_social_reason_field_tracked(self):
        """AC-06-01 — social_reason field is defined with tracking=True."""
        field = self.env['res.partner']._fields['social_reason']
        self.assertTrue(field.tracking)

    def test_logger_undefined_nameerror_preserved_bug(self):
        """AC-07-01 [PRESERVE-BUG] BSL-008 — malformed API response (missing siret) raises NameError, not a handled log."""
        bad_result = _result(nom_complet='', matching_etablissements=[])
        bad_result['siege']['siret'] = ''
        with patch('requests.get', return_value=_mock_response([bad_result])):
            with self.assertRaises(NameError):
                self.env['siret.wizard'].with_context(active_id=self.partner.id).create({})
