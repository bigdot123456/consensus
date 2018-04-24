import ecdsa
import random
import json
import numpy as np
import time
import hashlib
from ecdsa import SigningKey,VerifyingKey,BadSignatureError
import asyncio
from .blockchain import BlockChain
from .listnode import ListNode

MIN_AMOUNT=1000
MAX_AMOUTN=10000
MIN_HASHRATE=1000
MAX_HASHRATE=10000
MASTETNODES_NUMS=100
REGION_NUMS=32
POW_NUMS=21
VERIFY_NUMS=11
UTXO_WEIGHT_DELTA=0.1
MAX_NONCE = 2 ** 32
VERIFY_TIME=10
MAX_BLOCKHEIGHT=100
ELECT_GAP=10
VERIFY_GAP=25
POW_DIFF=15
MINUPTIME=3600

class Matrix(BlockChain):
    def __init__(self):
        super(Matrix, self).__init__()
        self.global_list = self.generateMN(MASTETNODES_NUMS)
        self.pow_nodes = random.sample(list(self.global_list.values()), 21)
        self.verify_nodes = random.sample(list(self.global_list.values()), 11)

    def generateMN(self, nums):  # 生成主节点列表
        global_list = {}
        for i in range(nums):
            utxoamount = random.randint(MIN_AMOUNT, MAX_AMOUTN)
            hashrate = random.uniform(MIN_HASHRATE, MAX_HASHRATE)
            externalip = '.'.join([str(random.randint(0, 255)) for _ in range(4)])
            privkey = SigningKey.generate()
            txid = ''.join(random.choice('0123456789abcdef') for _ in range(32))
            uptime = time.time() - random.randint(0, 100000)
            global_list[txid] = ListNode(utxoamount, hashrate, externalip, privkey, txid, uptime)
        return global_list

    def clearAll(self):
        for node in self.global_list.values():
            node.updateLevel(0)
            node.updateChildren(None)
            node.updateFather(None)
            node.updateRegion(-1)

    def dividedRegions(self):
        regions = {}
        region_num = 0
        for item in sorted(self.global_list.items(), key=lambda item: item[1].utxoamount * item[1].hashrate):
            item[1].updateRegion(region_num)
            region_num = (region_num + 1) % REGION_NUMS
            if region_num not in regions:
                regions[region_num] = []
            regions[region_num].append(item[1])
        return regions

    def groupPK(self, group):
        timestamp = int(self.timestamp, 16)
        utxo_weights = [max(float(node.utxoamount) * (timestamp - node.uptime) * node.hashrate, UTXO_WEIGHT_DELTA) for
                        node in group]
        p = [float(w) / sum(utxo_weights) for w in utxo_weights]
        winner = np.random.choice(group, 1, p)[0]
        return winner

    def regionElections(self, region):
        select_pool = []
        random.seed(int(self.prevblockhash[:8], 16))
        rounds = 0
        while True:
            for node in region:
                if node.level == rounds:
                    select_pool.append(node)
            if len(select_pool) == 1:
                winner = select_pool[0]
                winner.updateUptime(winner.uptime + (int(self.timestamp, 16) - winner.uptime) / 2)
                return select_pool[0]
            while select_pool:
                if len(select_pool) >= 3:
                    group = random.sample(select_pool, 3)
                else:
                    group = select_pool
                winner = self.groupPK(group)
                children = [node for node in group if node != winner]
                winner.updateLevel(rounds + 1)
                winner.updateChildren(children)
                for node in children:
                    node.updateFather(winner)
                for node in group:
                    select_pool.remove(node)
            rounds += 1
        return False

    def elect(self):
        self.clearAll()
        regions = self.dividedRegions()
        pow_nodes = []
        verify_nodes = []
        for i in range(REGION_NUMS):
            if i < POW_NUMS:
                pow_nodes.append(self.regionElections(regions[i]))
            else:
                verify_nodes.append(self.regionElections(regions[i]))
        return pow_nodes, verify_nodes

    async def powNextblock(self):
        tasks = [node.mining() for node in self.pow_nodes]
        results = await asyncio.gather(*tasks)
        winner = -1
        blockhash = -1
        mintime = time.time()
        for i in range(POW_NUMS):
            hash_result, nonce, timestamp = results[i]
            if timestamp < mintime:
                blockhash, winner, mintime = hash_result, i, timestamp
        return blockhash, winner

    async def verifyAll(self):
        pass

    def run(self):
        for blockheight in range(MAX_BLOCKHEIGHT):
            loop = asyncio.new_event_loop()
            blockhash, winner = loop.run_until_complete(self.powNextblock())
            loop.close()
            if blockheight % ELECT_GAP == 7:
                self.pow_nodes, self.verify_nodes = self.elect()
                print(''.join('-' for _ in range(50)))
                print('POW_NODES: ' + ' '.join(node.txid for node in self.pow_nodes))
                print('VERYFI_NODES: ' + ' '.join(node.txid for node in self.verify_nodes))
                print(''.join('-' for _ in range(50)))
            if blockheight % VERIFY_GAP == 3:
                pass
            self.nextBlock(blockhash)
            for node in self.global_list.values():
                node.nextBlock(blockhash)
            print('blockheight: ' + str(self.blockheight), 'winner: ' + self.pow_nodes[winner].txid,
                  'blockhash: ' + blockhash)