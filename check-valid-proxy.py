#!/usr/bin/python

#author: thejoin

import re, sys, getopt, requests, json
from pymongo import MongoClient

def getJsonFile(filename):
	fileContent = []
	if filename != '':
		f = open(filename,"r")
		try:
			fileContent = json.loads(f)
			pass
		except Exception, e:
			print 'error: filename - invalid json'
			pass
		finally:
			print 'warning: try to read splitline from filename'
			fileContent = f.read().splitlines()
			pass

		f.close()

	return fileContent

def getDefaultConfig(conf):
	confJson = {}
	try:
		confJson = getJsonFile(conf)
		pass
	except Exception, e:
		print e
		pass
	finally:
		confJson = {
			"db": {
				"connection": "mongodb://localhost:27017/",
				"database": "scraping",
				"collection": "proxy"
			},
			"proxy": {
				"timeout": 20,
				"methods": ["get"],
				"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36",
			},
			"websites": [
				{
					"name":"google", 
					"url": "http://www.google.com"
				}, {
					"name":"lagado",
					"url": "http://www.lagado.com/proxy-test"
				}, {
					"name":"amazon",
					"url": "http://www.amazon.com"
				}
			],
			"learn": False
		}
		pass

	
	return confJson

def find_value(obj, val):
	for v in obj:
		if v == val:
			return True

def formatResponse(response):
	formatted = {
		"status": response.status_code
	}
	return formatted

def tryProxy(websites, proxy, conf):
	proxyObj = {
			"http": "http://" + proxy["full_address"],
			"https": "http://" + proxy["full_address"],
		}
		
	responseFromWebsite = {}
	for website in websites:
		# i need to update/insert, if db connection exists, proxy's informations
		print website['url'] + ': ' + proxy["full_address"]
		try:
			for method in conf["methods"]:
				if method == "get":
					responseFromWebsite[website["name"]] = formatResponse(requests.get(website["url"], proxies=proxyObj, timeout=conf["timeout"]))
				elif method == "post":
					responseFromWebsite[website["name"]] = formatResponse(requests.post(website["url"], proxies=proxyObj, data={ping: True}, timeout=conf["timeout"]))

		except requests.exceptions.RequestException as e:
			print e
			responseFromWebsite[website["name"]] = "error"
			# proxyCollection.update({'_id':proxy['_id']}, {'$set':{'websites.'+websites['name']: False}})
			pass

	return responseFromWebsite



if __name__ == '__main__':

	argv = sys.argv[1:]
	conf = ""
	try:
  		opts, args = getopt.getopt(argv,"hi:o:s:c:db:d:t:f:conf:v",["status=","db=", "collection=", "psw=", "learn=", "timeout=", "websites=", "filename=", "conf="])
	except getopt.GetoptError:
  		print 'check-valid-proxy.py -status <status> -db <database> -c <collection> -l <learn> -t <timeout> -w <websites> -f <filename> -conf <config>'
  		sys.exit(2)
	for opt, arg in opts:
  		if opt == '-h':
 			print 'check-valid-proxy.py -u <usr> -p <psw> -d <domain> -t <recordType> -v <value>'
 			sys.exit()
  		elif opt in ("-c", "--collection"):
 			collection = arg
  		elif opt in ("-db", "--database"):
 			database = arg
  		elif opt in ("-s", "--status"):
 			status = arg
  		elif opt in ("-l", "--learn"):
 			learn = arg
  		elif opt in ("-t", "--timeout"):
 			timeout = arg
  		elif opt in ("-w", "--websites"):
			websites = arg
  		elif opt in ("-conf", "--conf"):
			conf = arg

	status = {'$in': ["draft", "active"]} # add more status like error
	confJson = getDefaultConfig(conf)
	print confJson
	if "proxy_filename" in confJson:
		fileContent = getJsonFile(confJson['proxy_filename'])

	if "db" in confJson:
		proxyCollection = MongoClient(w=0)[confJson["db"]["database"]][confJson["db"]["collection"]]
		proxiesResult = proxyCollection.find({"status": status})

	for proxy in proxiesResult:

		responseFromWebsite = tryProxy(confJson["websites"], proxy, confJson["proxy"])

		checkStatus = []
		for key, response in responseFromWebsite.items():
		#for response in responseFromWebsite:
			print response
			if response["status"] != 200:
				checkStatus.append(False)
				proxyCollection.update({"_id":proxy["_id"]}, {'$set':{"websites."+key: False}})
			else:
				checkStatus.append(True)
				proxyCollection.update({"_id":proxy["_id"]}, {'$set':{"websites."+key: True}})

		# valutare se aggiungere status: error
		if find_value(checkStatus, True):
			statusToSet = "active"
		else:
			statusToSet = "draft"

		proxyCollection.update({"_id": proxy["_id"]}, {'$set': {"status": statusToSet}})
