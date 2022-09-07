from time import sleep
import requests
import json
import openpyxl

from datetime import date

queriedItem = {}

def debug(x):
  print(x, repr(eval(x)))

def getLeaseOutOder(id):
  sleep(1)
  url = 'http://api.youpin898.com/api/trade/Order/GetTopLeaseOutOrderList?TemplateId=' + str(id)
  res = requests.get(url, verify=False)
  data = json.loads(res.text).get('Data')
  return data

def getOfferOder(id):
  sleep(1)
  url = 'http://api.youpin898.com/api/trade/Order/GetTopOfferOrderList?TemplateId=' + str(id)
  res = requests.get(url, verify=False)
  data = json.loads(res.text).get('Data')
  return data

def getFindValue(id):
  sleep(1)
  url = 'https://api.youpin898.com/api/youpin/commodity/purchase/find'
  payload = { "templateId": str(id), "pageIndex": 1, "pageSize": 20 }
  res = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
  data = json.loads(res.text).get('data').get('response')
  minPrice = 0
  for item in data:
    minPrice = max(minPrice, item['unitPrice'] / 100)
  return minPrice

def analyseObject(id):
  LeaseOutData = getLeaseOutOder(id)
  OfferData = getOfferOder(id)
  dateGap = False
  expectedIncomePerDay = 0.0
  prevDate = date.today()
  if len(LeaseOutData) == 0 or len(OfferData) == 0:
    return []
  uniqueData = {}
  for LeaseOuts in LeaseOutData:
    if uniqueData.get(LeaseOuts['LeaseDays']) == None:
      uniqueData[LeaseOuts['LeaseDays']] = 1000000
    uniqueData[LeaseOuts['LeaseDays']] = min(uniqueData[LeaseOuts['LeaseDays']], LeaseOuts['LeaseUnitPrice'])
  for LeaseOuts in LeaseOutData:
    expectedIncomePerDay += uniqueData[LeaseOuts['LeaseDays']] * (LeaseOuts['LeaseDays'] / (LeaseOuts['LeaseDays'] + 7))
    # print(uniqueData[LeaseOuts['LeaseDays']] * (LeaseOuts['LeaseDays'] / (LeaseOuts['LeaseDays'] + 7)))
    nowDate = date.fromisoformat(LeaseOuts['DateTime'].replace('.', '-'))
    if (prevDate - nowDate).days > 1:
      dateGap = True
    prevDate = nowDate
  if dateGap:
    return []
  expectedIncomePerDay /= len(LeaseOutData)
  shortPriceSum, longPriceSum = 0, 0
  shortCnt, longCnt = 0, 0
  for item in uniqueData.items():
    if item[0] < 21:
      shortPriceSum += item[1]
      shortCnt += 1
    else:
      longPriceSum += item[1]
      longCnt += 1
  lowestPrice = OfferData[0]['Price']
  for offers in OfferData:
    lowestPrice = min(lowestPrice, offers['Price'])
  lowestPrice = max(lowestPrice, getFindValue(id))
  IncomeRate = expectedIncomePerDay * 365 / max(lowestPrice, getFindValue(id))
  return [lowestPrice, shortPriceSum / max(shortCnt, 1), longPriceSum / max(longCnt, 1), expectedIncomePerDay, IncomeRate, shortPriceSum * 8 / 15 * 365 / lowestPrice, longPriceSum * 21 / 28 * 365 / lowestPrice]
  
def getObjectList(i: int):
  payload = {
    "gameId": "730",
    "listSortType": "2",
    "listType": "30",
    "maxPrice": 8,
    "minPrice": "0.1",
    "pageIndex": 1,
    "pageSize": 20,
    "sortType": "0"
  }
  url = "https://api.youpin898.com/api/homepage/es/template/GetCsGoPagedList"
  res = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
  data = json.loads(res.text).get('Data')
  for item in data:
    if queriedItem.get(item['SortId']) == None:
      queriedItem[item['SortId']] = 1
      sheet1.append([item['CommodityName'], item['SortId'], item['TypeName']] + analyseObject(item['SortId']))

if __name__ == '__main__':
  print(analyseObject(102319))
  '''
  wb = openpyxl.Workbook()
  sheet1 = wb.active
  sheet1.append(['商品名称', '悠悠有品ID', '类型', '最低卖出价', '短租平均最低价', '长租平均最低价', '每天期望收入', '回报率', '短期回报率', '长期回报率'])
  for i in range(1, 50):
    print("solving list", i)
    getObjectList(i)
    if i & 1:
      wb.save('yyyp.xlsx')
  '''

