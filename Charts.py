
# coding: utf-8

# In[2]:

import datetime as dt
from steemdata import SteemData


# In[3]:

db = SteemData().db


# In[4]:

# %load_ext autoreload
# %autoreload 2


# In[5]:

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

# TODO: skip first day of all charts [1:]


# In[24]:

# helpers
from toolz import keyfilter

def keep(d, whitelist):
    return keyfilter(lambda k: k in whitelist, d)


def omit(d, blacklist):
    return keyfilter(lambda k: k not in blacklist, d)


# In[6]:

# go offline for faster workflow
cf.go_offline()


# In[6]:

# go back online to update charts on website
# cf.go_online()


# ## Daily Posts Count

# In[7]:

# time constraints
time_constraints = {
    '$gte': dt.datetime.now() - dt.timedelta(days=90),
}
conditions = {
    'created': time_constraints,
}


# In[8]:

posts = list(db['Posts'].find(conditions, projection={'_id': 0, 'created': 1}))


# In[9]:

len(posts)


# In[10]:

# count number of daily posts
from collections import Counter
c = Counter([x['created'].date() for x in posts])


# In[11]:

# create pandas dataframe
df = pd.DataFrame.from_dict(c, orient='index').reset_index()
df.columns = ['date', 'count']
df = df.sort_values('date')
df.set_index('date', inplace=True)


# In[12]:

df.tail()


# In[13]:

# plot everything but last day
df.ix[1:-1].iplot(title='Daily Post Count',
                 colors=['blue'],
                 theme='white',
                 bestfit=True,
                 filename='steemdata-30d-post-count')


# In[ ]:




# ## Type Frequency Breakdown

# In[14]:

# list op_types
db['AccountOperations'].distinct('type', {})


# In[15]:

# time constraints
time_constraints = {
    '$gte': dt.datetime.now() - dt.timedelta(days=7),
}
conditions = {
    'timestamp': time_constraints,
}


# In[16]:

# count all operations
db['AccountOperations'].find(conditions).count()


# In[17]:

# count operations for each type
query = [
    {'$match': conditions},
    {'$project': {'type':1}},
    {'$group': {'_id': '$type', 'total': {'$sum': 1}}}
]
results = list(db['AccountOperations'].aggregate(query))


# In[18]:

# construct a Pandas dataframe
df = pd.DataFrame(results)
df.columns = ['type', 'total']
total = df['total'].sum()
df['pct'] = df['total'].apply(lambda x: (x/total*100))


# In[19]:

# check most common operations
df.sort_values('pct', ascending=False).head()


# In[20]:

# filter out op_types that are less than 0.05%
df = df[(df['pct'] > 0.05)]


# In[21]:

# render a nice pie chart
pie = go.Pie(
    labels=df['type'].values.tolist(),
    values=df['pct'].values)

layout = go.Layout(title='Blockchain Operations Distribution')
py.iplot(go.Figure(data=[pie], layout=layout), filename='steemdata-7d-type-pct')


# In[22]:

# py.iplot?


# ## Daily Power-Ups

# In[23]:

from steem.converter import Converter

def power_up_down_data(direction='up', days=30, exclude_steemit=False):
    """direction: `up` or `down`."""
    time_constraints = {
        '$gte': dt.datetime.now() - dt.timedelta(days=days),
    }
    conditions = {
        'type': 'fill_vesting_withdraw' if direction == 'down' else 'transfer_to_vesting',
        'timestamp': time_constraints,
    }
    # count daily power up sums
    power_ups = list(db['AccountOperations'].find(conditions))
    
    def power_down_amount(amount):
        """ If power-down is in VESTS, convert it to STEEM first."""
        if amount['asset'] == 'VESTS':
            return Converter().vests_to_sp(amount['amount'])
        return amount['amount']
    
    if direction == 'down':
        return [{
            'account': x['account'],
            'amount': power_down_amount(x['deposited']),
            'date': x['timestamp'].date()
        } for x in power_ups if not (exclude_steemit == True and x['account'] == 'steemit')]
    else:
        return [{
            'account': x['account'],
            'amount': x['amount']['amount'],
            'date': x['timestamp'].date()
        } for x in power_ups]


