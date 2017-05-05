import datetime as dt
import time

import cufflinks as cf
import pandas as pd
import plotly.graph_objs as go
import plotly.plotly as py
from steem.converter import Converter
from steemdata import SteemData

db = SteemData().db

# go back online to update charts on website
cf.go_online()

while True:
    # time constraints
    time_constraints = {
        '$gte': dt.datetime.now() - dt.timedelta(days=90),
    }
    conditions = {
        'created': time_constraints,
    }
    posts = list(db['Posts'].find(conditions, projection={'_id': 0, 'created': 1}))
    # count number of daily posts
    from collections import Counter
    c = Counter([x['created'].date() for x in posts])

    # create pandas dataframe
    df = pd.DataFrame.from_dict(c, orient='index').reset_index()
    df.columns = ['date', 'count']
    df = df.sort_values('date')
    df.set_index('date', inplace=True)

    # plot everything but last day
    df.ix[1:-1].iplot(title='Daily Post Count',
                     colors=['blue'],
                     theme='white',
                     bestfit=True,
                     filename='steemdata-30d-post-count')


    # list op_types
    db['AccountOperations'].distinct('type', {})

    # time constraints
    time_constraints = {
        '$gte': dt.datetime.now() - dt.timedelta(days=7),
    }
    conditions = {
        'timestamp': time_constraints,
    }

    # count operations for each type
    query = [
        {'$match': conditions},
        {'$project': {'type':1}},
        {'$group': {'_id': '$type', 'total': {'$sum': 1}}}
    ]
    results = list(db['AccountOperations'].aggregate(query))


    # construct a Pandas dataframe
    df = pd.DataFrame(results)
    df.columns = ['type', 'total']
    total = df['total'].sum()
    df['pct'] = df['total'].apply(lambda x: (x/total*100))

    # filter out op_types that are less than 0.05%
    df = df[(df['pct'] > 0.05)]

    # render a nice pie chart
    pie = go.Pie(
        labels=df['type'].values.tolist(),
        values=df['pct'].values)

    layout = go.Layout(title='Blockchain Operations Distribution')
    py.iplot(go.Figure(data=[pie], layout=layout), filename='steemdata-7d-type-pct')


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

    ups = pd.DataFrame(power_up_down_data(direction='up', days=20))
    daily_powerups = ups[['amount', 'date']].groupby('date').sum()
    daily_powerups.columns = ['UP']

    downs = pd.DataFrame(power_up_down_data(direction='down', days=20))
    daily_powerdowns = downs[['amount', 'date']].groupby('date').sum()
    daily_powerdowns.columns = ['DOWN']

    combined = pd.merge(daily_powerdowns.reset_index(), daily_powerups.reset_index(), on='date')
    combined.set_index('date', inplace=True)

    combined.iplot(kind='bar',
                    title='Daily STEEM Power-Up vs Power-Down for past 20 days',
                    colors=['blue', 'orange'],
                    theme='white',
                    filename='steemdata-30d-power-ups')

    # time constraints
    time_constraints = {
        '$gte': dt.datetime.now() - dt.timedelta(days=30),
    }
    conditions = {
        'json_metadata.app': {'$exists': True},
        'created': time_constraints,
    }

    posts = list(db['Posts'].find(conditions, projection={'_id': 0, 'json_metadata.app': 1}))
    apps = [x['json_metadata']['app'] for x in posts]
    # remove version information
    apps = [x.split('/')[0] for x in apps]

    # count most common apps
    c = Counter(apps)
    top_apps = c.most_common(10)

    df = pd.DataFrame(top_apps, index=list(range(1, len(top_apps)+1)))
    df.columns = ['App', 'Post Count']
    df.head()

    # save table to plotly
    from plotly import figure_factory as FF

    table = FF.create_table(df, index=True, index_title='Position')
    py.iplot(table, filename='steemdata-30d-post-app-types')

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

    accounts = [{
        'creator': x['creator'],
        'name': x['new_account_name'],
        'date': x['timestamp'].date(),

    } for x in accounts]

    df = pd.DataFrame(accounts)
    # df.set_index('date', inplace=True)
    df.drop('name', axis=1, inplace=True)
    df.head()

    df_count = df.groupby('date').count()
    df_count.ix[1:-1].iplot(
        theme='white',
        colors=['blue'],
        bestfit=True,
        legend=False,
        title='Daily Account Creation',
        filename='steemdata-account-creation',
    )

    df_affiliate = df.groupby('creator').count().sort_values('date', ascending=False)
    # df_affiliate.ix[:5].iplot(
    #     kind='bar',
    #     theme='white',
    #     colors=['blue'],
    #     title='Top Account Creators for past 90 days',
    #     filename='steemdata-account-creation-faucet',
    # )

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


    def process_payouts(payouts):
        """ Turn author_rewards into normalized VESTS payouts. """
        results = []
        for payout in payouts:
            # if this is a 100% power-up post, cut VESTS in half
            vests = int(payout['vesting_payout']['amount'])
            if int(payout['steem_payout']['amount']) == 0:
                vests = int(vests / 2)

            results.append({
                'account': payout['account'],
                'permlink': payout.get('permlink', ''),
                'VESTS': vests,
                'date': payout['timestamp'].date(),
            })
        return results

    payouts = process_payouts(payouts)

    df = pd.DataFrame(payouts)
    top_earners = df[['account', 'VESTS']].groupby('account').sum().sort_values('VESTS', ascending=False)
    top_earners.iplot(
        kind='area',
        fill=True,
        title='Distribution of Author Rewards for past 30 days',
        colors=['blue', 'orange'],
        theme='white',
        legend=True,
        filename='steemdata-30d-author-rewards'
    )

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
    payouts2 = process_payouts(payouts)
    posts_pool = 0
    comments_pool = 0
    for p in payouts2:
        if p['permlink'][:3] == "re-":
            comments_pool += p['VESTS']
        else:
            posts_pool += p['VESTS']
    comments_pool/posts_pool*100

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


    from funcy.colls import pluck
    post_rshares = sum(map(int, pluck('abs_rshares', posts)))
    root_posts = list(pluck('identifier', posts))

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


    from steem.utils import is_comment
    from funcy import complement, pluck

    # split into comments and main posts
    comments = list(filter(is_comment, all_comments))
    posts = list(filter(complement(is_comment), all_comments))

    # turn datetime into dates
    comments = [{**x, 'date': x['timestamp'].date()} for x in comments]
    posts = [{**x, 'date': x['timestamp'].date()} for x in posts]

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

    # create a list of all accounts with adequate Rep/SP for both comments and posts
    accounts_to_filter = list(set(pluck('author', comments)) | set(pluck('author', posts)))
    qualifying_accounts = filter_accounts(accounts_to_filter)
    len(qualifying_accounts)

    def filter_comments(posts_or_comments, qualifying_accounts):
        """ Filter out all posts/comments from disqualified accounts. """
        return [x for x in posts_or_comments if x['author'] in qualifying_accounts]

    def create_df(posts_or_comments):
        df = pd.DataFrame(posts_or_comments)
        df.drop_duplicates(['author', 'permlink'], inplace=True)
        return df[['author', 'date']]

    # prepare all dataframes
    comments_df = create_df(comments)
    posts_df = create_df(posts)
    q_comments_df = create_df(filter_comments(comments, qualifying_accounts))
    q_posts_df = create_df(filter_comments(comments, qualifying_accounts))


    def merge_counts(qualified, unqualified):
        """ Merge all comments and comments from reputable authors into single DataFrame. """
        left = qualified.groupby('date').count().ix[:-1]
        left.columns = ['reputable']
        right = unqualified.groupby('date').count().ix[:-1]
        right.columns = ['all']

        return pd.merge(left, right, left_index=True, right_index=True)

    merge_counts(q_comments_df, comments_df).iplot(
        theme='white',
        colors=['orange', 'blue'],
        title='Daily Comments Count',
        filename='steemdata-comments-count',
    )

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

    withdrawing_accounts = [{
        'name': x['name'],
        'sp': Converter().vests_to_sp(x['vesting_withdraw_rate']['amount']),
        'date': x['next_vesting_withdrawal'].date()} for x in data]

    df = pd.DataFrame(withdrawing_accounts)

    pd_sum = df[['sp', 'date']].groupby('date').sum()
    pd_sum.iplot(
        kind='bar',
        theme='white',
        colors=['blue'],
        legend=False,
        title='Future Power-Downs',
        filename='steemdata-future-powerdown',
    )

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

    from steem.utils import keep_in_dict
    def simplify_transfers(transfers):
        data = [keep_in_dict(x, ['amount', 'from', 'to', 'timestamp']) for x in transfers]
        data = [{
            x['amount']['asset']: x['amount']['amount'],
            'date': x['timestamp'].date(),
            **keep_in_dict(x, ['to', 'from']),
        } for x in data]
        return data

    def exchange_flow(direction='incoming'):
        if direction == 'incoming':
            return simplify_transfers(db['Operations'].find({**conditions, **incoming}))
        return simplify_transfers(db['Operations'].find({**conditions, **outgoing}))

    incoming = exchange_flow('incoming')
    outgoing = exchange_flow('outgoing')

    incoming_df = pd.DataFrame(incoming).groupby('date')['STEEM'].sum()
    outgoing_df = pd.DataFrame(outgoing).groupby('date')['STEEM'].sum() * -1
    diff_df = incoming_df + outgoing_df # add together because we mult outgoing by -1 above

    # outgoing_df.iplot(kind='bar')

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

    print('End, sleeping...')
    time.sleep(3600*16)
