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
