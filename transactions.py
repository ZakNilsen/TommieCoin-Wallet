#
#   transactions.py - useful functions for handling blocks and transactions in TommieCoin
# 
#   Author: Scott Yilek, April 2018
#




import time
import copy
import tommieutils as tu
import json



################################################
###    EMPTY TRANSACTION/BLOCK DICTIONARIES ####
################################################

# sigs should just contain a signature from Tommie 
emptyCreateTrans = {
    'transtype' : '0',
    'outs' : [],
    'sigs' : []
}

# an empty Pay Transaction.
emptyPayTrans = {
    'transtype' : '1',
    'ins' : [],
    'outs' : [],
    'sigs' : []
}

# only valid if prevmine is id of block with the most recent mined transaction 
# SHA256(nonce||SHA256(trans with nonce set to '')) should be hex that starts with six 0s
emptyMinedTrans = {
    'prevmine' : '',
    'transtype' : '2',
    'outs': [],
    'nonce' : '',
    'timestamp':''
}


# block will contain a single transaction (of any type) inside of it
# id will be incremented with each new block
# currhash will be sha256 hash of the block with currhash set to ''.  Then, this hash will be assigned to currhash.
emptyBlock = {
    'id':'',
    'prevhash':'',
    'timestamp':'',
    'transactions':{},
    'currhash':''
}




#########################################
####### Tommie's keys ###################
#########################################

# You should never use sk in your wallet application
f = open('./keys/tommiesk.txt','r')
sktommie = f.read()
f.close()
f = open('./keys/tommiepk.txt','r')
pktommie = f.read()
f.close()



def genCreate(pklist, amtlist): 
    """
    Generates a new Create transaction.
    You shouldn't use this, but it will be useful as a reference for how to create transactions
    
    pklist is a list of recipients
    amtlist is a list of how much to pay to each recipient. Should be same len as pklist
    """

    trans = copy.deepcopy(emptyCreateTrans) # make copy of an empty create transaction (to fill in)
    # build up output list with dictionary containing amt and H(key)
    for i in range(len(pklist)):
        pk = pklist[i]
        amt = amtlist[i]
        pkhash = tu.sha256(pk)
        out = {'value':amt, 'recipient':pkhash}
        trans['outs'].append(out)
    pre_trans_str = json.dumps(trans, sort_keys=True) 
    sig = tu.sign(sktommie, pre_trans_str) 
    trans['sigs'].append({'pk':pktommie,'signature':sig})
    return trans




def genPay(pk,sk, inlist, pklist, amtlist):
    """
    You might want to complete this to use in your wallet

    inlist should be list of pairs, with (transid, outnum)
    inlist should be spendable by same user (who has pk,sk as key)
    this function does not have any restrictions enforced (i.e., shouldn't call isValidTrans), those will be checked before creating a block, so output of this function could be rejected by server
    """
    trans = copy.deepcopy(emptyPayTrans)
    return trans

  
def genMined(beneficiarypk, prevmine):
    """
    You will want to write this function, probably in your wallet
    """
    trans = copy.deepcopy(emptyMinedTrans)
    return trans 







    
def genBlock(prevhash, previd, trans):
    """
    Take a transaction and build it into a block that can be added to chain.
    previd is an int (that will be converted to a string after increment)
    trans is a dictionary with transaction details
 
    This function is important for the addTrans function later
    """
    block = copy.deepcopy(emptyBlock) 
    block['id'] = str(previd+1)
    block['prevhash'] = prevhash
    block['transactions'] = copy.deepcopy(trans)
    block['timestamp'] = str(time.time())
    # currhash is of entire block with currhash=''
    currhash = tu.sha256(json.dumps(block, sort_keys=True))
    block['currhash'] = currhash
    return block


def getCurrChainStr():
    f = open('currchain.txt','r')
    s = f.read()
    f.close()
    return s

def setCurrChain(chaindict):
    chainstr = json.dumps(chaindict, indent=4, sort_keys=True)
    f = open('currchain.txt','w')
    f.write(chainstr)
    f.close()

 
def getCurrChain():
    chainstr = getCurrChainStr()
    chain = json.loads(chainstr)
    return chain



def addTrans(trans, chain):
    """
    If trans is valid, add to chain by creating a new block and adding it
    If trans is not valid, currently prints error message and returns original
    """
    chain = copy.deepcopy(chain)
    if isValidTrans(chain, trans):
        prevblock = chain['blocks'][-1]
        prevhash = prevblock['currhash']
        previd = int(prevblock['id'])
        newblock = genBlock(prevhash, previd, trans)
        chain['blocks'].append(newblock)
        latesthash = newblock['currhash']
        chain['lasthash'] = latesthash  
        chain['signature'] = tu.sign(sktommie, latesthash)
    else:
        print "Transaction invalid"
    return chain

