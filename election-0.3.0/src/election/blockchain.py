import random
import time

POW_DIFF=15

class BlockChain:
    def __init__(self):
        self.blockheight = 0
        self.version = '00000010'
        self.prevblockhash = '00000000000000000000000000000701'
        self.merkleroot = '00000000000000000000000000001994'
        self.timestamp = hex(int(time.time()))[2:]
        self.target = '00000010'
        self.blockheader = self.getBlockheader()

    def getBlockheader(self):
        return self.version + self.prevblockhash + self.merkleroot + self.timestamp + self.target

    def getDifficulty(self):
        diff = POW_DIFF
        return diff

    def getPrevblockhash(self):
        return self.prevblockhash

    def getBlockheight(self):
        return self.blockheight

    def nextBlock(self, blockhash):
        self.blockheight += 1
        self.version = self.version
        self.prevblockhash = blockhash
        self.merkleroot = ''.join(random.choice('0123456789abcdef') for _ in range(32))
        self.timestamp = hex(int(time.time()))[2:]
        self.target = self.target
        self.blockheader = self.getBlockheader()