import json
from decimal import Decimal
from typing import List

import numpy as np
import pandas as pd

import demeter_fetch.common._typing as _typing
import demeter_fetch.common.constants as constants


def signed_int(h):
    """
    Converts hex values to signed integers.
    """
    s = bytes.fromhex(h[2:])
    i = int.from_bytes(s, "big", signed=True)
    return i


def hex_to_address(topic_str):
    return "0x" + topic_str[26:]


def split_topic(value: str) -> List[str]:
    if isinstance(value, list):
        return value
    elif isinstance(value, str):
        value = value.strip("[]").replace('"', "").replace("'", "").replace(" ", "").replace("\n", ",")
        return value.split(",")
    else:
        raise NotImplementedError("Unknown topic type")


def handle_proxy_event(topic_str):
    if topic_str is None or isinstance(topic_str, float) or len(topic_str) == 0:  # is none or nan
        return None
    topic_list = split_topic(topic_str)
    type_topic = topic_list[0]
    if len(topic_list) > 1 and (
        type_topic == constants.INCREASE_LIQUIDITY or type_topic == constants.DECREASE_LIQUIDITY or type_topic == constants.COLLECT
    ):
        return int(topic_list[1], 16)
    else:
        return None


def get_tx_type(topics_str):
    topic_list = split_topic(topics_str)
    type_topic = topic_list[0]
    tx_type = constants.type_dict[type_topic]
    return tx_type


def handle_event(tx_type, topics_str, data_hex):
    # proprocess topics string ->topic list
    # topics_str = topics.values[0]
    receipt = current_tick = tick_lower = tick_upper = None
    liquidity = Decimal(np.nan)
    delta_liquidity = Decimal(np.nan)
    current_liquidity = Decimal(np.nan)
    sqrtPriceX96 = Decimal(np.nan)

    topic_list = split_topic(topics_str)

    # data_hex = data.values[0]

    no_0x_data = data_hex[2:]
    chunk_size = 64
    chunks = len(no_0x_data)
    match tx_type:
        case _typing.OnchainTxType.SWAP:
            sender = hex_to_address(topic_list[1])
            receipt = hex_to_address(topic_list[2])
            split_data = ["0x" + no_0x_data[i : i + chunk_size] for i in range(0, chunks, chunk_size)]
            amount0, amount1, sqrtPriceX96, current_liquidity, current_tick = [signed_int(onedata) for onedata in split_data]

        case _typing.OnchainTxType.BURN:
            sender = hex_to_address(topic_list[1])
            tick_lower = signed_int(topic_list[2])
            tick_upper = signed_int(topic_list[3])
            split_data = ["0x" + no_0x_data[i : i + chunk_size] for i in range(0, chunks, chunk_size)]
            liquidity, amount0, amount1 = [signed_int(onedata) for onedata in split_data]
            delta_liquidity = -liquidity
        case _typing.OnchainTxType.MINT:
            # sender = topic_str_to_address(topic_list[1])
            owner = hex_to_address(topic_list[1])
            tick_lower = signed_int(topic_list[2])
            tick_upper = signed_int(topic_list[3])
            split_data = ["0x" + no_0x_data[i : i + chunk_size] for i in range(0, chunks, chunk_size)]
            sender = hex_to_address(split_data[0])
            liquidity, amount0, amount1 = [signed_int(onedata) for onedata in split_data[1:]]
            delta_liquidity = liquidity
        case _typing.OnchainTxType.COLLECT:
            tick_lower = signed_int(topic_list[2])
            tick_upper = signed_int(topic_list[3])
            split_data = ["0x" + no_0x_data[i : i + chunk_size] for i in range(0, chunks, chunk_size)]
            sender = hex_to_address(topic_list[1])
            receipt = hex_to_address(split_data[0])
            amount0, amount1 = [signed_int(onedata) for onedata in split_data[1:]]

        case _:
            raise ValueError("not support tx type")
    return (
        sender,
        receipt,
        Decimal(amount0),
        Decimal(amount1),
        Decimal(sqrtPriceX96),
        Decimal(current_liquidity),
        current_tick,
        tick_lower,
        tick_upper,
        Decimal(liquidity),
        Decimal(delta_liquidity),
    )


