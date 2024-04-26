#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024-01-09 11:21
# @Author  : 32ethers
# @Description:
from collections import namedtuple
from datetime import timedelta, date

import os
from typing import List, Dict, Callable, Tuple

import pandas as pd
from tqdm import tqdm

from ._typing import Config, FromConfig, ToFileType
from .utils import TimeUtil, set_global_pbar

EmptyNamedTuple = namedtuple("EmptyNamedTuple", [])


class Node:

    name = "ParentNode"

    def __init__(self):  # depends: List,
        self.depend_instance: List[Node] = []
        self.depends_dict: Dict[str, Node] = {}
        self.config: Config | None = None
        self.from_config: FromConfig | None = None
        self.to_path: str | None = None

    depend = []

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        if type(self) is not type(other):
            return False
        # !!! actually, instead of compare reference, i should compare property
        if self.config != other.config:
            return False
        return True

    def set_depend_instance(self, depends: List):
        self.depend_instance = depends
        self.depends_dict = {d.name: d for d in self.depend_instance}

    def get_config_for_depend(self, depend_name: str) -> List[Config]:
        return [self.config]

    def set_depend(self, depends: List):
        self.depend_instance = depends

    def set_config(self, config: Config):
        self.config = config
        self.from_config = config.from_config
        self.to_path = config.to_config.save_path

    def work(self):
        set_global_pbar(None)
        missing_params: List[EmptyNamedTuple] = []
        if self.config.to_config.skip_existed:
            step_file_names = self.get_file_paths
            for key, fn in step_file_names.items():
                if not os.path.exists(fn):
                    missing_params.append(key)
                    break
            if len(missing_params) < 1:
                return
        data = {}
        for depend in self.depend_instance:
            data[depend.name] = list(depend.get_file_paths.values())
        pbar = tqdm(total=len(missing_params), ncols=80, position=0, leave=False)
        set_global_pbar(pbar)
        for param in missing_params:
            df = self._process_one(data, param)
            self.save_file(df, self.get_file_path(param))
            pbar.update()

    def _process_one(self, data: Dict[str, List[str]], param: namedtuple) -> pd.DataFrame:
        return pd.DataFrame()

    # region Function about files

    def _get_file_name(self, param: namedtuple) -> str:
        return f"{self.name}-{str(param)}.csv"

    def get_file_path(self, param: namedtuple) -> str:
        return os.path.join(self.to_path, self._get_file_name(param))

    @property
    def get_file_paths(self) -> Dict[namedtuple, str]:
        return {
            EmptyNamedTuple(): self.get_file_path(EmptyNamedTuple()),
        }

    @property
    def _load_csv_converter(self) -> Dict[str, Callable]:
        """
        if you want to read csv generated by this step with pandas, you have to use those csv converter
        :return:
        """
        return {}

    @property
    def _parse_date_column(self) -> List[str]:
        return []

    def _get_file_ext(self):
        match self.config.to_config.to_file_type:
            case ToFileType.csv:
                return ".csv"
            case ToFileType.feather:
                return ".feather"
            case _:
                raise RuntimeError(f"{self.config.to_config.to_file_type.name} not supported")

    def save_file(self, df: pd.DataFrame, path: str):
        match self.config.to_config.to_file_type:
            case ToFileType.csv:
                df.to_csv(path, index=False, lineterminator="\n")
            case ToFileType.feather:
                df.to_feather(path)
            case _:
                raise RuntimeError(f"{self.config.to_config.to_file_type.name} not supported")

    def read_file(self, path: str):
        match self.config.to_config.to_file_type:
            case ToFileType.csv:
                return pd.read_csv(path, converters=self._load_csv_converter, parse_dates=self._parse_date_column)
            case ToFileType.feather:
                return pd.read_feather(path)
            case _:
                raise RuntimeError(f"{self.config.to_config.to_file_type.name} not supported")

    def get_depend_by_name(self, name: str):
        return self.depends_dict[name]

    # endregion

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


DailyParam = namedtuple("DailyParam", ["day"])


class DailyNode(Node):
    """
    Node whose input and output and dependings are daily, and generate only one file per day.
    """

    def __init__(self):
        super().__init__()

    def work(self):
        set_global_pbar(None)
        # if daily, global loop will handle processbar, outfile existence, gather param
        day_idx = self.from_config.start
        pbar = tqdm(total=(self.from_config.end - self.from_config.start).days + 1, ncols=80, position=0, leave=False)
        set_global_pbar(pbar)
        while day_idx <= self.from_config.end:
            # day_str = day_idx.strftime("%Y-%m-%d")
            day_param = DailyParam(day_idx)
            step_file_name = self.get_file_path(day_param)
            if self.config.to_config.skip_existed and os.path.exists(step_file_name):
                day_idx += timedelta(days=1)
                continue
            param = {}
            for depend in self.depend_instance:
                depend_file_path = depend.get_file_path(day_param)
                param[depend.name] = depend.read_file(depend_file_path)
            df = self._process_one_day(param, day_idx)
            self.save_file(df, self.get_file_path(day_param))
            day_idx += timedelta(days=1)
            pbar.update()

    def _process_one_day(self, data: Dict[str, pd.DataFrame], day: date) -> pd.DataFrame:
        return pd.DataFrame()

    @property
    def get_file_paths(self) -> Dict[namedtuple, str]:
        return {
            DailyParam(day): self.get_file_path(DailyParam(day))
            for day in TimeUtil.get_date_array(self.from_config.start, self.from_config.end)
        }


AaveDailyParam = namedtuple("AaveDailyParam", ["day", "token"])


class AaveDailyNode(Node):
    """
    Node whose input and output and dependings are daily, and generate multiple files per day.
    """

    def __init__(
        self,
    ):
        super().__init__()

    @property
    def get_file_paths(self) -> Dict[namedtuple, str]:
        ret = {}
        for day in TimeUtil.get_date_array(self.from_config.start, self.from_config.end):
            for token in self.from_config.aave_config.tokens:
                param = AaveDailyParam(day, token)
                ret[param] = self.get_file_path(param)
        return ret

    def work(self):
        set_global_pbar(None)
        # if daily, global loop will handle processbar, outfile existence, gather param
        day_idx = self.from_config.start
        pbar = tqdm(total=(self.from_config.end - self.from_config.start).days + 1, ncols=80, position=0, leave=False)
        set_global_pbar(pbar)
        while day_idx <= self.from_config.end:
            # check file exist
            if self.config.to_config.skip_existed:
                all_exist = True
                for token in self.from_config.aave_config.tokens:
                    data_depends = AaveDailyParam(day_idx, token)
                    step_file_name = self.get_file_path(data_depends)
                    if not os.path.exists(step_file_name):
                        all_exist = False
                        break
                if all_exist:
                    day_idx += timedelta(days=1)
                    continue

            data_depends = {}
            for depend in self.depend_instance:
                token_data = {}
                for token in self.from_config.aave_config.tokens:
                    path = depend.get_file_path(AaveDailyParam(day_idx, token))
                    token_data[token] = depend.read_file(path)
                data_depends[depend.name] = token_data

            token_dfs = self._process_one_day(data_depends, day_idx, self.from_config.aave_config.tokens)
            for token, df in token_dfs.items():
                self.save_file(df, self.get_file_path(AaveDailyParam(day_idx, token)))
            day_idx += timedelta(days=1)
            pbar.update()

    def _process_one_day(
        self, data: Dict[str, Dict[str, pd.DataFrame]], day: date, tokens: List[str]
    ) -> Dict[str, pd.DataFrame]:
        return {}