# In[24]:

#downs = pd.DataFrame(power_up_down_data(direction='down'))
#downs.sort_values(by='amount', ascending=False).head(30)

# downs[downs.account == 'steemit'].head()


# In[25]:

ups = pd.DataFrame(power_up_down_data(direction='up', days=20))
daily_powerups = ups[['amount', 'date']].groupby('date').sum()
daily_powerups.columns = ['UP']


# In[26]:

downs = pd.DataFrame(power_up_down_data(direction='down', days=20))
daily_powerdowns = downs[['amount', 'date']].groupby('date').sum()
daily_powerdowns.columns = ['DOWN']


# In[27]:

combined = pd.merge(daily_powerdowns.reset_index(), daily_powerups.reset_index(), on='date')
combined.set_index('date', inplace=True)


# In[28]:

combined.iplot(kind='bar',
                title='Daily STEEM Power-Up vs Power-Down for past 20 days',
                colors=['blue', 'orange'],
                theme='white',
                filename='steemdata-30d-power-ups')


# In[ ]:




# ## Post by App Type

# In[29]:

# time constraints
time_constraints = {
    '$gte': dt.datetime.now() - dt.timedelta(days=30),
}
conditions = {
    'json_metadata.app': {'$exists': True},
    'created': time_constraints,
}


# In[30]:

posts = list(db['Posts'].find(conditions, projection={'_id': 0, 'json_metadata.app': 1}))
apps = [x['json_metadata']['app'] for x in posts]
# remove version information
apps = [x.split('/')[0] for x in apps]


# In[31]:

# count most common apps
c = Counter(apps)
top_apps = c.most_common(10)


# In[32]:

df = pd.DataFrame(top_apps, index=list(range(1, len(top_apps)+1)))
df.columns = ['App', 'Post Count']
df.head()


# In[33]:

# save table to plotly
from plotly import figure_factory as FF

table = FF.create_table(df, index=True, index_title='Position')
py.iplot(table, filename='steemdata-30d-post-app-types')


# In[ ]:




# ## New Accounts

# In[34]:

# time constraints
time_constraints = {
    '$gte': dt.datetime.now() - dt.timedelta(days=90),
}
conditions = {
    'type': {'$in': ['account_create', 'account_create_with_delegation']},
    'timestamp': time_constraints,
}
projection = {
    '_id': 0,
    'timestamp': 1,
    'creator': 1,
    'new_account_name': 1,
}
accounts = list(db['Operations'].find(conditions, projection=projection))


# In[35]:

accounts = [{
    'creator': x['creator'],
    'name': x['new_account_name'],
    'date': x['timestamp'].date(),
    
} for x in accounts]


# In[36]:

accounts[0]


# In[37]:

df = pd.DataFrame(accounts)
# df.set_index('date', inplace=True)
df.drop('name', axis=1, inplace=True)
df.head()


# In[38]:

df_count = df.groupby('date').count()
df_count.ix[1:-1].iplot(
    theme='white',
    colors=['blue'],
    bestfit=True,
    legend=False,
    title='Daily Account Creation',
    filename='steemdata-account-creation',
)


# In[39]:

df_affiliate = df.groupby('creator').count().sort_values('date', ascending=False)
df_affiliate.ix[:5].iplot(
    kind='bar',
    theme='white',
    colors=['blue'],
    title='Top Account Creators for past 90 days',
    filename='steemdata-account-creation-faucet',
)


# In[ ]:




# ## Author Reward Distribution

# In[40]:

# time constraints
time_constraints = {
    '$gte': dt.datetime.now() - dt.timedelta(days=30),
}
conditions = {
    'type': 'author_reward',
    'timestamp': time_constraints,
    'vesting_payout.amount': {'$gt': 10000},
}
projection = {
    '_id': 0,
    'timestamp': 1,
    'account': 1,
    'vesting_payout.amount': 1,
    'steem_payout.amount': 1,
}
payouts = list(db['AccountOperations'].find(conditions, projection=projection))


# In[41]:

payouts[0]


# In[42]:

