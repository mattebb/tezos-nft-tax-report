# MIT License

# Copyright (c) 2023 Matt Ebb

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

query_variables = {
	"wallet":  "tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1",
	"timestart": "2021-07-01",
	"timeend": "2022-06-30"
}

buys_start = "2019-01-01"
currency = "AUD"


import json	
import os
import datetime
import csv
import requests

# Prepare conversion rates
# Using the RBA exchange rates spreadsheet cleaned up 
# and exported in CSV form
usd_conv = {}
with open('RBAex-2018-2022.csv', mode='r') as csv_file:
    csv_reader = csv.reader(csv_file)
    for row in csv_reader:
    	if (len(row) > 1):
	    	usd_conv[ row[0] ] = row[1]

# Returns a USD to AUD conversion rate 
# based on the RBA data
def audusd_datetime(dt):
	# Currency conversion to AUD
	aud_rate = None

	# backtrack to find the most recent rate if it doesn't
	# exist for this day
	for num_days in [0, -1, -2, -3, -4, -5]:
		matchdt = dt + datetime.timedelta(days=num_days)
		matchdate = matchdt.strftime('%d-%b-%Y')

		if matchdate not in usd_conv:
			continue
		else:
			aud_rate = float(usd_conv[matchdate])
			break
	if aud_rate is None:
		matchdt = dt + datetime.timedelta(days=num_days)
		matchdate = matchdt.strftime('%d-%b-%Y')
		raise ValueError("Can't find AUD conversion for {}".format(matchdate))

	return aud_rate


# ------- Teztok queries


def run_query(query, variables):
   response = requests.post(
       "https://api.teztok.com/v1/graphql",
       json={'query': query, 'variables': variables},
   )
   if response.status_code == 200:
       return response.json()
   else:
       raise Exception(f'Query failed with a {response.status_code}: {response.json()}')


# Many thanks for Marius Watz for his example queries which kicked all this off
# https://twitter.com/mariuswatz/status/1666715664566874113?s=20

def query_royalties():
	query = '''
	query royalties($wallet: String!, $timestart: timestamptz!, $timeend: timestamptz!) {
	  events(where: {implements: {_eq: "SALE"}, timestamp: { _gte: $timestart, _lt: $timeend}, seller_address: {_neq: $wallet}, artist_address: {_eq: $wallet}}, order_by: {timestamp: asc}) {
	    buyer_profile {
	      alias
	    }
	    buyer_address
	    token {
	      name
	      token_id
	      royalty_receivers {
	        receiver_address
	        royalties
	      }
	    }
	    timestamp
	    seller_address
	    seller_profile {
	      alias
	    }
	    price
	    price_in_usd
	  }
	}'''	
	return run_query(query, query_variables)

def query_sales():
	query = '''
	query Sales ($wallet: String!, $timestart: timestamptz!, $timeend: timestamptz!) {
	  events(where: {implements: {_eq: "SALE"}, seller_address: {_eq: $wallet}, timestamp: {_gte: $timestart, _lt: $timeend}}, order_by: {timestamp: asc}) {
	      timestamp
	      price
	      seller_address
	      seller_profile {
	        alias
	      }
	      price_in_usd
	      token {
	        name
	        fa2_address
	        token_id
	        artist_profile {
	          alias
	        }
	      }
	  }
	}'''
	return run_query(query, query_variables)

def query_buys():
	query = '''
	query Buys ($wallet: String!, $timestart: timestamptz!, $timeend: timestamptz!) {
	  events(where: {implements: {_eq: "SALE"}, buyer_address: {_eq: $wallet}, timestamp: {_gte: $timestart, _lt: $timeend}}, order_by: {timestamp: asc}) {
	    timestamp
	      price
	      seller_address
	      seller_profile {
	        alias
	      }
	      price_in_usd
	      token {
	        name
	        fa2_address
	        token_id
	        artist_profile {
	          alias
	        }
	      }
	  }
	}'''
	buys_variables = query_variables
	buys_variables['timestart'] = buys_start;
	return run_query(query, buys_variables)

# Prepare transaction data
royalties_data = query_royalties()['data']['events']
sales_data = query_sales()['data']['events']
buys_data = query_buys()['data']['events']



# ------- CSV data ouput


def write_csv(filename, rownames, rows):
	with open(filename, "w") as csv_file:
		csv_writer = csv.writer(csv_file, delimiter=',')
		csv_writer.writerow(rownames)
		for r in rows:
			csv_writer.writerow(r)



# ------- Collating the data


primary_rows = []
secondary_rows = []
royalty_rows = []

