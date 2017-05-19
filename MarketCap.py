
# coding: utf-8

# In[40]:

import datetime as dt
from funcy import walk_values, join, flatten, first, rest, rpartial

import pandas as pd
import numpy as np

try:
    import plotly.plotly as py
    import plotly.graph_objs as go
    import cufflinks as cf
except:
    get_ipython().system('pip install plotly')
    get_ipython().system('pip install cufflinks')


# In[ ]:




# In[24]:

# helpers
from toolz import keyfilter

def keep(d, whitelist):
    return keyfilter(lambda k: k in whitelist, d)

def omit(d, blacklist):
    return keyfilter(lambda k: k not in blacklist, d)


# In[ ]:




# In[41]:

import requests

def get_coin(symbol):
    r = requests.get('http://coinmarketcap.northpole.ro/api/v5/%s.json' % symbol.upper())
    return r.json()

def historic_data(urls=None):
    return list(map(lambda x: requests.get(x).json(), urls))

def merge_historic_data(historic_data):
    """ Simplify and flatten all historic data into a single list of events."""
    data = []
    for hist in historic_data:
        data.append([simplify_fragment(x) for x in hist['history'].values()])
    return list(flatten(data))

def simplify_fragment(obj):
    """ Simplify and flatten individual fragment."""
    # clean up the mess
    def replace_values(val):
        if type(val) == dict:
            return walk_values(replace_values, val)
        if val == "?" or val == 'None':
            return 0
        return val
    obj = walk_values(replace_values, obj)
    
    return {
        'symbol': obj['symbol'],
        'category': obj['category'],
        'supply': obj['availableSupplyNumber'],
        'change_btc': round(float(obj['change7d']['btc']), 2),   
        'change_usd': round(float(obj['change7d']['usd']), 2),   
        'position': int(obj['position']),
        'cap_usd': round(float(obj['marketCap']['usd'])),
        'cap_btc': round(float(obj['marketCap']['btc'])),
        'volume_btc': round(float(obj['volume24']['btc'])),
        'price_usd': float(obj['price']['usd']),
        'price_btc': float(obj['price']['btc']),
        'timestamp': dt.datetime.fromtimestamp(obj['timestamp'])
    }


chart_filter = rpartial(
    keep,
    ['symbol', 'timestamp', 'price_usd', 'price_btc', 'cap_usd', 'volume_btc', 'supply'],
)

def simplify_hist_data(historic_data):
    return [keep(x, ['symbol', 'timestamp', 'price_usd']) for x in historic_data]


# In[ ]:




# In[55]:

steem_urls = [
    'http://coinmarketcap.northpole.ro/api/v5/history/STEEM_2016.json',
    'http://coinmarketcap.northpole.ro/api/v5/history/STEEM_2017.json',
]
from toolz import thread_last

steem_chart = thread_last(
    historic_data(steem_urls),
    merge_historic_data,
    (map, chart_filter),
    list,
)


# In[ ]:




# In[63]:

df = pd.DataFrame(steem_chart)


# In[64]:

df.sort_values('timestamp').tail()


# In[77]:

cf.go_offline()


# In[65]:

df.sort_values('timestamp', inplace=True)
df.set_index('timestamp', inplace=True)


# In[76]:

df[['cap_usd', 'supply']].iplot(title='USD Market Cap and STEEM Supply',
                 colors=['blue', 'orange'],
                 theme='white',
                 fill=True,
                 filename='steem-supply-cap')


# In[70]:

get_ipython().magic('pinfo df.iplot')


# In[ ]:



