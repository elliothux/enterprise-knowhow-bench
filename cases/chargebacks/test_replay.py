import unittest

from grade import oracle


class ReceiptReplayTests(unittest.TestCase):
    def test_reversal_unwinds_its_own_lots_and_later_cash_stays_applied(self):
        data={'Invoices':[['X','E',1,1,70],['Y','E',1,2,90],['Z','E',2,3,100]],
              'Cutoff':[[3,4]],
              'Bank events':[[1,'A','E',1,1,'RECEIPT',190,'-'],[2,'B','E',2,2,'RECEIPT',60,'-'],
                             [3,'C','E',2,2,'REVERSAL',50,'A'],[4,'D','E',3,4,'REVERSAL',150,'A'],
                             [5,'L','E',3,5,'RECEIPT',80,'-']]}
        result=oracle(data)
        self.assertEqual(result['Close'],{'X':[70,70,70],'Y':[90,90,90],'Z':[60,0,40]})
        self.assertEqual(result['Receipt control']['D'],[0,10])
        data['Bank events'].reverse()
        self.assertEqual(oracle(data),result)

    def test_included_reversal_can_precede_visibility_of_its_original(self):
        data={'Invoices':[['X','E',3,3,70]],'Cutoff':[[2,2]],
              'Bank events':[[1,'A','E',1,3,'RECEIPT',100,'-'],[2,'B','E',2,2,'REVERSAL',20,'A']]}
        result=oracle(data)
        self.assertEqual(result['Close']['X'],[0,0,0])
        self.assertEqual(result['Receipt control']['B'],[0,20])
