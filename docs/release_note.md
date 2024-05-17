# v1.0.4

* fix bug:
  * [Breaking change]Base and quote token in uniswap price is reversed, you have to toggle the value in from.uniswap.is_token0_base in config file.  

# v1.0.3

* remove datetime.utcfromtimestamp
* add download entry with instance of Config class
* update requirement
* unify csv format from BigQuery and RPC
* unify csv format in linux and windows
* fix bugs

# v1.0.2

* Support feather file format, now you can save file as csv or feather
* fix bug in generate user_lp file

# v1.0.1

* fix bug in querying block range tool.
* add file type of uniswap price

# v1.0.0

* The kernel is refactored to support future needs.
* Add two source (chifra and bigquery) support for aave
* add type:
  * user_lp for userswap, it indicates actions of liquidtion provides
  * add uniswap position, which enable us to view investment behavior from a position perspective
* breaking change:
  * Raw data type has changed, now raw data is independent of DEFI type, it's just another representation of the event log.
  * The chifra download supports automatic invocation of chifra export command, you can execute demeter-fetch directly on the server where chifra is installed, without run chifra export commend first. 
  * Some config has changed:
    * date config has been moved to from
    * ignore_position_id is moved to uniswap

# v0.2.0

* import uniswap data from chifra
* fix bug:
  * if batch_size in rpc section is omitted, an error will raise
  * if tmp file has existed in rpc, the last file may be empty
* breaking change:
  * proxy config has moved to from section

# v0.1.8

* fix bug for aave
* add tick output for aave

# v0.1.7

* add config for base chain

# v0.1.6

* support aave
* add config: 
  * skip_existed in "to" section.
  * dapp_type in "From" section.
  * etherscan_api_key for rpc config. 
* breaking change
  * address of uniswap pool is listed in from.uniswap
  * dapp_type is required