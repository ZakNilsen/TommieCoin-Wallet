#!/usr/bin/python

# dictionaries to strings using json
import json

# to send requests to server
import requests

# for command-line arguments
import sys 

# all the crypto stuff is here
import tommieutils as tu



######### YOUR CODE HERE ############
import random
import time
import copy

emptyBlock = {
    'id':'',
    'prevhash':'',
    'timestamp':'',
    'transactions':{},
    'currhash':''
}


emptyPayTrans = {
    'transtype' : '1',
    'ins' : [],
    'outs' : [],
    'sigs' : []
}

emptyMinedTrans = {
    'prevmine' : '',
    'transtype' : '2',
    'outs': [],
    'nonce' : '',
    'timestamp':''
}


pkFile = open(sys.argv[1], "r")
skFile = open(sys.argv[2], "r")
pkFileStr = pkFile.read()
skFileStr = skFile.read()

#val = requests.get('http://127.0.0.1:8080/showchainraw')
#valstr = json.loads(val.text)
hashpkList = [
"8fe3b49c46150b76f7e46cb887b9b3b6ea779fd98610ab5737945e236202c049",
"3b7d6e6b450fc8ae06a5190a92f48d947a3551a3832e991bda38a0a26377767a",
"143b58a9939ecfaf50158d7be803c75225fd3ad67d42cb6b391497911159a8d4",
"958fcd568aab0fd8dfba46a40a08335c2a4d98f5bf25e7459afa2341e5a15661",
"b7601e33121e99d98d13395fefe2020586b6ab309f5a52821e36b77a8dbe62b5"
]
hashpkList.remove(tu.sha256(pkFileStr))

def getBal(valstr):
	
	#query
    used = []
    used = getAllUsedCoins(valstr)
    coinList = []
    value = 0

    transid = 0
    for block in valstr['blocks']:
    	outnum = 0
        transactions = block['transactions']
        for out in transactions['outs']:
            recipient = out['recipient']
            if recipient == tu.sha256(pkFileStr):
                coinList =  coinList + [(transid, outnum)]
                if coinList[len(coinList)-1] in used:
                    break
                value += out['value']
            outnum += 1
        transid += 1
    return value

#pay
def payCoins(chain, name, amount, nameIndex):
    #going to want list of tuples with (Bal, transid, outnum)
    coins = []
    used = getAllUsedCoins(chain)
    coinList = []
    transid = 0
    #grab coins user can pay with
    for block in chain['blocks']:
    	outnum = 0
        transactions = block['transactions']
       	for out in transactions['outs']:
            recipient = out['recipient']
            if recipient == tu.sha256(pkFileStr):
                coinValue = out['value']
                coinList =  coinList + [(transid, outnum)]
                if coinList[len(coinList)-1] in used:
                	break
                coins = coins + [(coinValue, transid, outnum)]
            outnum += 1
        transid += 1
    
    #sort coins from highest to lowest
    coins = sorted(coins, reverse=True)
    intHold = coins[0][0]
    inpayList = []
    inpayList.append(coins[0])
    #figure out minimal number of coins needed
    for i in range(1,len(coins)):
    	if(amount > intHold):
    		intHold += coins[i][0]
    		inpayList.append(coins[i])
    
    trans = genPay(pkFileStr, skFileStr, inpayList, hashpkList, amount, nameIndex)
    paystr = json.dumps(trans, sort_keys=True)
    payVal = requests.post('http://127.0.0.1:8080/addtrans', data={'trans':paystr})
    return payVal
#mine
def mineCoins(chain, pk):
	blocks = chain['blocks']
	#blockint = findLastMined(chain)
	#Correct way to get right prevMine?
	#transHold = blocks[blockint]['transactions']
	trans = genMined(pk, str(findLastMined(chain)))
	valid = False
	i = 0
	while(valid !=True):
			trans['nonce'] = str(i)
			valid = isValidMinedTrans(chain, trans)
			i+=1
	
	minestr = json.dumps(trans, sort_keys=True)
	mineVal = requests.post('http://127.0.0.1:8080/addtrans', data={'trans':minestr})
	return mineVal

#from transactions
#use findLastMined as prevmine
def genMined(beneficiarypk, prevmine):
    
    trans = copy.deepcopy(emptyMinedTrans)
    trans['prevmine'] = prevmine
    out_dict = {'recipient':tu.sha256(beneficiarypk), 'value':50}
    out_copy = out_dict.copy()
    trans['outs'].append(out_copy)
    trans['timestamp'] = time.time()
    return trans


