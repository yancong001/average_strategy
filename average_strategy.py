# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on 2019-09-02  15:11

@author:  ancona117@163.com
"""
import pandas as pd
import datetime
import numpy as np
import ujson
from matplotlib import pyplot

POSITION = {
    'cost': 0,  # 成本
    'balance': 0,  # 市值
    'profit': 0,  # 盈亏
    'amount': 0,  # 持仓
    'order_price': 0,  # 成交价
    'size': 0,  # 数量
    'side': None,  # 方向
    'time': None,  # 时间
    'win_rate': None,  # 胜率  （使用当前最新价，与上一次成交价做对比）
    'ave_win_count': 0,  # 平均盈利数量
    'ave_loss_count': 0,  # 平均亏损数量
    'profit_loss_ratio': 0,  # 盈亏比
    'max_loss_period': {'index': 0, 'time_period': {'begin': 0, 'end': 0, 'timedelta': 0}, 'max_loss_money': 0},
    # 'max_continuous_loss_period': {'index':0,'time_period':{'begin':0,'end':0},'timedelta':datetime.timedelta(minutes=0)},  # {'begin':'2019-01-02 11:03:50.500', 'end':'2019-01-02 11:13:52.500']
    'three_m_ave_price': 0,  # 三分钟均价
    'eight_m_ave_price': 0,  # 八分钟均价
    'all_three_m_data': dict(),  # 三分钟360条数据价格
    'all_eight_m_data': dict(),  # 八分钟960条数据价格
}

# 变量
MAX_LOSS_PERIOD = {
    'index': 0,
    'time_period': {'begin': 0, 'end': 0, 'timedelta': 0},
    'max_loss_money': 0
}
MAX_CONTINUOUS_LOSS_PERIOD = {
    'index': 0,
    'time_period': {'begin': 0, 'end': 0},
    'timedelta': 0,
}

# 3分钟数据 list 长度为360 ，8分钟为960

global_index = 0
global_win_count = 0
global_profit_count = 1
global_loss_count = 1
CONTRACT_NUMBER = 1000


class Ave_strategy:
    def __init__(self, file_name):
        # self.buy_switch = False
        # self.sell_switch = False
        self.status = True # 3 分钟均线大于 8 分钟为True，小于为False

        self.init_three_m_index = 0
        self.init_eight_m_index = 0
        self.all_three_m_data = dict()
        self.all_eight_m_data = dict()
        self.ave_three_m_data = None
        self.ave_eight_m_data = None
        self.three_limit = datetime.timedelta(minutes=3)
        self.eight_limit = datetime.timedelta(minutes=8)

        self.df = pd.read_csv(file_name, encoding="gb2312")
        self.strategy_df = pd.DataFrame
        # print(self.strategy_df)
        # pass
        # self.strategy_df.
        self.first_time = datetime.datetime.strptime(self.df['时间'][0], "%Y-%m-%d %H:%M:%S.%f")
        self.first_price = self.df['最新'][0] * CONTRACT_NUMBER

        self.all_three_m_data.update({0: self.first_price})
        self.all_eight_m_data.update({0: self.first_price})

    def run(self):
        total_L = list()
        origin_time = datetime.datetime.strptime(self.df['时间'][1], "%Y-%m-%d %H:%M:%S.%f")
        for _index in range(len(self.df['时间'])):
        # for _index in range(2000):
        #     print(_index)
            str_time = self.df['时间'][_index]
            end_time = datetime.datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S.%f")
            self.all_three_m_data[_index] = float(self.df['最新'][_index]) * CONTRACT_NUMBER
            self.all_eight_m_data[_index] = float(self.df['最新'][_index]) * CONTRACT_NUMBER

            if end_time - origin_time <= self.three_limit:
                continue
            elif end_time - origin_time <= self.eight_limit:
                del self.all_three_m_data[self.init_three_m_index]
                self.init_three_m_index += 1
            else:
                del self.all_three_m_data[self.init_three_m_index]
                del self.all_eight_m_data[self.init_eight_m_index]
                self.init_three_m_index += 1
                self.init_eight_m_index += 1
            self.ave_three_m_data = np.mean(list(self.all_three_m_data.values()))
            self.ave_eight_m_data = np.mean(list(self.all_eight_m_data.values()))

            new_price = float(self.df['最新'][_index]) * CONTRACT_NUMBER

            if self.status == True:
                #开空单
                if self.ave_three_m_data > self.ave_eight_m_data:
                    pass
                else:
                    self.status = False
                    side = 'sell'
                    order_price = float(self.df['买一价'][_index]) * CONTRACT_NUMBER
                    L = self.order(self.all_three_m_data, self.all_eight_m_data, self.ave_three_m_data,
                                   self.ave_eight_m_data,
                                   order_price, new_price, side, end_time)
                    total_L.append(L)
            else:
                #开多单
                if self.ave_three_m_data >= self.ave_eight_m_data:
                    self.status = True
                    side = 'buy'
                    order_price = float(self.df['卖一价'][_index]) * CONTRACT_NUMBER
                    L = self.order(self.all_three_m_data, self.all_eight_m_data, self.ave_three_m_data,
                                   self.ave_eight_m_data,
                                   order_price, new_price, side, end_time)
                    total_L.append(L)
                else:
                    pass


        _data = total_L
        # _data = [all_three_m_data_list, all_eight_m_data_list, three_m_ave_price_list, \
        #          eight_m_ave_price_list, cost_list, amount_list, price_list, size_list, \
        #          side_list, time_list, win_rate_list, ave_win_count_list, ave_loss_count_list, \
        #          profit_loss_ratio_list]

        new_df = self.strategy_df(data=_data, columns=list(POSITION.keys()))
        return new_df

    def cp_dict(self,max_loss_period):
        cp_a = {}
        for k,v in max_loss_period.items():
            cp_a[k] = v
        return cp_a

    def order(self,
              all_three_m_data,
              all_eight_m_data,
              three_m_ave_price,
              eight_m_ave_price,
              order_price,
              new_price,
              side,
              _time,
              ):

        global global_index, global_profit_count, global_loss_count, POSITION

        L = list()
        global_index += 1

        size = -1 if side is 'buy' else 1
        cost = order_price * size
        amount = -size
        balance = new_price * (amount + POSITION.get('amount'))
        profit = balance + cost + POSITION.get('cost')
        if profit > 0:
            global_profit_count += 1
        else:
            global_loss_count += 1
        if (new_price > POSITION.get('order_price') and POSITION.get('side') is 'buy') \
                or (new_price < POSITION.get('order_price') and POSITION.get('side') is 'sell'):
            global global_win_count
            global_win_count += 1

        # 最大亏损时间算法
        if profit < 0 and profit < POSITION.get('max_loss_period').get('max_loss_money'):
            MAX_LOSS_PERIOD['max_loss_money'] = profit
            MAX_LOSS_PERIOD['index'] = global_index
            MAX_LOSS_PERIOD['time_period']['begin'] = _time
            MAX_LOSS_PERIOD['time_period']['end'] = _time + datetime.timedelta(seconds=0.5)
            MAX_LOSS_PERIOD['time_period']['timedelta'] = datetime.timedelta(seconds=0.5)
            POSITION['max_loss_period'].update(MAX_LOSS_PERIOD)

        elif profit < 0 and profit == POSITION.get('max_loss_period').get('max_loss_money'):
            if global_index - MAX_LOSS_PERIOD['index'] == 1:
                MAX_LOSS_PERIOD['index'] = global_index
                MAX_LOSS_PERIOD['max_loss_money'] = profit
                MAX_LOSS_PERIOD['time_period']['end'] = _time
                MAX_LOSS_PERIOD['time_period']['timedelta'] = _time - MAX_LOSS_PERIOD['time_period']['begin']

            else:
                MAX_LOSS_PERIOD['time_period']['begin'] = _time
                MAX_LOSS_PERIOD['time_period']['end'] = _time + datetime.timedelta(seconds=0.5)
                MAX_LOSS_PERIOD['time_period']['timedelta'] = datetime.timedelta(seconds=0.5)

            if MAX_LOSS_PERIOD['time_period']['timedelta'] > POSITION['max_loss_period']['time_period']['timedelta']:
                POSITION['max_loss_period'].update(MAX_LOSS_PERIOD)
            else:
                pass
        else:
            pass
        max_loss_period = self.cp_dict(POSITION['max_loss_period'])
        order_position = {
            'cost': cost + POSITION.get('cost'),
            'balance': balance,
            'profit': profit,
            'amount': amount + POSITION.get('amount'),
            'order_price': order_price,
            'size': abs(size),
            'side': side,
            'time': _time,
            'win_rate': round((global_win_count / global_index), 4),
            'ave_win_count': round((global_profit_count / global_index), 4),
            'ave_loss_count': round((global_loss_count / global_index), 4),
            'profit_loss_ratio': round(global_profit_count / global_loss_count, 4),
            'max_loss_period': max_loss_period,
            # 'max_continuous_loss_period': {'index': 0, 'time_period': {'begin': 0, 'end': 0},
            #                                'timedelta': datetime.timedelta(minutes=0)},
            'three_m_ave_price': three_m_ave_price,
            'eight_m_ave_price': eight_m_ave_price,
            'all_three_m_data': ujson.dumps(all_three_m_data),
            'all_eight_m_data': ujson.dumps(all_eight_m_data),
        }
        POSITION = order_position
        for key, value in order_position.items():
            L.append(value)
        return L

def main():
    total_df = None
    total_df_list = []

    for i in range(2,32):
        day = str(i).rjust(2,'0')
        print(day)
        try:
            strategy_df = Ave_strategy(f'./SC主力/sc主力连续_201901{day}.csv').run()
            total_df_list.append(strategy_df)
        except FileNotFoundError:
            continue
        # strategy_df.to_csv('./test4.csv', mode='a')
    total_df = pd.concat(total_df_list)
    total_df.to_csv('./test4.csv')
    # df = pd.read_csv('./test4.csv')
    time = total_df['time']
    profit = total_df['profit']
    pyplot.plot(time,profit)
    pyplot.show()


main()
