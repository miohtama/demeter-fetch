from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Dict, NamedTuple


class DataSource(str, Enum):
    big_query = "big_query"
    rpc = "rpc"
    chifra = "chifra"


class ChainType(str, Enum):
    ethereum = "ethereum"
    polygon = "polygon"
    optimism = "optimism"
    arbitrum = "arbitrum"
    celo = "celo"
    bsc = "bsc"
    base = "base"


# closest: 'before' or 'after'
ChainTypeConfig = {
    ChainType.ethereum: {
        "allow": [DataSource.big_query, DataSource.rpc, DataSource.chifra],
        "query_height_api": "https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp=%1&closest=%2",
        "uniswap_proxy_addr": "0xc36442b4a4522e871399cd717abdd847ab11fe88",
        "aave_v3_pool_addr": "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2",
    },
    ChainType.polygon: {
        "allow": [DataSource.big_query, DataSource.rpc, DataSource.chifra],
        "query_height_api": "https://api.polygonscan.com/api?module=block&action=getblocknobytime&timestamp=%1&closest=%2",
        "uniswap_proxy_addr": "0xc36442b4a4522e871399cd717abdd847ab11fe88",
        "aave_v3_pool_addr": "0x794a61358d6845594f94dc1db02a252b5b4814ad",
    },
    ChainType.optimism: {
        "allow": [DataSource.rpc, DataSource.chifra],
        "query_height_api": "https://api-optimistic.etherscan.io/api?module=block&action=getblocknobytime&timestamp=%1&closest=%2",
        "uniswap_proxy_addr": "0xc36442b4a4522e871399cd717abdd847ab11fe88",
    },
    ChainType.arbitrum: {
        "allow": [DataSource.rpc, DataSource.chifra],
        "query_height_api": "https://api.arbiscan.io/api?module=block&action=getblocknobytime&timestamp=%1&closest=%2",
        "uniswap_proxy_addr": "0xc36442b4a4522e871399cd717abdd847ab11fe88",
    },
    ChainType.celo: {
        "allow": [DataSource.rpc, DataSource.chifra],
        "query_height_api": "https://api.celoscan.io/api?module=block&action=getblocknobytime&timestamp=%1&closest=%2",
        "uniswap_proxy_addr": "0x3d79edaabc0eab6f08ed885c05fc0b014290d95a",
    },
    ChainType.bsc: {
        "allow": [DataSource.rpc, DataSource.chifra],
        "query_height_api": "https://api.bscscan.com/api?module=block&action=getblocknobytime&timestamp=%1&closest=%2",
        "uniswap_proxy_addr": "0x7b8a01b39d58278b5de7e48c8449c9f4f5170613",
    },
    ChainType.base: {
        "allow": [DataSource.rpc, DataSource.chifra],
        "query_height_api": "https://api.basescan.org/api?module=block&action=getblocknobytime&timestamp=%1&closest=%2",
        "uniswap_proxy_addr": "0x03a520b32c04bf3beef7beb72e919cf822ed34f1",
    },
}


class ToType(str, Enum):
    minute = "minute"
    tick = "tick"
    raw = "raw"
    position = "position"
    user_lp = "user_lp"


class DappType(str, Enum):
    uniswap = "uniswap"
    aave = "aave"


@dataclass
class BigQueryConfig:
    auth_file: str


@dataclass
class RpcConfig:
    end_point: str
    batch_size: int = 500
    auth_string: str | None = None
    keep_tmp_files: bool = False
    etherscan_api_key: str = None
    force_no_proxy:bool=False # if set to true, will ignore proxy setting


@dataclass
class ChifraConfig:
    etherscan_api_key: str = None  # query block number


@dataclass
class UniswapConfig:
    pool_address: str
    ignore_position_id: bool = False  # if set to true, will not download proxy logs and leave a empty column


class AaveKey(NamedTuple):
    day: date
    address: str


@dataclass
class AaveConfig:
    tokens: List[str]


@dataclass
class FromConfig:
    chain: ChainType
    data_source: DataSource
    dapp_type: DappType
    start: date
    end: date
    uniswap_config: UniswapConfig | None = None
    aave_config: AaveConfig | None = None
    big_query: BigQueryConfig | None = None
    chifra_config: ChifraConfig | None = None
    rpc: RpcConfig | None = None
    http_proxy: str | None = None