def process_payouts(payouts):
    """ Turn author_rewards into normalized VESTS payouts. """
    results = []
    for payout in payouts:
        # if this is a 100% power-up post, cut VESTS in half
        vests = int(payout['vesting_payout']['amount'])
        if int(payout['steem_payout']['amount']) == 0:
            vests = int(vests/2)
        
        results.append({
            'account': payout['account'],
            'permlink': payout.get('permlink', ''),
            'VESTS': vests,
            'date': payout['timestamp'].date(),
        })
    return results


# In[43]:

payouts = process_payouts(payouts)


# In[44]:

payouts[0]


# In[45]:

df = pd.DataFrame(payouts)


# In[46]:

top_earners = df[['account', 'VESTS']].groupby('account').sum().sort_values('VESTS', ascending=False)


# In[47]:

top_earners.iplot(
    kind='area',
    fill=True,
    title='Distribution of Author Rewards for past 30 days',
    colors=['blue', 'orange'],
    theme='white',
    legend=True,
    filename='steemdata-30d-author-rewards'
)


# In[ ]:




# ## How much rewards go to posts vs comments?

# In[48]:

time_constraints = {
    '$gte': dt.datetime.now() - dt.timedelta(days=7),
}
conditions = {
    'type': 'author_reward',
    'timestamp': time_constraints,
    'vesting_payout.amount': {'$gt': 10000},
}
projection = {
    '_id': 0,
    'timestamp': 1,
    'account': 1,
    'permlink': 1,
    'vesting_payout.amount': 1,
    'steem_payout.amount': 1,
}
payouts = list(db['AccountOperations'].find(conditions, projection=projection))


# In[49]:

payouts2 = process_payouts(payouts)


# In[50]:

posts_pool = 0
comments_pool = 0
for p in payouts2:
    if p['permlink'][:3] == "re-":
        comments_pool += p['VESTS']
    else:
        posts_pool += p['VESTS']


# In[51]:

comments_pool/posts_pool*100


# In[52]:

## how about rshares ratio?


# In[53]:

time_constraints = {
    '$gte': dt.datetime.now() - dt.timedelta(days=7),
}
conditions = {
    'created': time_constraints,
}
projection = {
    '_id': 0,
    'identifier': 1,
    'abs_rshares': 1,
    'children_abs_rshares': 1,
}
posts = list(db['Posts'].find(conditions, projection=projection))


# In[54]:

from funcy.colls import pluck
post_rshares = sum(map(int, pluck('abs_rshares', posts)))


# In[55]:

root_posts = list(pluck('identifier', posts))


# In[ ]:




# ## Reputable Users Comments

# In[56]:

# time constraints
time_constraints = {
    '$gte': dt.datetime.now() - dt.timedelta(days=90),
}
conditions = {
    'type': 'comment',
    'timestamp': time_constraints,
}
projection = {
    '_id': 0,
    'json_metadata': 0,
    'body': 0,
    'trx_id': 0,
    'block_num': 0,
    'type': 0,
}
all_comments = list(db['Operations'].find(conditions, projection=projection))


# In[57]:

all_comments[0]


# In[58]:

from steem.utils import is_comment
from funcy import first, complement, pluck


# In[59]:

# split into comments and main posts
comments = list(filter(is_comment, all_comments))
posts = list(filter(complement(is_comment), all_comments))


# In[60]:

# turn datetime into dates
comments = [{**x, 'date': x['timestamp'].date()} for x in comments]
posts = [{**x, 'date': x['timestamp'].date()} for x in posts]


# In[61]:

def filter_accounts(accounts, min_rep=40, min_sp=100):
    """ Return list of accounts that match minimum rep and SP requirements. """
    conditions = {
        'name': {'$in': accounts},
        'sp': {'$gt': min_sp},
        'rep': {'$gt': min_rep},
    }
    projection = {
        '_id': 0,
        'name': 1,
    }
    return [x['name'] for x in db['Accounts'].find(conditions, projection)]


# In[62]:

# create a list of all accounts with adequate Rep/SP for both comments and posts
accounts_to_filter = list(set(pluck('author', comments)) | set(pluck('author', posts)))
qualifying_accounts = filter_accounts(accounts_to_filter)
len(qualifying_accounts)


