# -*- coding: utf-8 -*-

import ee
import gee

class AccountManager:
    #define nome das pastas com as contas
    __accountNames = ['soltan', 'diego', 'diegoc', 'rodrigo']
    
    #funcao ainda nao implementada do numero de mudancas
    def __init__(self, number_tasks_per_cycle=1):
        self._number_tasks_per_cycle = number_tasks_per_cycle
        self._atual_index = 0
    #muda a conta do gee     
    def swich_account(self):
        gee.switch_user(self._accountNames[self._atual_index])
        gee.init()
        gee.tasks(20)
        if(self._atual_index == len(self._accountNames)-1):
            self._atual_index = 0
        else:
            self._atual_index = self._atual_index+1
        
