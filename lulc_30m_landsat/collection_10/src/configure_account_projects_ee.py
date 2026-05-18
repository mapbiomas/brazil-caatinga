import os

dictProjAccount = {
    'caatinga01' : 'mapbiomas-caatinga-cloud',
    'caatinga02' : 'mapbiomas-caatinga-cloud02',
    'caatinga03' : 'mapbiomas-caatinga-cloud03',
    'caatinga04' : 'mapbiomas-caatinga-cloud04',
    'caatinga05' : 'mapbiomas-caatinga-cloud05',
    'solkan1201': 'geo-datasciencessol',
    'solkanCengine': 'ee-solkancengine17',
    'solkanGeodatin': 'geo-data-s',
    'diegoGmail': 'diegocosta',
    'diegoUEFS': 'diegocosta',
    'superconta': 'mapbiomas'
}

def get_current_account():
    """
    Obtém a conta corrente do Earth Engine.
    """
    
    USER_ROOT= os.path.expanduser('~')
    EE_CONFIG_PATH= f'{USER_ROOT}/.config/earthengine'
    currentAccount = os.popen(f"cat {EE_CONFIG_PATH}/current_user.txt").read()
    currentAccount = currentAccount[:-1]
    print(f" The correntAccount >>> {currentAccount} <<< ")

    return dictProjAccount[currentAccount]

def get_project_from_account(myaccoun):
    return dictProjAccount[myaccoun]