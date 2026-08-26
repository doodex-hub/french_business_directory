from odoo import fields, models, api, _
import requests
import urllib

class SiretWizard(models.TransientModel):
    _name = 'siret.wizard'
    _description = 'Siret Wizard'

    result_ids = fields.One2many('siret.wizard.result', 'wizard_id', string='Results')
    result_count = fields.Integer(string='Result Count')
    page_number = fields.Integer(string='Page Number', default=1)
    partner_name = fields.Char(string='Partner Name')
    page_count = fields.Integer(default=1)
    total_pages = fields.Integer(string='Total Pages')

    @api.depends('result_ids')
    def _compute_result_count(self):
        for wizard in self:
            wizard.result_count = len(wizard.result_ids)

    @api.model
    def default_get(self, fields):
        res = super(SiretWizard, self).default_get(fields)
        active_id = self._context.get('active_id')

        if active_id:
            partner = self.env['res.partner'].browse(active_id)
            res['partner_name'] = partner.name
            search_name = urllib.parse.quote(str(partner.name))  # Ensure partner.name is a string

            api_url = f"https://recherche-entreprises.api.gouv.fr/search?q={search_name}&page=1&per_page=25&limite_matching_etablissements=100"
            self._fetch_siret_data(api_url, res)

        return res

    def _fetch_siret_data(self, api_url, res=None):
        try:
            response = requests.get(api_url)
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])
            total_results = data.get('total_results', 0)
            total_pages = data.get('total_pages', 0)

            result_records = []
            for result in results:
                siege = result.get('siege', {})
                matching_etablissements_data = result.get('matching_etablissements', [])

                if isinstance(siege, dict):
                    name = result.get('nom_complet', '')
                    nom_raison_sociale = result.get('nom_raison_sociale', '')
                    siret = siege.get('siret', '')
                    etat_administratif = siege.get('etat_administratif', '')
                    etat_administratif_status = 'en activité' if etat_administratif == 'A' else 'fermé le'
                    if name and siret:
                        matching_etablissements = []
                        for me in matching_etablissements_data:
                            # Adjust fields according to the structure of matching_etablissements
                            matching_etablissements.append((0, 0, {
                                # Assuming these are the fields within matching_etablissements
                                'activite_principale': me.get('activite_principale', ''),
                                'adresse': me.get('adresse', ''),
                                'code_postal': me.get('code_postal', ''),
                                'date_creation': me.get('date_creation', ''),
                                'date_debut_activite': me.get('date_debut_activite', ''),
                                'date_fermeture': me.get('date_fermeture', ''),
                                'latitude': me.get('latitude', ''),
                                'city': me.get('libelle_commune', ''),
                                "longitude": me.get('longitude', ''),
                                "siret": me.get('siret', ''),
                                'etat_administratif': 'en activité' if me.get('etat_administratif') == 'A' else 'fermé le',
                                # Add other relevant fields
                            }))

                        # If no matching_etablissements, fill it with data from the result itself
                        if not matching_etablissements:
                            matching_etablissements.append((0, 0, {
                                'activite_principale': siege.get('activite_principale', ''),
                                'adresse': str(siege.get('numero_voie', '')) + " " + siege.get('libelle_voie', ''),
                                'code_postal': siege.get('code_postal', ''),
                                'date_creation': siege.get('date_creation', ''),
                                'date_debut_activite': siege.get('date_debut_activite', ''),
                                'date_fermeture': siege.get('date_fermeture', ''),
                                'latitude': siege.get('latitude', ''),
                                'city': siege.get('libelle_commune', ''),
                                "longitude": siege.get('longitude', ''),
                                "siret": siege.get('siret', ''),
                                "etat_administratif": etat_administratif_status
                            }))

                        result_records.append({
                            'name': name,
                            'social_reason': nom_raison_sociale,
                            'siret': siret,
                            'street': str(siege.get('numero_voie', '')) + " " + siege.get('libelle_voie', ''),
                            'street2': siege.get('complement_adresse', ''),
                            'city': siege.get('libelle_commune', ''),
                            'department': siege.get('departement', ''),
                            'post_code': siege.get('code_postal', ''),
                            'region': siege.get('region', ''),
                            'latitude': siege.get('latitude', ''),
                            'longitude': siege.get('longitude', ''),
                            'date_creation': siege.get('date_creation', ''),
                            'date_debut_activite': siege.get('date_debut_activite', ''),
                            'date_fermeture': siege.get('date_fermeture', ''),
                            'activite_principale': siege.get('activite_principale', ''),
                            'etat_administratif': etat_administratif_status,
                            'matching_etablissements': matching_etablissements
                        })
                    else:
                        _logger.warning(f"Unexpected structure for 'siege': {siege}")

            # Create new result records
            created_results = self.env['siret.wizard.result'].create(result_records)

            if res is not None:
                # Set result_ids to the IDs of the newly created records
                res['result_ids'] = [(6, 0, created_results.ids)]
                res['result_count'] = total_results
                res['total_pages'] = total_pages
            else:
                # Replace the current results with the new ones
                self.result_ids = [(6, 0, created_results.ids)]

        except requests.RequestException as e:
            _logger.error(f"Error fetching SIRET data: {e}")


    def fetch_next_page(self):
        self.ensure_one()  # Ensure the method is being called on a single record

        if self.page_number < self.total_pages:
            if self.partner_name:
                search_name = urllib.parse.quote(str(self.partner_name))
                self.page_number += 1
                self.result_ids.unlink()

                api_url = f"https://recherche-entreprises.api.gouv.fr/search?q={search_name}&page={self.page_number}&per_page=25&limite_matching_etablissements=100"
                print(api_url)
                self._fetch_siret_data(api_url)

                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'siret.wizard',
                    'view_mode': 'form',
                    'res_id': self.id,
                    'target': 'new',
                }
        else:
            search_name = urllib.parse.quote(str(self.partner_name))
            self.page_number = 1
            self.result_ids.unlink()

            api_url = f"https://recherche-entreprises.api.gouv.fr/search?q={search_name}&page={self.page_number}&per_page=25&limite_matching_etablissements=100"
            print(api_url)
            self._fetch_siret_data(api_url)

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'siret.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
            }

    def fetch_previous_page(self):
        self.ensure_one()  # Ensure the method is being called on a single record

        if self.page_number > 1:
            if self.partner_name:
                search_name = urllib.parse.quote(str(self.partner_name))
                self.page_number -= 1
                self.result_ids.unlink()

                api_url = f"https://recherche-entreprises.api.gouv.fr/search?q={search_name}&page={self.page_number}&per_page=25"
                print(api_url)
                self._fetch_siret_data(api_url)

                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'siret.wizard',
                    'view_mode': 'form',
                    'res_id': self.id,
                    'target': 'new',
                }
        else:
            if self.partner_name:
                search_name = urllib.parse.quote(str(self.partner_name))
                self.page_number = self.total_pages
                print(self.page_count)
                self.result_ids.unlink()

                api_url = f"https://recherche-entreprises.api.gouv.fr/search?q={search_name}&page={self.page_number}&per_page=25"
                print(api_url)
                self._fetch_siret_data(api_url)

                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'siret.wizard',
                    'view_mode': 'form',
                    'res_id': self.id,
                    'target': 'new',
                }


