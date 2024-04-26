from ixbrlparse import IXBRL
import requests, io

headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
             AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'} 
def extract_xbrl(codes, years, items):
    """
    extract items from financial statements that companies file with the regulator
    codes, a list with companies eg. [1101, 1102]
    years, a list with years eg. [2019, 2020]
    items, a list with items eg. ['Revenue', 'GrossProfit']
    this function will retrieving items and their respective amounts of the Q4 financial statements from the websiet of mops
    https://mops.twse.com.tw/mops/web/t203sb01
    and return a dictionary
    """
    data = {}
    for code in codes:
        for year in years:
            # setting the keys of the dictionary, and value with an emtpy list if the key does not exist 
            data.setdefault('code', []).append(code)
            data.setdefault('date', []).append(year)
            url_add = f'https://mops.twse.com.tw/server-java/t164sb01?step=1&CO_ID={str(code)}&SYEAR={str(year)}&SSEASON=4&REPORT_ID=C'
            res = requests.get(url_add, headers = headers)
            res.encoding = 'big5'
            x = IXBRL(io.StringIO(res.text), raise_on_error=False)
            for item in items:
                is_found = False
                for i in x.numeric:
                    
                    # point of time data have an instant attribute; period data have an enddate attribute
                    i_year = i.context.instant.year if i.context.enddate is None else i.context.enddate.year
                    # some items may be duplicates. using '_' in the context to make sure the correct one 
                    #(in the body of FS rather than notes)
                    if i.name == item and i_year == year  and str(i.context).find('_') == -1:
                                            
                        print(code, year, end='\r')
                        # retrieved value is dollar unit
                        data.setdefault(item, []).append(i.value)
                        is_found = True
                        break # if found break the loop and start the next item
                # if the item is not found, setting it to zero
                if not is_found:
                    print(code, year, end='\r')
                    data.setdefault(item, []).append(0)   
    return data
