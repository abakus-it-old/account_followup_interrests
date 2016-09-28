from openerp import models, fields, api
from datetime import datetime
import time
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)
    
class account_followup(models.Model):
    _inherit = ['account_followup.followup']

    late_interest_percentage = fields.Integer(string="Late interest (%)")
    late_allowance = fields.Float(string="Late allowance")

class account_followup_line(models.Model):
    _inherit = ['account_followup.followup.line']

    compute_interests = fields.Boolean(string="Compute interests")
    compute_allowance = fields.Boolean(string="Compute allowance")