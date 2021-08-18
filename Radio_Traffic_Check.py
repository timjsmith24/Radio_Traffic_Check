#!/usr/bin/env python3
import requests
import json
import warnings
import time
import os
import logging
import multiprocessing
from pprint import pprint

warnings.filterwarnings("ignore")

scriptTime = time.strftime("%Y-%m-%d--%H:%M")

PATH = os.path.dirname(os.path.abspath(__file__))

# Wing Controller info
wlc_list = ["192.168.4.4"]
login = {"user":"<NAME>","password":"<PASSWORD>"}

filename = "RadioTrafficInfo.json"

HEADERS= {
    'Content-Type': 'application/json'
    }

#-------------------------
# logging file and info
PATH = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    filename='{}/Radio_Traffic_Check.log'.format(PATH),
    filemode='a',
    level=os.environ.get("LOGLEVEL", "INFO"),
    format= '%(asctime)s: %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
)

file_read_success = True

def debug_print(msg, status):
    lines = msg.splitlines()
    if status == "error":
        for line in lines:
            #print("ERROR: " + line)
            logging.error(line)
    elif status == "warning":
        for line in lines:
            #print("WARNING: " + line)
            logging.warning(line)
    elif status == "info":
        for line in lines:
            #print("WARNING: " + line)
            logging.info(line)

def get_api_token(url):
    try:
        r = requests.get(url, headers=HEADERS, verify=False, auth=(login['user'], login['password']), timeout=8)
    except requests.ConnectionError as e:
        raise TypeError(f"Connection Error - {e}")
    except requests.exceptions.HTTPError as e:
        raise TypeError(f"HTTP Error - {e}")
    except requests.exceptions.Timeout:
        raise TypeError("API call timeout")
    except:
        raise TypeError("API Auth request failed")
    data = json.loads(r.text)
    auth_token = data['data']['auth_token']
    return(auth_token)

def close_api_session(url):
    try:
        r = requests.post(url, headers=HEADERS, verify=False, timeout=8)
    except requests.ConnectionError as e:
        raise TypeError(f"Connection Error - {e}")
    except requests.exceptions.HTTPError as e:
        raise TypeError(f"HTTP Error - {e}")
    except requests.exceptions.Timeout:
        raise TypeError("API call timeout")
    except:
        raise TypeError("API close session request failed")
    try:
        data = json.loads(r.text)
    except:
        logmsg = r.text
        log_msg = "Closing sessions {} failed with message: {}".format(HEADERS['cookie'],logmsg)
        debug_print(log_msg, 'error')
        raise TypeError("Failed to close session {}".format(HEADERS['cookie']))
    if 'return_code' in data:
        if data['return_code'] != 0:
            debug_print("\n\nClosing session returned error {} for sessions {}").format(data['return_code'],HEADERS['cookie'], 'error')
        #else:
        #    print("\n\nSuccessfully closed session")

def post_api_call(url, rf_domain=None, device=None, tokenheader=None):
    global HEADERS
    if rf_domain:
        payload = "{\n\t\"rf-domain\":\"RF_DOMAIN\"\n}"
        payload=payload.replace('RF_DOMAIN',rf_domain)
    elif device:
        payload = "{\n\t\"device\":\"DEVICE\"\n}"
        payload=payload.replace('DEVICE',device)
    else:
        payload = {}
    if tokenheader:
        HEADERS = tokenheader
    try:
        r = requests.post(url, headers=HEADERS, data=payload, verify=False, timeout=60)
    except requests.ConnectionError as e:
        raise TypeError(f"Connection Error - {e}")
    except requests.exceptions.HTTPError as e:
        raise TypeError(f"HTTP Error - {e}")
    except requests.exceptions.Timeout:
        raise TypeError("API call timeout")
    except:
        log_msg = "API request {} failed for site {}".format(url, rf_domain)
        debug_print(log_msg, 'error')
        raise TypeError(log_msg)
    try:
        data = json.loads(r.text)
    except ValueError as e:
        print(e)
        raise TypeError("Response was not in json format")
    except:
        logmsg = r.text
        log_msg = "API post call failed with message: {}".format(logmsg)
        debug_print(log_msg, 'error')
        raise TypeError("Failed to read info from API request {}".format(url))
    if data['return_code'] == 0:
        return(data['data'])
    else:
        log_msg = "{} returned code {}\n{}".format(url,data['return_code'],data['errors'])
        raise ValueError("{}".format(data['errors']))

def radio_stat_collector(url, wlc, domain, HEADERS, mp_queue):
    data = {}

    try:
        rawRadio = post_api_call(url, rf_domain=domain, tokenheader=HEADERS)
    except TypeError as e:
        debug_print(f"{str(e)} on {domain} - {wlc}", 'warning')
        exit()
    except ValueError as e:
        debug_print(f"{str(e)} - {wlc}", 'warning')
        exit()
    except:
        debug_print(f'UNKNOWN ERROR: Radio API Failed on {domain} - {wlc}', 'error')
        exit()
    for radio in rawRadio:
        name = radio['radio_alias']
        data[name]={}
        data[name]['tx_pkts']=radio['tx_pkts']
        data[name]['rx_pkts']=radio['rx_pkts']
    mp_queue.put(data)

