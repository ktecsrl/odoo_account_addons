# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 KTec S.r.l.
#    (<http://www.ktec.it>).
#
#    Copyright (C) 2016 Luigi Di Naro
##############################################################################

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class AccountPaymentTermEOM(models.Model):
    _inherit = 'account.payment.term'


    @api.one
    def compute(self, value, date_ref=False):
        lines_months = False
        for line in self.line_ids:
            if line.months:
                lines_months = True
                break
        if not lines_months:
            return super(AccountPaymentTermEOM,self).compute(value,date_ref=date_ref)[0]
        date_ref = date_ref or fields.Date.today()
        amount = value
        result = []
        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id
        prec = currency.decimal_places
        for line in self.line_ids:
            if line.value == 'fixed':
                amt = round(line.value_amount, prec)
            elif line.value == 'percent':
                amt = round(value * (line.value_amount / 100.0), prec)
            elif line.value == 'balance':
                amt = round(amount, prec)
            else:
                continue
            if amt:
                next_date = fields.Date.from_string(date_ref)
                if line.option == 'day_after_invoice_date':
                    next_date += relativedelta(days=line.days, months=line.months)
                elif line.option == 'fix_day_following_month':
                    next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                    next_date = next_first_date + relativedelta(days=line.days - 1, months=line.months)
                elif line.option == 'last_day_following_month':
                    next_date += relativedelta(day=31, months=1)  # Getting last day of next month
                elif line.option == 'last_day_current_month':
                    next_date += relativedelta(day=31, months=0)  # Getting last day of next month
                result.append((fields.Date.to_string(next_date), amt))
                amount -= amt
        amount = reduce(lambda x, y: x + y[1], result, 0.0)
        dist = round(value - amount, prec)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist))
        return result

class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    months = fields.Integer(string='Number of Months', default=0)
