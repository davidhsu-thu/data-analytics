from ixbrlparse import IXBRL
import requests, io
import numpy as np
from pathlib import Path


headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
             AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'} 
def extract_xbrl(codes, years, items, quarterly=False):
    """
    extract items form financial statements that companies file with the regulator
    codes, a list with companies eg. [1101, 1102]
    years, a list with years eg. [2019, 2020]
    items, a list with items eg. ['Revenue', 'GrossProfit']
    this function will retrieving items and respective amount of the Q4 financial statements from the websiet of mops
    https://mops.twse.com.tw/mops/web/t203sb01
    and return a dictionary (codes will be recasted as string)
    """
    data = {}
    for code in codes:
        for year in years:
            
            quarters = [1, 2, 3, 4] if quarterly else [4]
                
            for quarter in quarters:
                # setting the keys of the dictionary, and value with an emtpy list if the key does not exist 
                data.setdefault('code', []).append(str(code))
                yq = f"{str(year)}Q{str(quarter)}"  
                data.setdefault('date', []).append(yq)
                # data.setdefault('quarter', []).append(quarter)
                is_located = False
                fr_ms = ['fr1-m1', 'fr1-m2', 'fr2-m1', 'fr2-m2']
                for frm in fr_ms:
                    url_add = f'https://mopsov.twse.com.tw/server-java/t164sb01?step=3&SYEAR={str(year)}&file_name=tifrs-{frm}-ci-cr-{str(code)}-{str(year)}Q{quarter}.html'
                    res = requests.get(url_add, headers = headers)
                    res.encoding = 'big5'
                    if '檔案不存在' not in res.text:
                        is_located = True
                        break # found the xbrl file, stop try 
                    else: # not found, continue trying
                        continue
                                         
                # found the xbrl file, parse the data, rather fill in zeors
                if is_located:
                    x = IXBRL(io.StringIO(res.text), raise_on_error=False)
                    for i in x.nonnumeric:
                        if i.name == 'CompanyChineseName':
                            data.setdefault('name', []).append(i.value)
                            break
            
                else: 
                    data.setdefault('name', []).append(np.nan)
                    for item in items:
                        data.setdefault(item, []).append(np.nan)
                    continue
                # found the xbrl file, parse items
                for item in items:
                    is_found = False
                    for i in x.numeric:
                        
                        # point of time data have an instant attribute; period data have an enddate attribute
                        # for quarter data adding a begdate.month to ascertain cumulative value
                        i_year = i.context.instant.year if i.context.enddate is None else i.context.enddate.year
                        # some items may be duplicates. using '_' in the context to make sure the correct one 
                        #(in the body of FS rather than notes) 
                        #startdate None if instant
                        
                        if i.name == item and i_year == year and str(i.context).find('_') == -1:
                            if i.context.instant is None and i.context.startdate.month != 1:
                                continue # if not a cumulative amount, search next 
                            print(code, year, quarter, end='\r')
                            data.setdefault(item, []).append(i.value)
                            is_found = True
                            break # if found break the loop and start the next item
                    # if the item is not found, setting it to zero
                    if not is_found:
                        print(code, year, quarter, end='\r')
                        data.setdefault(item, []).append(np.nan)   
    print("Data Retrieved.", end='\r')
    return data