def load_json_file(filename):
    if not os.path.isdir(PATH+'/archive'):
        os.makedirs(PATH+'/archive')
        data = {}
        return(data)
    if os.path.isfile(PATH+'/archive/'+filename):
        with open(PATH+'/archive/'+filename, 'r') as f:
            try:
                data = json.load(f)
            except ValueError:
                file_read_success = False
                debug_print(f"failed to load {filename}", "error")
                data = {}
                return(data)
    else: 
        print(f"There was no file {filename}")
        debug_print(f"There was no file {filename}", "error")
        data = {}
    
    if '10' in data:
        del data['10']
    for i in range( 9,0,-1):
        if str(i) in data:
            data[str(i+1)] = data[str(i)]
    if '1' in data:
        del data['1']
    
    return(data)


def main():
    global HEADERS
    ap_list = load_json_file(filename)
    ap_list['1'] = {}
    ap_list['1']['time']= scriptTime
    ap_list['1']['data']={}
    for wlc in wlc_list:
        #print(f"Gathering from {wlc}")
        baseurl = 'https://{}/rest'.format(wlc)
        try:
            url = '{}/v1/act/login'.format(baseurl)
            auth_token = get_api_token(url)
        except TypeError as e:
            debug_print(str(e), 'error')
            continue
        except:
            debug_print(f"Failed to generate token for {wlc}", 'error')
            continue
        HEADERS['cookie']='auth_token={}'.format(auth_token)
        url = '{}/v1/stats/noc/domains'.format(baseurl)
        try:
            rawList = post_api_call(url)
        except TypeError as e:
            debug_print(wlc+str(e), 'error')
            continue
        except:
            debug_print(f'Unknown Error getting Domains on {wlc}', 'error')
            continue
        domainList = [ sub['name'] for sub in rawList ]
        url = '{}/v1/act/logout'.format(baseurl)
        try:
            close_api_session(url)
        except TypeError as e:
            if 'Failed to close session' not in e:
                debug_print(e, 'error')
        except:
            log_msg = (f"Failed to disconnect {HEADERS['cookie']}")
            debug_print(log_msg, 'error')
        sizeofbatch = 100
        for i in range(0, len(domainList), sizeofbatch):
            batch = domainList[i:i+sizeofbatch]
            mp_queue = multiprocessing.Queue()
            processes = []
            url = '{}/v1/act/login'.format(baseurl)
            auth_token = get_api_token(url)
            HEADERS['cookie']='auth_token={}'.format(auth_token)
            url = '{}/v1/stats/wireless/radio-stats'.format(baseurl)
            for domain in batch:
                p = multiprocessing.Process(target=radio_stat_collector, args=(url, wlc, domain, HEADERS, mp_queue))
                processes.append(p)
                p.start()
            for p in processes:
                try:
                    p.join()
                    p.terminate()
                except:
                    debug_print("Error occurred in thread", "error")
            mp_queue.put('STOP')
            for ap in iter(mp_queue.get, 'STOP'):
                ap_list['1']['data'].update(ap)
            url = '{}/v1/act/logout'.format(baseurl)
            try:
                close_api_session(url)
            except TypeError as e:
                if 'Failed to close session' not in str(e):
                    debug_print(str(e), 'error')
            except:
                log_msg = (f"Failed to disconnect {HEADERS['cookie']}")
                debug_print(log_msg, 'error')
    if '1' not in ap_list:
        exit()
    if file_read_success == True:
        with open(PATH+"/archive/"+filename, 'w') as f:
            json.dump(ap_list, f)
    if '2' not in ap_list:
        print("This appears to be the first run. Please run again to compare packet counts")
        debug_print("First run, skipping comparison", "error")
        exit()
    last_list = ap_list['2']['data']
    current_list = ap_list['1']['data']
  
    #pprint(ap_list)

    diff_tx = [k for k in current_list if current_list[k]['tx_pkts'] == last_list[k]['tx_pkts']]
    diff_rx = ([k for k in current_list if current_list[k]['rx_pkts'] == last_list[k]['rx_pkts']])
    diff_list = set(diff_tx + diff_rx)
    
    msg = 'radio, stagnant direction, previous time, recent time, previous tx pkts, recent tx pkts, previous rx pkts, recent rx pkts\n'
    for radio in diff_tx:
        if radio in diff_rx:
            direction = 'both'
        else:
            direction = "tx"
        msg += f"{radio}, {direction}, {ap_list['2']['time']},{ap_list['1']['time']}, {last_list[radio]['tx_pkts']}, {current_list[radio]['tx_pkts']}, {last_list[radio]['rx_pkts']}, {current_list[radio]['rx_pkts']}\n"
    for radio in diff_rx:
        if radio not in diff_tx:
            msg += f"{radio}, rx, {ap_list['2']['time']},{ap_list['1']['time']}, {last_list[radio]['tx_pkts']}, {current_list[radio]['tx_pkts']}, {last_list[radio]['rx_pkts']}, {current_list[radio]['rx_pkts']}\n"
    if len(diff_list) > 0:
        with open(PATH+"/stagnant_radios.csv", 'w') as f:
            f.write(msg)
            debug_print("updated csv file", "info")
if __name__ == '__main__':
    main()