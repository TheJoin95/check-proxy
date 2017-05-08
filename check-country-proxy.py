
import re, sys, getopt, requests, json, datetime
from pymongo import MongoClient

if __name__ == '__main__':
	proxyCollection = MongoClient(w=0).scraping.proxy
	queryProxies = {"status":"active", "country_code": {'$exists': False}}
	proxiesResult = proxyCollection.find(queryProxies, no_cursor_timeout=True).sort("updatetime", 1).limit(50)

	for proxy in proxiesResult:
		try:
			countryCode = json.loads(requests.get("http://ip-api.com/json", timeout=15, proxies={
									"http": "http://" + proxy["full_address"],
									"https": "http://" + proxy["full_address"],
								}).content)["countryCode"]
			pass
		except Exception, e:
			print e
			countryCode = "nd"
			pass

		print proxy["full_address"] + " " + countryCode
		proxyCollection.update({"_id":proxy["_id"]}, {'$set': {"country_code": countryCode}})