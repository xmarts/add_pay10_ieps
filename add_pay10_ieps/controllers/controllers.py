# -*- coding: utf-8 -*-
from odoo import http

# class AddPay10Ieps(http.Controller):
#     @http.route('/add_pay10_ieps/add_pay10_ieps/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/add_pay10_ieps/add_pay10_ieps/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('add_pay10_ieps.listing', {
#             'root': '/add_pay10_ieps/add_pay10_ieps',
#             'objects': http.request.env['add_pay10_ieps.add_pay10_ieps'].search([]),
#         })

#     @http.route('/add_pay10_ieps/add_pay10_ieps/objects/<model("add_pay10_ieps.add_pay10_ieps"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('add_pay10_ieps.object', {
#             'object': obj
#         })