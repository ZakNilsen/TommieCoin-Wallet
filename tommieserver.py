#
#   tommieserver.py : python bottle server that maintains the TommieCoin blockchain
#
#   Author: Scott Yilek  (April 2018)
#


import tommieutils as tu
import transactions
import json 
from bottle import route, run, debug, template, static_file, request, redirect, response




@route('/showchainraw')
def showchain():
# open chain file, print it out to screen
    chainstr=transactions.getCurrChainStr()
    return chainstr

@route('/')
@route('/showchainhtml')
def shownicechain():
    chainstr=transactions.getCurrChainStr()
    return '<html><body><pre>%s</pre></body></html>'%chainstr

@route('/addtrans',method='POST')
def addtrans():
    trans_str = request.POST.get('trans')
    trans = json.loads(trans_str) 
    origchain = transactions.getCurrChain()
    orighash = origchain['lasthash']
    chain = transactions.addTrans(trans, origchain)
    newhash = chain['lasthash']
    if (orighash==newhash):
        return 'Failure' 
    transactions.setCurrChain(chain)
    return 'Success' 


debug(True)
run()
