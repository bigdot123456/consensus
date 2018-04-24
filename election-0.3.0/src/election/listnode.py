from .masternode import Masternode

class ListNode(Masternode):
    def __init__(self, utxoamount, hashrate, externalip, privkey, txid, uptime):
        super(ListNode, self).__init__(utxoamount, hashrate, externalip, privkey, txid)
        self.uptime = uptime  # 节点上线时间
        self.level = 0  # 节点选举等级
        self.region = -1
        self.father = None  # 父节点
        self.children = None  # 子节点

    def updateLevel(self, level):
        self.level = level

    def updateRegion(self, region):
        self.region = region

    def updateFather(self, father):
        self.father = father

    def updateChildren(self, children):
        self.children = children

    def updateUptime(self, uptime):
        self.uptime = uptime