# Go over all the wallet's sales
for sale in sales_data:
	
	# Find the artist alias if there is one
	# artist = ""
	# if 'artist_profile' in sale['token'].keys() and sale['token']['artist_profile'] is not None:
	# 	artist = sale['token']['artist_profile']['alias']


	# Check if this sale is a secondary sale by scanning over all the wallet's purchased tokens 
	# and grabbing any where the contract address and id match.
	token_fa2 = sale['token']['fa2_address']
	token_id = sale['token']['token_id']
	initial_purchases = [buy for buy in buys_data
					if	buy['token']['fa2_address'] == token_fa2 and 
						buy['token']['token_id'] == token_id ]


	
	# Find the price at the date that it was sold
	dt = datetime.datetime.strptime(sale['timestamp'], '%Y-%m-%dT%H:%M:%S+00:00')
	aud_rate = audusd_datetime(dt)
	pricetz = float(sale['price']) / 1000000.0
	priceusd = float(sale['price_in_usd']) / 1000000.0
	priceaud = priceusd / aud_rate

	# data to write to the csv
	primary_row = [
		sale['token']['name'],		# name
		dt.strftime('%d-%m-%Y'),	# date
		"${:.2f}".format(priceaud),	# sale price in AUD
		"${:.2f}".format(priceusd),	# sale price in USD
		"{:.2f}".format(pricetz),	# sale price in XTZ
		]
	

	# If this token was a primary sale we can add this data
	# and skip over capital gains calculation
	if len(initial_purchases) == 0:
		primary_rows.append(primary_row)
		continue


	# Calculate capital gains from this sale
	
	# Just grab the first initial sale in our list of previous purchases
	# Note! This will probably be incorrect if you've bought/sold two editions of a single token
	# I didnt need this in my case
	buy = initial_purchases[0]

	purchase_dt = datetime.datetime.strptime(buy['timestamp'], '%Y-%m-%dT%H:%M:%S+00:00')
	aud_rate = audusd_datetime(purchase_dt)
	
	# Find the price at the date that it was sold
	purchase_pricetz = float(buy['price']) / 1000000.0
	purchase_priceusd = float(buy['price_in_usd']) / 1000000.0
	purchase_priceaud = purchase_priceusd / aud_rate
	gain_aud = priceaud - purchase_priceaud

	# Skip transaction if purchase and sale are zero...
	# don't care about this for tax purposes
	if pricetz == 0 and purchase_pricetz == 0:
		continue

	# purchase data to write to the csv
	secondary_row = primary_row + [
		purchase_dt.strftime('%d-%m-%Y'),	# date
		"${:.2f}".format(purchase_priceaud),	# sale price in AUD
		"${:.2f}".format(purchase_priceusd),	# sale price in USD
		"{:.2f}".format(purchase_pricetz),	# sale price in XTZ
		"${:.2f}".format(gain_aud),	# gain in AUD
	]
	secondary_rows.append(secondary_row)


# Go over all the wallet's potential royalty events
# Note: this may not cover more complex royalties such as collabs
for event in royalties_data:
	dt = datetime.datetime.strptime(event['timestamp'], '%Y-%m-%dT%H:%M:%S+00:00')
	aud_rate = audusd_datetime(dt)
	pricetz = float(event['price']) / 1000000.0
	priceusd = float(event['price_in_usd']) / 1000000.0
	priceaud = priceusd / aud_rate

	first_receiver = event['token']['royalty_receivers'][0]
	royalty_rate = float(first_receiver['royalties']) / 1000000.0
	royalty_aud = priceaud * royalty_rate

	row = [
		event['token']['name'],
		dt.strftime('%d-%m-%Y'),	# date
		"${:.2f}".format(priceaud),	# sale price in AUD
		"${:.2f}".format(priceusd),	# sale price in USD
		"{:.2f}".format(pricetz),	# sale price in XTZ
		royalty_rate*100,			# multiplier of sale price
		"${:.2f}".format(royalty_aud)
		]
	royalty_rows.append(row)


# Write out the CSVs

primary_names = ['Title', 'Date', 
				 'Sale Price {}'.format(currency),
				 'Sale Price USD', 'Sale Price XTZ']
write_csv("primary-sales.csv", primary_names, primary_rows)

secondary_names = ['Title', 'Date', 
				 'Sale Price {}'.format(currency),
				 'Sale Price USD', 'Sale Price XTZ',
				'Purchase Date', 
				'Purchase Price {}'.format(currency),
				'Purchase Price USD', 'Purchase Price XTZ',
				'Gain {}'.format(currency)]
write_csv("secondary-sales.csv", secondary_names, secondary_rows)

royalty_names = ['Title', 'Date', 
			'Sale Price {}'.format(currency),
			'Sale Price USD', 'Sale Price XTZ',
			'Royalty %',
			'Royalty {}'.format(currency)]
write_csv("royalties.csv", royalty_names, royalty_rows)