@dataclass
class ToConfig:
    type: ToType  # minute or tick
    save_path: str
    multi_process: bool
    skip_existed: bool
    keep_raw: bool
    to_file_list: Dict = field(default_factory=dict)


class KECCAK(str, Enum):
    MINT = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
    SWAP = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
    BURN = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c"
    COLLECT = "0x70935338e69775456a85ddef226c395fb668b63fa0115f5f20610b388e6ca9c0"
    UNI_PROXY_INCREASE = "0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f"
    UNI_PROXY_DECREASE = "0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4"
    UNI_PROXY_COLLECT = "0x40d0efd1a53d60ecbf40971b9daf7dc90178c3aadc7aab1765632738fa8b8f01"
    AAVE_SUPPLY = "0x2b627736bca15cd5381dcf80b0bf11fd197d01a037c52b927a881a10fb73ba61"
    AAVE_WITHDRAW = "0x3115d1449a7b732c986cba18244e897a450f61e1bb8d589cd2e69e6c8924f9f7"
    AAVE_BORROW = "0xb3d084820fb1a9decffb176436bd02558d15fac9b0ddfed8c465bc7359d7dce0"
    AAVE_REPAY = "0xa534c8dbe71f871f9f3530e97a74601fea17b426cae02e1c5aee42c96c784051"
    AAVE_LIQUIDATION = "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
    AAVE_UPDATED = "0x804c9b842b2748a22bb64b345453a3de7ca54a6ca45ce00d415894979e22897a"
    TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


uni_topic_mapping = {
    KECCAK.MINT.value: KECCAK.UNI_PROXY_INCREASE.value,  # mint
    KECCAK.SWAP.value: None,  # swap
    KECCAK.BURN.value: KECCAK.UNI_PROXY_DECREASE.value,  # burn
    KECCAK.COLLECT.value: KECCAK.UNI_PROXY_COLLECT.value,  # collect
}


@dataclass
class Config:
    from_config: FromConfig
    to_config: ToConfig


class MinuteData(object):
    def __init__(self):
        self.timestamp = None
        self.netAmount0 = 0
        self.netAmount1 = 0
        self.closeTick = None
        self.openTick = None
        self.lowestTick = None
        self.highestTick = None
        self.inAmount0 = 0
        self.inAmount1 = 0
        self.currentLiquidity = None

    def to_array(self):
        return [
            self.timestamp,
            self.netAmount0,
            self.netAmount1,
            self.closeTick,
            self.openTick,
            self.lowestTick,
            self.highestTick,
            self.inAmount0,
            self.inAmount1,
            self.currentLiquidity,
        ]

    def __repr__(self):
        return str(self.timestamp)

    def __str__(self):
        return str(self.timestamp)

    def fill_missing_field(self, prev_data) -> bool:
        """
        fill missing field with previous data
        :param prev_data:
        :return: data is available or not
        """
        if prev_data is None:
            prev_data = MinuteData()
        self.closeTick = self.closeTick if self.closeTick is not None else prev_data.closeTick
        self.openTick = self.openTick if self.openTick is not None else prev_data.closeTick
        self.lowestTick = self.lowestTick if self.lowestTick is not None else prev_data.closeTick
        self.highestTick = self.highestTick if self.highestTick is not None else prev_data.closeTick
        self.currentLiquidity = (
            self.currentLiquidity if self.currentLiquidity is not None else prev_data.currentLiquidity
        )

        return False if (self.closeTick is None or self.currentLiquidity is None) else True


MinuteDataNames = [
    "timestamp",
    "netAmount0",
    "netAmount1",
    "closeTick",
    "openTick",
    "lowestTick",
    "highestTick",
    "inAmount0",
    "inAmount1",
    "currentLiquidity",
]


class EthError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class UniNodesNames:
    pool = "pool"
    proxy_transfer = "proxy_transfer"
    proxy_lp = "proxy_LP"
    minute = "minute"
    tick = "tick"
    tx = "tx"
    tick_without_pos = "tick_without_pos"
    positions = "positions"
    user_lp = "user_lp"


class AaveNodesNames:
    raw = "raw"
    minute = "minute"
    tick = "tick"