class SiretWizardResult(models.TransientModel):
    _name = 'siret.wizard.result'
    _description = 'Siret Wizard Result'

    wizard_id = fields.Many2one('siret.wizard', string='Wizard')
    activite_principale = fields.Char(string='Core Bussines')
    name = fields.Char(string='Name')
    social_reason = fields.Char(string='Social Reason')
    post_code = fields.Char(string='Post Code')
    department = fields.Char(string='Department')
    date_creation = fields.Char(string='Date Creation')
    date_debut_activite = fields.Char(string='Activity Start Date')
    date_fermeture = fields.Date(string="Closing Date")
    region = fields.Char(string='Region')
    siret = fields.Char(string='Siret')
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    latitude = fields.Char(string='Latitude')
    longitude = fields.Char(string='Longitude')
    city = fields.Char(string="City")
    matching_etablissements = fields.One2many(
        comodel_name='matching.etablissement',
        inverse_name='result_id',
        string='Matching Establishments'
    )
    etat_administratif = fields.Char(string='Administratif Status')
    result_count = fields.Integer(string='Result Count', compute='_compute_result_count')

    @api.depends('matching_etablissements')
    def _compute_result_count(self):
        for record in self:
            record.result_count = len(record.matching_etablissements)

    @api.model
    def default_get(self, fields):
        res = super(SiretWizardResult, self).default_get(fields)
        # Get the active wizard ID from the context
        wizard_active_id = self._context.get('wizard_active_id')
        if wizard_active_id:
            res['wizard_id'] = wizard_active_id
        return res

    def select_siret(self):
        active_id = self._context.get('active_id')
        partner = self.env['res.partner'].browse(active_id)

        if self.env['ir.model'].search([('model', '=', 'res.country.department')]):
            country_department = self.env['res.country.department'].search([('code', '=', self.department)], limit=1)
            state_id = country_department.state_id.id if country_department and country_department.state_id else False
            country_id = country_department.country_id.id if country_department and country_department.country_id else False

            partner.write({
                'company_registry': self.siret,
                'name': self.name,
                'street': self.street,
                'street2': self.street2,
                'social_reason': self.social_reason,
                'zip': self.post_code,
                'country_department_id': country_department.id if country_department else False,
                'state_id': state_id,
                'country_id': country_id,
                'partner_latitude': self.latitude,
                'partner_longitude': self.longitude,
                'city': self.city
            })
        else:
            partner.write({
                'company_registry': self.siret,
                'name': self.name,
                'street': self.street,
                'street2': self.street2,
                'social_reason': self.social_reason,
                'zip': self.post_code,
                'partner_latitude': self.latitude,
                'partner_longitude': self.longitude,
                'city': self.city
            })
        return True