#from transactions
#Need to complete 
def genPay(pk,sk, inlist, pklist, amtlist, nameIndex):
    
	trans = copy.deepcopy(emptyPayTrans)
	in_list = []
	coinTotal = 0
	#inlist as of right now has (coinvalue, transid, outnum)
	for i in range(len(inlist)):
		in_list += [{'outnum':inlist[i][2], 'transid':inlist[i][1]}]
		coinTotal += inlist[i][0]

	trans['ins'] = in_list
	out_dict = {'recipient':pklist[nameIndex], 'value':amtlist}
	out_copy = out_dict.copy()
	trans['outs'].append(out_copy)
	if(coinTotal > amtlist):
		coinTotal = coinTotal - amtlist
		extraout_dict = {'recipient':tu.sha256(pk), 'value':coinTotal}
		extraout_copy = extraout_dict.copy()
		trans['outs'].append(extraout_copy)

	#signature 
	sig_dict = {'pk':pk, 'signature':tu.sign(sk, json.dumps(trans,sort_keys=True))}
	trans['sigs'].append(sig_dict)
	return trans

def isValidMinedTrans(chain, trans):
    
    tcopy = copy.deepcopy(trans)
    tcopy['nonce'] = ''
 
    minehash = tu.sha256(trans['nonce']+tu.sha256(json.dumps(tcopy,sort_keys=True)))
    
    # needs to hash correctly to start with six 0s
    if (minehash[:6] != '000000'):
        #print "mine transaction does not hash to 6 zeros"
        return False
    
    print("Mining was successful")
    return True


def findLastMined(chain):
    
    numblocks = len(chain['blocks'])
    i = numblocks-1
    while (i>=0):
        if (chain['blocks'][i]['transactions']['transtype']=='2'):
            break
        i -= 1
    return i

#from transactions
def getAllUsedCoins(chain):
    used = []
    for block in chain['blocks']:
        currtrans = block['transactions']
        if (currtrans['transtype']=='1'):
            currins = [(x['transid'],x['outnum']) for x in currtrans['ins']]
            used.extend(currins)
    return used

def findUser(name):
	newstr = name.replace('keys/', '')
        strHold = list(newstr)
        strName = ''
        strHold[0] = strHold[0].upper()
        for i in range(len(newstr)):
                if(strHold[i] == 'p' and strHold[i+1] == 'k'):
                        return strName
                strName += strHold[i]
        return strName

def validPKSK(string):
	holder = "keys/" + string.lower() + "sk.txt"
	if(sys.argv[2] == holder):
		return True
	return False


#User interface stuff below and important values
#_________________________________________________

name = findUser(sys.argv[1])
if(validPKSK(name) == False):
	print("Public key and Secret key do not match, nice try")
	exit(0)

nameList = ['Alice', 'Bob', 'Carlos', 'Dawn', 'Eve']
nameList.remove(name)

print("Hello " + name + ", welcome")
while(True):
	val = requests.get('http://127.0.0.1:8080/showchainraw')
	valstr = json.loads(val.text)
	bal = getBal(valstr)
	print("You currently have " + str(bal) + " TommieCoins.")
	print("<>"*20)
	print("What would you like to do?")
	print("Options:\n 1) Pay\n 2) Mine\n 3) Quit")
	option = raw_input("Enter action: ")
	option = str(option).lower()
	print("<>"*20) 
	if (option == "1" or option == "pay") and bal > 0:
		while(True):
			print("Who would you like to pay?")
			print("Options:\n1) " + nameList[0])
			print("2) " + nameList[1])
			print("3) " + nameList[2])
			print("4) " + nameList[3])
			payName = raw_input("Enter: ")
			payName = str(payName).lower()
			if payName == "1" or payName == nameList[0].lower():
					print("Paying to " + nameList[0])
					nameIndex = 0	
			elif payName == "2" or payName == nameList[1].lower():
					print("Paying to " + nameList[1])
					nameIndex = 1
			elif payName == "3" or payName == nameList[2].lower():
					print("Paying to " + nameList[2])
					nameIndex = 2
			elif payName == "4" or payName == nameList[3].lower():
					print("Paying to " + nameList[3])
					nameIndex = 3
			else:
				print("Invalid option, try again")
				print("<>"*20)
				continue
	
			payTotal = input("Enter payment amount: ")
			if payTotal <= 0 or payTotal > bal:
				print("Invalid Amount, enter value greater than 0 and less than bal")
				print("<>"*20)
				continue

			payCoins(valstr, payName, payTotal, nameIndex)
			print("Payment was successful")
			print("<>"*20)
			break

	elif option == "2" or option == "mine":
		print("Beginning mining transaction...")
		mineCoins(valstr, pkFileStr)
		print("--Mining complete--")	
		print("<>"*20)	
	elif option == "3" or option == "quit":
		print("Exiting")
		print("<>"*20)
		exit(0)
	else:
		print("Invalid option, try again")
		print("<>"*20)
		continue
