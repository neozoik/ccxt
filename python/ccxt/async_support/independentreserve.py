# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.async_support.base.exchange import Exchange


class independentreserve (Exchange):

    def describe(self):
        return self.deep_extend(super(independentreserve, self).describe(), {
            'id': 'independentreserve',
            'name': 'Independent Reserve',
            'countries': ['AU', 'NZ'],  # Australia, New Zealand
            'rateLimit': 1000,
            'has': {
                'CORS': False,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/30521662-cf3f477c-9bcb-11e7-89bc-d1ac85012eda.jpg',
                'api': {
                    'public': 'https://api.independentreserve.com/Public',
                    'private': 'https://api.independentreserve.com/Private',
                },
                'www': 'https://www.independentreserve.com',
                'doc': 'https://www.independentreserve.com/API',
            },
            'api': {
                'public': {
                    'get': [
                        'GetValidPrimaryCurrencyCodes',
                        'GetValidSecondaryCurrencyCodes',
                        'GetValidLimitOrderTypes',
                        'GetValidMarketOrderTypes',
                        'GetValidOrderTypes',
                        'GetValidTransactionTypes',
                        'GetMarketSummary',
                        'GetOrderBook',
                        'GetAllOrders',
                        'GetTradeHistorySummary',
                        'GetRecentTrades',
                        'GetFxRates',
                    ],
                },
                'private': {
                    'post': [
                        'PlaceLimitOrder',
                        'PlaceMarketOrder',
                        'CancelOrder',
                        'GetOpenOrders',
                        'GetClosedOrders',
                        'GetClosedFilledOrders',
                        'GetOrderDetails',
                        'GetAccounts',
                        'GetTransactions',
                        'GetDigitalCurrencyDepositAddress',
                        'GetDigitalCurrencyDepositAddresses',
                        'SynchDigitalCurrencyDepositAddressWithBlockchain',
                        'WithdrawDigitalCurrency',
                        'RequestFiatWithdrawal',
                        'GetTrades',
                        'GetBrokerageFees',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'taker': 0.5 / 100,
                    'maker': 0.5 / 100,
                    'percentage': True,
                    'tierBased': False,
                },
            },
        })

    async def fetch_markets(self, params={}):
        baseCurrencies = await self.publicGetGetValidPrimaryCurrencyCodes(params)
        quoteCurrencies = await self.publicGetGetValidSecondaryCurrencyCodes(params)
        result = []
        for i in range(0, len(baseCurrencies)):
            baseId = baseCurrencies[i]
            baseIdUppercase = baseId.upper()
            base = self.common_currency_code(baseIdUppercase)
            for j in range(0, len(quoteCurrencies)):
                quoteId = quoteCurrencies[j]
                quoteIdUppercase = quoteId.upper()
                quote = self.common_currency_code(quoteIdUppercase)
                id = baseId + '/' + quoteId
                symbol = base + '/' + quote
                result.append({
                    'id': id,
                    'symbol': symbol,
                    'base': base,
                    'quote': quote,
                    'baseId': baseId,
                    'quoteId': quoteId,
                    'info': id,
                })
        return result

    async def fetch_balance(self, params={}):
        await self.load_markets()
        balances = await self.privatePostGetAccounts(params)
        result = {'info': balances}
        for i in range(0, len(balances)):
            balance = balances[i]
            currencyId = self.safe_string(balance, 'CurrencyCode')
            uppercase = currencyId.upper()
            code = self.common_currency_code(uppercase)
            account = self.account()
            account['free'] = balance['AvailableBalance']
            account['total'] = balance['TotalBalance']
            account['used'] = account['total'] - account['free']
            result[code] = account
        return self.parse_balance(result)

    async def fetch_order_book(self, symbol, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'primaryCurrencyCode': market['baseId'],
            'secondaryCurrencyCode': market['quoteId'],
        }
        response = await self.publicGetGetOrderBook(self.extend(request, params))
        timestamp = self.parse8601(response['CreatedTimestampUtc'])
        return self.parse_order_book(response, timestamp, 'BuyOrders', 'SellOrders', 'Price', 'Volume')

    def parse_ticker(self, ticker, market=None):
        timestamp = self.parse8601(ticker['CreatedTimestampUtc'])
        symbol = None
        if market:
            symbol = market['symbol']
        last = ticker['LastPrice']
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': ticker['DayHighestPrice'],
            'low': ticker['DayLowestPrice'],
            'bid': ticker['CurrentHighestBidPrice'],
            'bidVolume': None,
            'ask': ticker['CurrentLowestOfferPrice'],
            'askVolume': None,
            'vwap': None,
            'open': None,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': None,
            'percentage': None,
            'average': ticker['DayAvgPrice'],
            'baseVolume': ticker['DayVolumeXbtInSecondaryCurrrency'],
            'quoteVolume': None,
            'info': ticker,
        }

    async def fetch_ticker(self, symbol, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'primaryCurrencyCode': market['baseId'],
            'secondaryCurrencyCode': market['quoteId'],
        }
        response = await self.publicGetGetMarketSummary(self.extend(request, params))
        return self.parse_ticker(response, market)

    def parse_order(self, order, market=None):
        symbol = None
        if market is None:
            symbol = market['symbol']
        else:
            market = self.find_market(order['PrimaryCurrencyCode'] + '/' + order['SecondaryCurrencyCode'])
        orderType = self.safe_value(order, 'Type')
        if orderType.find('Market') >= 0:
            orderType = 'market'
        elif orderType.find('Limit') >= 0:
            orderType = 'limit'
        side = None
        if orderType.find('Bid') >= 0:
            side = 'buy'
        elif orderType.find('Offer') >= 0:
            side = 'sell'
        timestamp = self.parse8601(order['CreatedTimestampUtc'])
        amount = self.safe_float(order, 'VolumeOrdered')
        if amount is None:
            amount = self.safe_float(order, 'Volume')
        filled = self.safe_float(order, 'VolumeFilled')
        remaining = None
        feeRate = self.safe_float(order, 'FeePercent')
        feeCost = None
        if amount is not None:
            if filled is not None:
                remaining = amount - filled
                if feeRate is not None:
                    feeCost = feeRate * filled
        feeCurrency = None
        if market is not None:
            symbol = market['symbol']
            feeCurrency = market['base']
        fee = {
            'rate': feeRate,
            'cost': feeCost,
            'currency': feeCurrency,
        }
        id = self.safe_string(order, 'OrderGuid')
        status = self.parse_order_status(self.safe_string(order, 'Status'))
        cost = self.safe_float(order, 'Value')
        average = self.safe_float(order, 'AvgPrice')
        price = self.safe_float(order, 'Price', average)
        return {
            'info': order,
            'id': id,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'lastTradeTimestamp': None,
            'symbol': symbol,
            'type': orderType,
            'side': side,
            'price': price,
            'cost': cost,
            'average': average,
            'amount': amount,
            'filled': filled,
            'remaining': remaining,
            'status': status,
            'fee': fee,
        }

    def parse_order_status(self, status):
        statuses = {
            'Open': 'open',
            'PartiallyFilled': 'open',
            'Filled': 'closed',
            'PartiallyFilledAndCancelled': 'canceled',
            'Cancelled': 'canceled',
            'PartiallyFilledAndExpired': 'canceled',
            'Expired': 'canceled',
        }
        return self.safe_string(statuses, status, status)

    async def fetch_order(self, id, symbol=None, params={}):
        await self.load_markets()
        response = await self.privatePostGetOrderDetails(self.extend({
            'orderGuid': id,
        }, params))
        market = None
        if symbol is not None:
            market = self.market(symbol)
        return self.parse_order(response, market)

    async def fetch_my_trades(self, symbol=None, since=None, limit=50, params={}):
        await self.load_markets()
        pageIndex = self.safe_integer(params, 'pageIndex', 1)
        if limit is None:
            limit = 50
        request = self.ordered({
            'pageIndex': pageIndex,
            'pageSize': limit,
        })
        response = await self.privatePostGetTrades(self.extend(request, params))
        market = None
        if symbol is not None:
            market = self.market(symbol)
        return self.parse_trades(response['Data'], market, since, limit)

    def parse_trade(self, trade, market=None):
        timestamp = self.parse8601(trade['TradeTimestampUtc'])
        id = self.safe_string(trade, 'TradeGuid')
        orderId = self.safe_string(trade, 'OrderGuid')
        price = self.safe_float_2(trade, 'Price', 'SecondaryCurrencyTradePrice')
        amount = self.safe_float_2(trade, 'VolumeTraded', 'PrimaryCurrencyAmount')
        symbol = None
        if market is not None:
            symbol = market['symbol']
        side = self.safe_string(trade, 'OrderType')
        if side is not None:
            if side.find('Bid') >= 0:
                side = 'buy'
            elif side.find('Offer') >= 0:
                side = 'sell'
        return {
            'id': id,
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'order': orderId,
            'type': None,
            'side': side,
            'price': price,
            'amount': amount,
            'fee': None,
        }

    async def fetch_trades(self, symbol, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'primaryCurrencyCode': market['baseId'],
            'secondaryCurrencyCode': market['quoteId'],
            'numberOfRecentTradesToRetrieve': 50,  # max = 50
        }
        response = await self.publicGetGetRecentTrades(self.extend(request, params))
        return self.parse_trades(response['Trades'], market, since, limit)

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        capitalizedOrderType = self.capitalize(type)
        method = 'privatePostPlace' + capitalizedOrderType + 'Order'
        orderType = capitalizedOrderType
        orderType += 'Offer' if (side == 'sell') else 'Bid'
        request = self.ordered({
            'primaryCurrencyCode': market['baseId'],
            'secondaryCurrencyCode': market['quoteId'],
            'orderType': orderType,
        })
        if type == 'limit':
            request['price'] = price
        request['volume'] = amount
        response = await getattr(self, method)(self.extend(request, params))
        return {
            'info': response,
            'id': response['OrderGuid'],
        }

    async def cancel_order(self, id, symbol=None, params={}):
        await self.load_markets()
        request = {
            'orderGuid': id,
        }
        return await self.privatePostCancelOrder(self.extend(request, params))

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'][api] + '/' + path
        if api == 'public':
            if params:
                url += '?' + self.urlencode(params)
        else:
            self.check_required_credentials()
            nonce = self.nonce()
            auth = [
                url,
                'apiKey=' + self.apiKey,
                'nonce=' + str(nonce),
            ]
            keys = list(params.keys())
            for i in range(0, len(keys)):
                key = keys[i]
                value = str(params[key])
                auth.append(key + '=' + value)
            message = ','.join(auth)
            signature = self.hmac(self.encode(message), self.encode(self.secret))
            query = self.ordered({})
            query['apiKey'] = self.apiKey
            query['nonce'] = nonce
            query['signature'] = signature.upper()
            for i in range(0, len(keys)):
                key = keys[i]
                query[key] = params[key]
            body = self.json(query)
            headers = {'Content-Type': 'application/json'}
        return {'url': url, 'method': method, 'body': body, 'headers': headers}
