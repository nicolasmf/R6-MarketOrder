# R6 MarketSnipe

This tool can be used to buy a certain item for cheap, also called sniping. 

Don't hesitate to create issues to ask for more functionalities.

## Usage

- Create a .env file like this
```
AUTH_TOKEN = ""
SESSION_ID = ""
APP_ID = ""
```
- Change the URL with the one of the item you want in the 9th line of the main script
- Run and wait !

### Find the variable values 

- Go to the [Rainbow6 Markeplace](https://www.ubisoft.com/en-us/game/rainbow-six/siege/marketplace?route=home)
- Open the network dev tools
- Navigate to either the Buy, Sell, or My Transactions
- You'll get a POST request with everything you need.