def getAllUsedCoins(chain):
    used = []
    for block in chain['blocks']:
        currtrans = block['transactions']
        if (currtrans['transtype']=='1'):
            currins = [(x['transid'],x['outnum']) for x in currtrans['ins']]
            used.extend(currins)
    return used


def isAvailCoin(inpair, chain):
    #coin (repr. by a pair (blocknum,outnum)) is available if it has never appeared in an ins list
    chain = getCurrChain()
    used = getAllUsedCoins(chain)
    if (inpair in used):
        return False
    return True


#################################################
#### CHECK TRANSACTION VALIDITY #################
#################################################

def isValidTrans(chain, trans):
    """
    Check transaction validity.  Look at transtype and delegate to more specific isValid function.
    """
    ttype = trans['transtype']
    if (ttype=='0'):
        return isValidCreateTrans(chain, trans)
    elif (ttype=='1'):
        return isValidPayTrans(chain, trans)
    elif (ttype=='2'):
        return isValidMinedTrans(chain, trans)

    return False 

def isValidCreateTrans(chain, trans):
    """
    Make sure pay transaction is correct
    should be signed by tommie
    """
    pk = trans['sigs'][0]['pk']
    if (pk != pktommie):
        return False
    tcopy = copy.deepcopy(trans)
    tcopy['sigs'] = []
    if (not tu.verify(pktommie, json.dumps(tcopy, sort_keys=True), trans['sigs'][0]['signature'])):
        return False
    return True

def isValidMinedTrans(chain, trans):
    """
    check that a mined transaction is valid, given current chain
    this means
    1. contains nonce such that SHA256(nonce||SHA256(trans without nonce)) starts with 6 '0' hex chars
    2. transaction contains id of block containing the most recent mined transaction on the chain
    3. transaction gives amount exactly 50
    """ 
    tcopy = copy.deepcopy(trans)
    tcopy['nonce'] = ''
    minehash = tu.sha256(trans['nonce']+tu.sha256(json.dumps(tcopy,sort_keys=True)))
    # need one output, and needs to have amount 50
    if (len(trans['outs']) != 1):
        print "too many outs"
        return False
    if (trans['outs'][0]['value'] != 50):
        print "wrong value - not 50"
        return False
    # needs to hash correctly to start with six 0s
    if (minehash[:6] != '000000'):
        print "mine transaction does not hash to 6 zeros"
        return False
    # needs to have id of prev block with most recent mined transaction
    if (trans['prevmine'] != str(findLastMined(chain))):
        print "prevmine id is not correct"
        return False
    return True


def findLastMined(chain):
    """
    return the block index/id containing most recent mined transaction
    used by isValidMinedTrans, since a valid mined transaction must have id of previous mined trans.
    """
    numblocks = len(chain['blocks'])
    i = numblocks-1
    while (i>=0):
        if (chain['blocks'][i]['transactions']['transtype']=='2'):
            break
        i -= 1
    return i


def isValidPayTrans(chain, trans):
    """
    Check that pay transaction trans is valid, given current chain
    Must check 
    1. input coins exist
    2. input coins haven't already been spent
    3. input amounts equal output amounts
    4. signature verifies and public key that goes with signature was recipient of all input coins

    Somewhat miraculous that this appears to work
    """
    intotal = 0
    outtotal = 0
    inrecips = []
    transcopy = copy.deepcopy(trans)
    for inp in trans['ins']:
        #inp is a dict w/ transid and outnum fields 
        transid = int(inp['transid'])
        outnum = int(inp['outnum'])
        # make sure coins exist (there is a block with that number and an output with that index)
        if (transid<0 or transid>=len(chain['blocks'])):
            print "bad transaction id"
            return False
        if (outnum<0 or outnum>=len(chain['blocks'][transid]['transactions']['outs'])):
            print "that outnum doesn't exist"
            return False
        # make sure coins in inputs haven't been used before
        if (not isAvailCoin((transid,outnum),chain)):
            print "coin already used"
            return False
        intotal += chain['blocks'][transid]['transactions']['outs'][outnum]['value']
        inrecips.append(chain['blocks'][transid]['transactions']['outs'][outnum]['recipient'])
    # make sure amts add up to inputs
    for outp in trans['outs']:
        outtotal += outp['value'] 
    if (intotal != outtotal):
        print "outtotal not equal to intotal"
        return False

    # make sure signature is valid for each input, and make sure key in signature was recipient of all inputs
    transcopy['sigs'] = []
    sigmessage = json.dumps(transcopy, sort_keys=True)
    pk = trans['sigs'][0]['pk']
    signature = trans['sigs'][0]['signature']

    pkhash = tu.sha256(pk)
    if (inrecips.count(pkhash) != len(inrecips)):
        print "recipient hashes didn't work out"
        return False
    if (not tu.verify(pk, sigmessage, signature)):
        print "bad signature verify"
        return False

    # if get here, all should be OK
    return True








