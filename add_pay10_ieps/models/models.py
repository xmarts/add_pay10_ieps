# -*- coding: utf-8 -*-

import base64
from itertools import groupby
import re
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import BytesIO
import requests
from pytz import timezone

from lxml import etree
from lxml.objectify import fromstring
from suds.client import Client

from odoo import _, api, fields, models, tools
from odoo.tools.xml_utils import _check_with_xsd
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.tools import float_round
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_repr

from odoo.addons.l10n_mx_edi.tools.run_after_commit import run_after_commit
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _l10n_mx_edi_create_taxes_cfdi_values(self):
        '''Create the taxes values to fill the CFDI template.
        '''
        self.ensure_one()
        values = {
            'total_withhold': 0,
            'total_transferred': 0,
            'withholding': [],
            'transferred': [],
        }
        taxes = {}
        for line in self.invoice_line_ids.filtered('price_subtotal'):
            price = line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)
            p1 = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            p2 = 0.0
            p3 = 0.0
            taxes_line = line.invoice_line_tax_ids


            # SECCION 1
            #######################################################
            #######################################################
            #######################################################
            taxes_linee1 = taxes_line.filtered(
                lambda tax: tax.amount_type != 'group' and 'IEPS' not in tax.tag_ids.name and tax.price_include!=True) + taxes_line.filtered(
                    lambda tax: tax.amount_type == 'group' and 'IEPS' not in tax.tag_ids.name and tax.price_include!=True).mapped(
                        'children_tax_ids')
            tax_line = {tax['id']: tax for tax in taxes_linee1.compute_all(
                p1, line.currency_id, line.quantity, line.product_id, line.partner_id)['taxes']}
            for tax in taxes_linee1.filtered(lambda r: r.l10n_mx_cfdi_tax_type != 'Exento'):
                tax_dict = tax_line.get(tax.id, {})
                amount = round(abs(tax_dict.get(
                    'amount', tax.amount / 100 * float("%.2f" % line.price_subtotal))), 2)
                rate = round(abs(tax.amount), 2)
                if tax.id not in taxes:
                    taxes.update({tax.id: {
                        'name': (tax.tag_ids[0].name
                                 if tax.tag_ids else tax.name).upper(),
                        'amount': amount,
                        'rate': rate if tax.amount_type == 'fixed' else rate / 100.0,
                        'type': tax.l10n_mx_cfdi_tax_type,
                        'tax_amount': tax_dict.get('amount', tax.amount),
                    }})
                else:
                    taxes[tax.id].update({
                        'amount': taxes[tax.id]['amount'] + amount
                    })
                if tax.amount >= 0:
                    values['total_transferred'] += amount
                else:
                    values['total_withhold'] += amount

            taxes_line1 = taxes_line.filtered(
                lambda tax: tax.amount_type != 'group' and 'IEPS' not in tax.tag_ids.name and tax.price_include is True) + taxes_line.filtered(
                    lambda tax: tax.amount_type == 'group' and 'IEPS' not in tax.tag_ids.name and tax.price_include is True).mapped(
                        'children_tax_ids')
            tax_line = {tax['id']: tax for tax in taxes_line1.compute_all(
                p1, line.currency_id, line.quantity, line.product_id, line.partner_id)['taxes']}
            for tax in taxes_line1.filtered(lambda r: r.l10n_mx_cfdi_tax_type != 'Exento'):
                tax_dict = tax_line.get(tax.id, {})
                amount = round(abs(tax_dict.get(
                    'amount', tax.amount / 100 * float("%.2f" % line.price_subtotal))), 2)
                rate = round(abs(tax.amount), 2)
                if tax.id not in taxes:
                    taxes.update({tax.id: {
                        'name': (tax.tag_ids[0].name
                                 if tax.tag_ids else tax.name).upper(),
                        'amount': amount,
                        'rate': rate if tax.amount_type == 'fixed' else rate / 100.0,
                        'type': tax.l10n_mx_cfdi_tax_type,
                        'tax_amount': tax_dict.get('amount', tax.amount),
                    }})
                else:
                    taxes[tax.id].update({
                        'amount': taxes[tax.id]['amount'] + amount
                    })
                if tax.amount >= 0:
                    values['total_transferred'] += amount
                else:
                    values['total_withhold'] += amount
                p2 = p1 - round(abs(amount/line.quantity),2)
            if not taxes_line1:
                p2 = p1


            # SECCION 2
            #######################################################
            #######################################################
            #######################################################
            taxes_linee2 = taxes_line.filtered(
                lambda tax: tax.amount_type != 'group' and 'IEPS' in tax.tag_ids.name and tax.amount_type == 'fixed' and tax.price_include!=True) + taxes_line.filtered(
                    lambda tax: tax.amount_type == 'group' and 'IEPS' in tax.tag_ids.name and tax.amount_type == 'fixed' and tax.price_include!=True).mapped(
                        'children_tax_ids')
            tax_line = {tax['id']: tax for tax in taxes_linee2.compute_all(
                p2, line.currency_id, line.quantity, line.product_id, line.partner_id)['taxes']}
            for tax in taxes_linee2.filtered(lambda r: r.l10n_mx_cfdi_tax_type != 'Exento'):
                tax_dict = tax_line.get(tax.id, {})
                amount = round(abs(tax_dict.get(
                    'amount', tax.amount / 100 * float("%.2f" % line.price_subtotal))), 2)
                rate = round(abs(tax.amount), 2)
                if tax.id not in taxes:
                    taxes.update({tax.id: {
                        'name': (tax.tag_ids[0].name
                                 if tax.tag_ids else tax.name).upper(),
                        'amount': amount,
                        'rate': rate if tax.amount_type == 'fixed' else rate / 100.0,
                        'type': tax.l10n_mx_cfdi_tax_type,
                        'tax_amount': tax_dict.get('amount', tax.amount),
                    }})
                else:
                    taxes[tax.id].update({
                        'amount': taxes[tax.id]['amount'] + amount
                    })
                if tax.amount >= 0:
                    values['total_transferred'] += amount
                else:
                    values['total_withhold'] += amount

            taxes_line2 = taxes_line.filtered(
                lambda tax: tax.amount_type != 'group' and 'IEPS' in tax.tag_ids.name and tax.amount_type == 'fixed' and tax.price_include is True) + taxes_line.filtered(
                    lambda tax: tax.amount_type == 'group' and 'IEPS' in tax.tag_ids.name and tax.amount_type == 'fixed' and tax.price_include is True).mapped(
                        'children_tax_ids')
            tax_line = {tax['id']: tax for tax in taxes_line2.compute_all(
                p2, line.currency_id, line.quantity, line.product_id, line.partner_id)['taxes']}
            for tax in taxes_line2.filtered(lambda r: r.l10n_mx_cfdi_tax_type != 'Exento'):
                tax_dict = tax_line.get(tax.id, {})
                amount = round(abs(tax_dict.get(
                    'amount', tax.amount / 100 * float("%.2f" % line.price_subtotal))), 2)
                rate = round(abs(tax.amount), 2)
                if tax.id not in taxes:
                    taxes.update({tax.id: {
                        'name': (tax.tag_ids[0].name
                                 if tax.tag_ids else tax.name).upper(),
                        'amount': amount,
                        'rate': rate if tax.amount_type == 'fixed' else rate / 100.0,
                        'type': tax.l10n_mx_cfdi_tax_type,
                        'tax_amount': tax_dict.get('amount', tax.amount),
                    }})
                else:
                    taxes[tax.id].update({
                        'amount': taxes[tax.id]['amount'] + amount
                    })
                if tax.amount >= 0:
                    values['total_transferred'] += amount
                else:
                    values['total_withhold'] += amount
                p3 = p2 - round(abs(amount/line.quantity),2)
            if not taxes_line2:
                p3 = p2

            # SECCION 2
            #######################################################
            #######################################################
            #######################################################
            taxes_linee3 = taxes_line.filtered(
                lambda tax: tax.amount_type != 'group' and 'IEPS' in tax.tag_ids.name and tax.amount_type == 'percent' and tax.price_include!=True) + taxes_line.filtered(
                    lambda tax: tax.amount_type == 'group' and 'IEPS' in tax.tag_ids.name and tax.amount_type == 'percent' and tax.price_include!=True).mapped(
                        'children_tax_ids')
            tax_line = {tax['id']: tax for tax in taxes_linee3.compute_all(
                p3, line.currency_id, line.quantity, line.product_id, line.partner_id)['taxes']}
            for tax in taxes_linee3.filtered(lambda r: r.l10n_mx_cfdi_tax_type != 'Exento'):
                tax_dict = tax_line.get(tax.id, {})
                amount = round(abs(tax_dict.get(
                    'amount', tax.amount / 100 * float("%.2f" % line.price_subtotal))), 2)
                rate = round(abs(tax.amount), 2)
                if tax.id not in taxes:
                    taxes.update({tax.id: {
                        'name': (tax.tag_ids[0].name
                                 if tax.tag_ids else tax.name).upper(),
                        'amount': amount,
                        'rate': rate if tax.amount_type == 'fixed' else rate / 100.0,
                        'type': tax.l10n_mx_cfdi_tax_type,
                        'tax_amount': tax_dict.get('amount', tax.amount),
                    }})
                else:
                    taxes[tax.id].update({
                        'amount': taxes[tax.id]['amount'] + amount
                    })
                if tax.amount >= 0:
                    values['total_transferred'] += amount
                else:
                    values['total_withhold'] += amount

            taxes_line3 = taxes_line.filtered(
                lambda tax: tax.amount_type != 'group' and 'IEPS' in tax.tag_ids.name and tax.amount_type == 'percent' and tax.price_include is True) + taxes_line.filtered(
                    lambda tax: tax.amount_type == 'group' and 'IEPS' in tax.tag_ids.name and tax.amount_type == 'percent' and tax.price_include is True).mapped(
                        'children_tax_ids')
            tax_line = {tax['id']: tax for tax in taxes_line3.compute_all(
                p3, line.currency_id, line.quantity, line.product_id, line.partner_id)['taxes']}
            for tax in taxes_line3.filtered(lambda r: r.l10n_mx_cfdi_tax_type != 'Exento'):
                tax_dict = tax_line.get(tax.id, {})
                amount = round(abs(tax_dict.get(
                    'amount', tax.amount / 100 * float("%.2f" % line.price_subtotal))), 2)
                rate = round(abs(tax.amount), 2)
                if tax.id not in taxes:
                    taxes.update({tax.id: {
                        'name': (tax.tag_ids[0].name
                                 if tax.tag_ids else tax.name).upper(),
                        'amount': amount,
                        'rate': rate if tax.amount_type == 'fixed' else rate / 100.0,
                        'type': tax.l10n_mx_cfdi_tax_type,
                        'tax_amount': tax_dict.get('amount', tax.amount),
                    }})
                else:
                    taxes[tax.id].update({
                        'amount': taxes[tax.id]['amount'] + amount
                    })
                if tax.amount >= 0:
                    values['total_transferred'] += amount
                else:
                    values['total_withhold'] += amount


        values['transferred'] = [tax for tax in taxes.values() if tax['tax_amount'] >= 0]
        values['withholding'] = self._l10n_mx_edi_group_withholding(
            [tax for tax in taxes.values() if tax['tax_amount'] < 0])
        return values