# In[63]:

def filter_comments(posts_or_comments, qualifying_accounts):
    """ Filter out all posts/comments from disqualified accounts. """
    return [x for x in posts_or_comments if x['author'] in qualifying_accounts]


# In[64]:

def create_df(posts_or_comments):
    df = pd.DataFrame(posts_or_comments)
    df.drop_duplicates(['author', 'permlink'], inplace=True)
    return df[['author', 'date']]


# In[65]:

# prepare all dataframes
comments_df = create_df(comments)
posts_df = create_df(posts)
q_comments_df = create_df(filter_comments(comments, qualifying_accounts))
q_posts_df = create_df(filter_comments(comments, qualifying_accounts))


# In[66]:

comments_df.head()


# In[67]:

def merge_counts(qualified, unqualified):
    """ Merge all comments and comments from reputable authors into single DataFrame. """
    left = qualified.groupby('date').count().ix[:-1]
    left.columns = ['reputable']
    right = unqualified.groupby('date').count().ix[:-1]
    right.columns = ['all']
    
    return pd.merge(left, right, left_index=True, right_index=True)


# In[68]:

merge_counts(q_comments_df, comments_df).iplot(
    theme='white',
    colors=['orange', 'blue'],
    title='Daily Comments Count',
    filename='steemdata-comments-count',
)


# In[ ]:




# ## Withdrawal Prediction

# In[69]:

# only bother with accounts powering down at least 1kV
conditions = {
    'vesting_withdraw_rate.amount': {'$gt': 1000},
}
projection = {
    '_id': 0,
    'vesting_withdraw_rate.amount': 1,
    'next_vesting_withdrawal': 1,
    'name': 1,
}
data = list(db['Accounts'].find(conditions, projection=projection))


# In[70]:

from steem.converter import Converter
withdrawing_accounts = [{
    'name': x['name'],
    'sp': Converter().vests_to_sp(x['vesting_withdraw_rate']['amount']),
    'date': x['next_vesting_withdrawal'].date()} for x in data]


# In[71]:

# how much SP is being powered down right now?
sum(pluck('sp', withdrawing_accounts))


# In[72]:

df = pd.DataFrame(withdrawing_accounts)


# In[73]:

pd_sum = df[['sp', 'date']].groupby('date').sum()
pd_sum.iplot(
    kind='bar',
    theme='white',
    colors=['blue'],
    legend=False,
    title='Future Power-Downs',
    filename='steemdata-future-powerdown',
)


# In[ ]:




# In[ ]:




# ## Transfer from exchanges

# In[74]:

exchanges = ['poloniex', 'bittrex', 'blocktrades']
# time constraints
time_constraints = {
    '$gte': dt.datetime.now() - dt.timedelta(days=60),
}
incoming = {
    'from': {'$in': exchanges},
    'to': {'$nin': exchanges},
}
outgoing = {
    'from': {'$nin': exchanges},
    'to': {'$in': exchanges},
}
conditions = {
    'type': 'transfer',
    'timestamp': time_constraints,
}


# In[75]:

from steem.utils import keep_in_dict
def simplify_transfers(transfers):
    data = [keep_in_dict(x, ['amount', 'from', 'to', 'timestamp']) for x in transfers]
    data = [{
        x['amount']['asset']: x['amount']['amount'],
        'date': x['timestamp'].date(),
        **keep_in_dict(x, ['to', 'from']),
    } for x in data]
    return data


# In[76]:

def exchange_flow(direction='incoming'):
    if direction == 'incoming':
        return simplify_transfers(db['Operations'].find({**conditions, **incoming}))
    return simplify_transfers(db['Operations'].find({**conditions, **outgoing}))


# In[77]:

incoming = exchange_flow('incoming')
outgoing = exchange_flow('outgoing')


# In[78]:

incoming[0]


# In[79]:

incoming_df = pd.DataFrame(incoming).groupby('date')['STEEM'].sum()
outgoing_df = pd.DataFrame(outgoing).groupby('date')['STEEM'].sum() * -1
diff_df = incoming_df + outgoing_df # add together because we mult outgoing by -1 above


