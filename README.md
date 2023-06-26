# tezos-nft-tax-report
This script generates CSV data of Tezos NFT transactions for tax purposes. It queries the Teztok API to get NFT transaction data related to a given Tezos wallet.
This is just a cleaned up version of what I hacked together for my own purposes, so it may not be useful completely out of the box for other people. I hope it is though!

It's converting prices to AUD at the time of each transaction, using conversion data from the Reserve Bank of Australia (https://www.rba.gov.au/statistics/historical-data.html) that I pulled out into a simple csv. With a bit of python knowledge it should be trivial to swap that out for other currency data.

USD prices are included by default alongside AUD.

This is intended to be very simple - a single python file with no external dependencies. Hopefully it's easy enough for others to repurpose too.

Many thanks for Marius Watz for his example teztok queries which kicked this off:
https://twitter.com/mariuswatz/status/1666715664566874113?s=20

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
It will output three CSV files that you can then import into a spreadsheet to present as you wish

- primary-sales.csv
- secondary-sales.csv
- royalties.csv

## License
Copyright 2023 Matt Ebb, licensed under the MIT license