def add_proxy_log(df, index, proxy_row):
    df.loc[index, "proxy_data"] = proxy_row.data
    df.at[index, "proxy_topics"] = proxy_row.topics
    df.loc[index, "proxy_log_index"] = proxy_row.log_index


def match_proxy_log(pool_logs: pd.DataFrame, proxy_logs: pd.DataFrame):
    """

    :param pool_logs:
    :param proxy_logs:
    :return:
    """
    pool_logs["tx_type"] = pool_logs.apply(lambda x: get_tx_type(x.topics), axis=1)
    proxy_logs = proxy_logs.set_index(keys="transaction_hash")
    pool_logs["topics"] = pool_logs["topics"].apply(lambda x: split_topic(x))
    proxy_logs["topics"] = proxy_logs["topics"].apply(lambda x: split_topic(x))

    proxy_logs["topic_name"] = proxy_logs["topics"].apply(lambda x: x[0])
    pool_logs["topic_name"] = pool_logs["topics"].apply(lambda x: x[0])

    pool_logs["proxy_topics"] = [[]] * pool_logs.shape[0]

    for index, row in pool_logs.iterrows():
        if row.tx_type == _typing.OnchainTxType.SWAP:
            continue
        if row.transaction_hash not in proxy_logs.index:
            continue
        proxy_tx: pd.DataFrame = proxy_logs.loc[[row.transaction_hash]]
        proxy_tx_matched: pd.DataFrame = proxy_tx.loc[proxy_tx.topic_name == constants.topic_dict[row.topic_name]]

        for pindex, possible_match in proxy_tx_matched.iterrows():
            if row.tx_type == _typing.OnchainTxType.MINT:
                if row.data[66:] == possible_match.data[2:]:
                    add_proxy_log(pool_logs, index, possible_match)
                    break
            elif row.tx_type == _typing.OnchainTxType.COLLECT or row.tx_type == _typing.OnchainTxType.BURN:
                if compare_burn_data(row.data, possible_match.data):
                    add_proxy_log(pool_logs, index, possible_match)
                    break
            else:
                raise ValueError("not support tx type")
    # if no column is generated

    if "proxy_data" not in pool_logs.columns:
        pool_logs["proxy_data"] = None
        pool_logs["proxy_topics"] = [[]] * pool_logs.shape[0]
        pool_logs["proxy_log_index"] = None
    else:
        pool_logs["proxy_topics"] = pool_logs["proxy_topics"].fillna("[]")


def compare_int_with_error(a: int, b: int, error: int = None) -> bool:
    if error is None:
        if a > 10**10:
            error = 30
        elif a > 10**6:
            error = 15
        elif a > 10**2:
            error = 3
        else:
            error = 1
    return abs(a - b) <= error


def compare_burn_data(a: str, b: str) -> bool:
    """
    Compare burn topic data, to decide burn event in pool and proxy is the same.
    Amount in burn and collect might be different, so it has to compare_int_with_error
    example:
    1. https://polygonscan.com/tx/0x2d88b0cc9f8008135accc8667aa907931edf0be01d311fe437336be7cfe511fd#eventlog, there are two burn: log: 371,382
    2. https://polygonscan.com/tx/0xca50d94a36bc730a4ebb46b9e7535075d7da8a4efbbf9cc53638b058516dc907#eventlog, amount in collect topic is different

    Data struct:
    0x0000000000000000000000000000000000000000000000000014aca30ddf7569
      000000000000000000000000000000000000000000000000000041b051acc70d
      0000000000000000000000000000000000000000000000000000000000000000
    """
    if len(a) != 194 or len(b) != 194:
        return False
    if a[0:66] != b[0:66]:
        return False
    if not compare_int_with_error(int("0x" + a[66 : 66 + 64], 16), int("0x" + b[66 : 66 + 64], 16)):
        return False
    if not compare_int_with_error(int("0x" + a[66 + 64 : 66 + 2 * 64], 16), int("0x" + b[66 + 64 : 66 + 2 * 64], 16)):
        return False
    return True