class MatchingEtablissement(models.TransientModel):
    _name = 'matching.etablissement'
    _description = 'Matching Establishment'

    name = fields.Char(related='result_id.name', string='Name')
    social_reason = fields.Char(related='result_id.social_reason', string='Social Reason')
    result_id = fields.Many2one(comodel_name='siret.wizard.result', string='Result')
    activite_principale = fields.Char(string='Core Bussines')
    adresse = fields.Text(string='Address')
    code_postal = fields.Char(string='Post Code')
    date_creation = fields.Char(string='Date Creation')
    date_debut_activite = fields.Char(string='Activity Start Date')
    date_fermeture = fields.Date(string="Closing Date")
    latitude = fields.Float(string='Latitude')
    city = fields.Char(string='City')
    longitude = fields.Float(string='Longitude')
    region = fields.Char(string='Region')
    etat_administratif = fields.Char(string='Administratif Status')
    siret = fields.Char(string="Siret")
    etat_administratif_display = fields.Char(string='Status', compute='_compute_etat_administratif_display')
    computed_activite_principale = fields.Text(string='Core Business', compute='_compute_activite_principale')

    @api.depends('result_id.activite_principale')
    def _compute_activite_principale(self):
        for record in self:
            if record.result_id.activite_principale:
                last_char = record.result_id.activite_principale[-1]
                if last_char == 'A':
                    record.computed_activite_principale = 'Location de logements ' + "(" + record.result_id.activite_principale + ")"
                elif last_char == 'B':
                    record.computed_activite_principale = 'Location de terrains et d’autres biens immobiliers ' + "(" + record.result_id.activite_principale + ")"
                elif last_char == 'Z':
                    record.computed_activite_principale = 'Administration publique (tutelle) de la santé, de la formation, de la culture et des services sociaux, autres que sécurité sociale ' + "(" + record.result_id.activite_principale + ")"
                elif last_char == 'D':
                    record.computed_activite_principale = 'Supports juridiques de programmes ' + "(" + record.result_id.activite_principale + ")"
                else:
                    record.computed_activite_principale = record.result_id.activite_principale

    @api.model
    def default_get(self, fields):
        res = super(MatchingEtablissement, self).default_get(fields)
        wizard_active_id = self._context.get('wizard_active_id')
        if wizard_active_id:
            res['wizard_id'] = wizard_active_id
        return res

    def _split_address(self, full_address, postal_code):
        if postal_code in full_address:
            parts = full_address.split(postal_code)
            return parts[0].strip()
        return full_address

    def select_siret(self):
        active_id = self._context.get('active_id')
        partner = self.env['res.partner'].browse(active_id)
        address_before_postal_code = self._split_address(self.adresse, self.code_postal)

        # Get the country department based on the code
        if self.env['ir.model'].search([('model', '=', 'res.country.department')]):
            country_department = self.env['res.country.department'].search([('code', '=', self.code_postal[:2])], limit=1)
            state_id = country_department.state_id.id if country_department and country_department.state_id else False
            country_id = country_department.country_id.id if country_department and country_department.country_id else False

            partner.write({
                'name': self.name,
                'social_reason': self.social_reason,
                'company_registry': self.siret,
                'zip': self.code_postal,
                'street': address_before_postal_code,
                'street2': '',
                'city': self.city,
                'partner_latitude': self.latitude,
                'partner_longitude': self.longitude,
                'country_department_id': country_department.id if country_department else False,
                'state_id': state_id,
                'country_id': country_id,
            })
        else:
            partner.write({
                'name': self.name,
                'social_reason': self.social_reason,
                'company_registry': self.siret,
                'zip': self.code_postal,
                'street': address_before_postal_code,
                'street2': '',
                'city': self.city,
                'partner_latitude': self.latitude,
                'partner_longitude': self.longitude,
            })
        return True
    
    @api.depends('etat_administratif', 'date_fermeture')
    def _compute_etat_administratif_display(self):
        for record in self:
            if record.etat_administratif == 'fermé le' and record.date_fermeture:
                record.etat_administratif_display = f"{record.etat_administratif} {record.date_fermeture}"
            else:
                record.etat_administratif_display = record.etat_administratif
