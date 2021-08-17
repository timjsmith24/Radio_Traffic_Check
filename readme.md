# Radio Traffic Check
## Radio_Traffic_Check.py
### Purpose
This script will check to see if tx and rx packets are incrementing on Wing radios. Radios that have not incremented since the last time the script was ran will be added to the 'stagnant_radios.csv' file.

### User Input
list of WiNG controller IPs or DNS names, ssh credentials for the controllers
Controllers IPs or DNS names need to be in quotes and sperated by commas as below
###### lines 17-19
```
#Wing Controller info
wlc_list = ["<IP ADDRESS OR DNS NAME>","<IP ADDRESS OR DNS NAME>", "<IP ADDRESS OR DNS NAME>"]
login = {"user":"<NAME>","password":"<PASSWORD>"}
```

### Outputs
#### csv file 
```
radio, stagnant direction, previous time, recent time, previous tx pkts, recent tx pkts, previous rx pkts, recent rx pkts
AP8533-PTP-RT:R3, both, 2021-08-17--14:08,2021-08-17--14:53, 0, 0, 0, 0
AP8533-PTP-RT:R1, both, 2021-08-17--14:08,2021-08-17--14:53, 0, 0, 0, 0
AP7532-PTP-BR:R1, both, 2021-08-17--14:08,2021-08-17--14:53, 0, 0, 0, 0
```
#### log file
stores any log information from the script
###### Radio_Traffic_Check.log
```
2021-08-17 14:53:55: root - WARNING - ['unable to get data for [wireless/radio-stats], error: Unable to locate rf-domain manager for 0091'] - 10.0.20.4
2021-08-17 14:53:55: root - WARNING - ['unable to get data for [wireless/radio-stats], error: Unable to locate rf-domain manager for default'] - 192.168.4.4
2021-08-17 14:53:58: root - ERROR - Connection Error - HTTPSConnectionPool(host='192.168.16.1', port=443): Max retries exceeded with url: /rest/v1/act/login (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x10ad1d8b0>, 'Connection to 192.168.16.1 timed out. (connect timeout=3)'))
2021-08-17 14:53:58: root - INFO - updated csv file
```
### Requirements
Python3 is required for this script.
The python requests module will need to be installed. If pip is installed, this can be done with pip install requests