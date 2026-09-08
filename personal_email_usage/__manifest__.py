# -*- coding: utf-8 -*-
{
    'name': "Personal Email Usage",

    'summary': "Advanced controls for email fetching: read status, sender filtering, and contact validation",

    'description': """
Enhanced Email Fetching Controls
==============================

This module adds several advanced controls to the email fetching process:

1. Read Status Control
   * Choose whether fetched emails should be marked as read or remain unread in the email server
   * Helps maintain email status synchronization between Odoo and email server

2. User Email Filtering
   * Automatically skips emails sent from internal Odoo users
   * Prevents duplicate processing of internal communications
   * Helps maintain clean email threading

3. Contact Validation
   * Only processes emails from senders that exist in your contacts
   * Reduces spam and unwanted email processing
   * Ensures communication only with known contacts

Technical Details:
----------------
* Adds a boolean field to control email read/unread status
* Implements sender validation against user and contact databases
* Provides detailed logging of skipped and processed emails
    """,

    'author': "Doodex",
    'company': "Doodex",
    'website': "https://www.doodex.net",

    'category': 'Discuss',
    'version': '16.0.1.0.0',

    'depends': ['base','mail'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/mail_views.xml',
    ],

    'images': [
       'static/description/banner.gif',
       'static/description/icon.png',
    ],
    'license': 'LGPL-3',

    'installable': True,
    'application': True,
    'auto_install': False,
}

