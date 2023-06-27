# tezos-nft-tax-report
This script generates CSV data of Tezos NFT transactions for tax purposes. It is dependent on the Teztok API (http://teztok.com) which it queries to get NFT transaction data related to a given Tezos wallet.

USD and EUR prices are included by default since they come in the Teztok API, and prices are also converted to AUD at the time of each transaction, using historical conversion data from the Reserve Bank of Australia (https://www.rba.gov.au/statistics/historical-data.html) that I pulled out into a simple csv. With a bit of python knowledge it should be trivial to swap that function out to convert other currency data. 

This is intended to be very simple - a single python file with no external module dependencies. Hopefully it's easy enough for others to repurpose too.

**Note:** I am not an accountant, this is just a tool that helped me prepare some info for my own accountants. Please do not rely on this as anything authoritative regarding whatever specific tax regulations you have, and please get it checked by a professional.

Many thanks for Marius Watz for his example teztok queries which kicked this off:
https://twitter.com/mariuswatz/status/1666715664566874113?s=20

## Potential Issues
This is just a cleaned up version of what I hacked together for my own purposes. It may or may not be useful for your situation out of the box, though I hope it is. Some things it won't support since I didn't need it:
- Calculating capital gains on transactions if you have bought/sold more than one edition of an identical token
- Calculating royalties on more complex scenarios like collabs

## Instructions
To use the script, first edit `report.py` to add your wallet address in the **query_variables** dictionary. timestart and timeend represent the period that you are reporting sales over (eg. your financial/tax year). 
```
query_variables = {
	"wallet":  "tz1NqA15BLrMFZNsGWBwrq8XkcXfGyCpapU1",
	"timestart": "2021-07-01",
	"timeend": "2022-06-30"
}
```

Then in a terminal, run
```
> python3 report.py
```

## Output
It will output three CSV files that you can import into a spreadsheet where you can do further sums or edits as you wish

- primary-sales.csv

![image](https://github.com/mattebb/tezos-nft-tax-report/assets/1897197/3bf7f087-d955-4018-9e39-7022722bbc4d)
 
- secondary-sales.csv

![image](https://github.com/mattebb/tezos-nft-tax-report/assets/1897197/754ace3d-ed5f-4535-b678-d97899977396)

- royalties.csv

![image](https://github.com/mattebb/tezos-nft-tax-report/assets/1897197/ba967153-d34c-469f-8597-3532c7b9a66d)

## License
Copyright 2023 Matt Ebb, licensed under the MIT license
