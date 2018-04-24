import random
import time
import hashlib
from ecdsa import SigningKey,VerifyingKey,BadSignatureError
import asyncio
from .blockchain import BlockChain

MAX_NONCE = 2 ** 32
VERIFY_TIME=10
POW_DIFF=15
MIN_PING=10
MAX_PING=100


class Masternode(BlockChain):
    def __init__(self, utxoamount, hashrate, externalip, privkey, txid):
        super(Masternode, self).__init__()
        self.hashrate = hashrate  # 节点宣称算力
        self.externalip = externalip  # 节点IP
        self.privkey = privkey  # 节点私钥 - 不广播
        self.txid = txid  # 节点txid - 验证抵押金，识别ID
        self.utxoamount = utxoamount  # 节点抵押货币
        self.publickey = self.generatePublickey(self.privkey)  # 节点公钥

    def generatePublickey(self, privkey):
        return privkey.get_verifying_key()

    def proof_of_work(self, header, difficulty_bits):
        target = 2 ** (256 - difficulty_bits)
        for nonce in range(MAX_NONCE):
            hash_result = hashlib.sha256((str(header) + str(nonce)).encode('utf-8')).hexdigest()
            if int(hash_result, 16) < target:
                return (hash_result, nonce)
        return False

    async def mining(self):
        blockheader = self.getBlockheader()
        difficulty_bits = self.getDifficulty()
        hash_result, nonce = self.proof_of_work(blockheader, difficulty_bits)
        await asyncio.sleep(random.uniform(0, 1))
        return hash_result, nonce, time.time()

    async def proveHashrate(self,difficulty_bits):
        blockheader = self.getPrevblockhash + self.txid
        endblock = self.getBlockheight() + VERIFY_TIME
        nonces = []
        while self.getBlockheight() < endblock:
            blockhash, nonce = self.proof_of_work(blockheader, difficulty_bits)
            blockheader = blockhash
            nonces.append(nonce)
        await asyncio.sleep(random.uniform(0, 1))
        return nonces

    def verifyHashrate(self, node, nonces,difficulty_bits):
        header = self.blockhash + node.txid
        target = 2 ** (256 - difficulty_bits)
        for nonce in nonces:
            hash_result = hashlib.sha256((str(header) + str(nonce)).encode('utf-8')).hexdigest()
            if int(hash_result, 16) > target:
                return False
            header = hash_result
        return True

    def sign(self, message):
        return self.privkey.sign(message)

    def verify(self, signature, message, verifykey):
        return verifykey.verify(signature, message)

    def verifyStake(self, node):
        is_node_txid_upsent = True
        is_txid_more_than_stake = True
        return is_node_txid_upsent * is_txid_more_than_stake

    def ping(self, node, mn):  # 节点间连接速度
        return random.uniform(MIN_PING, MAX_PING)

    def chosePartners(self, node, PartMN):  # 邀请小组成员
        connectivity = {}
        if len(PartMN) <= 2:
            return list(PartMN)
        available_mn = [mn for mn in PartMN if
                        abs(int(mn.txid, 16) - int(node.txid, 16) + int(self.blockhash, 16)) < 2 ** 10 and mn != node]
        if len(available_mn) <= 2: available_mn = [mn for mn in PartMN if mn != node]
        for mn in available_mn:
            connectivity[mn] = self.ping(node, mn)
        sorted_connectivity = sorted(connectivity.items(), key=lambda item: item[1])
        return [node, sorted_connectivity[0][0], sorted_connectivity[1][0]]