# In[80]:

diff_df.head()


# In[81]:

outgoing_df.iplot(kind='bar')


# In[82]:

diff = go.Scatter(
    name='Delta',
    mode = 'lines+markers',
    opacity=0.7,
    x=diff_df.index,
    y=diff_df.values
)

incoming = go.Bar(
    name='Incoming STEEM',
    opacity=0.9,
    x=incoming_df.index,
    y=incoming_df.values
)

outgoing = go.Bar(
    name='Outgoing STEEM',
    opacity=0.9,
    x=outgoing_df.index,
    y=outgoing_df.values
)

colors=['blue', 'orange', 'red']
layout = go.Layout(title='STEEM Exchange Flows')
fig = go.Figure(data=[incoming, outgoing, diff], layout=layout)
py.iplot(fig, filename='steemdata-exchange-flows')

# todo, make bar charts share X axis


# In[ ]:




# ## Daily Transaction Rates
# - avg tx/s, transaction number, transaction volume (USD implied)

# In[27]:

# time constraints
time_constraints = {
    '$gte': dt.datetime.now() - dt.timedelta(days=30),
}
conditions = {
    'type': 'transfer',
    'timestamp': time_constraints,
}
projection = {
    '_id': 0,
    'amount': 1,
    'timestamp': 1,
}
transfers = list(db['Operations'].find(conditions, projection=projection))


# In[28]:

transfers = [
    omit({
        **x,
        'date': x['timestamp'].date(),
         x['amount']['asset']: x['amount']['amount']}, ['timestamp', 'amount']) for x in transfers]


# In[30]:

transfers[0]


# In[33]:

df = pd.DataFrame(transfers).fillna(0)


# In[34]:

df.head()


# In[61]:

# df.groupby('date').aggregate({
#     'SBD': 'sum',
#     'STEEM': 'sum',
# })


# In[82]:

df_sum = df.groupby('date').sum()
df_sum['count'] = df.groupby('date').count()['SBD']
no_dust = df[(df.STEEM > 0.1) | (df.SBD > 0.1)]
df_sum['no_dust'] = no_dust.groupby('date').count()['SBD']


# In[83]:

df_sum.head()


# In[79]:

df_sum.iplot(
    kind='bar',
    theme='white',
    colors=['blue', 'orange'],
    legend=False,
    title='Daily Transfer Volume',
    filename='steemdata-daily-transfer-volume',
)


# In[85]:

data = [
    go.Scatter(
        name='Transactions',
        mode = 'lines+markers',
        opacity=0.7,
        x=df_sum.index,
        y=df_sum['no_dust'].values,
        yaxis='y2'
    ),
    go.Bar(
        name='STEEM Volume',
        opacity=0.9,
        x=df_sum.index,
        y=df_sum['STEEM'].values
    ),
    go.Bar(
        name='SBD Volume',
        opacity=0.9,
        x=df_sum.index,
        y=df_sum['SBD'].values
    )
]

layout = go.Layout(
    title='Daily Transfers',
    yaxis=dict(
        title='Transfer Volume'
    ),
    yaxis2=dict(
        title='Transfer Count (Dust Removed)',
        titlefont=dict(
            color='rgb(148, 103, 189)'
        ),
        tickfont=dict(
            color='rgb(148, 103, 189)'
        ),
        overlaying='y',
        side='right'
    )
)

colors=['blue', 'orange']
fig = go.Figure(data=data, layout=layout)
py.iplot(fig, filename='steemdata-tranfers-2')


# In[75]:

# daily transaction count
df_count = pd.DataFrame()
df_count['All Transfers'] = df.groupby('date').count()['SBD']
no_dust = df[(df.STEEM > 0.1) | (df.SBD > 0.1)]
df_count['/wo Dust'] = no_dust.groupby('date').count()['SBD']


# In[76]:

df_count.head()


# In[77]:

df_count.iplot(
    kind='line',
    theme='white',
    colors=['blue', 'orange'],
    legend=False,
    title='Daily Transfers Count',
    filename='steemdata-daily-transfers-count',
)

