#!/usr/bin/python

#author: thejoin

import re, sys, getopt, requests, json
from pymongo import MongoClient

global confJson

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
				"timeout": 10,
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
	for k, v in obj.items():
		if v == val:
			return True

def isProxyActive(status):
	# valutare se aggiungere status: error
	if find_value(status, True):
		statusToSet = "active"
	else:
		statusToSet = "draft"

	return statusToSet

def formatResponse(obj, response, website):
	try:
		if "cookies_are" in response.cookies:
			obj["cookies"] = True
		else:
			obj["cookies"] = False

		if "websites" in obj:
			obj["websites"][website] = False if response.status_code != 200 else True
		else:
			obj["websites"] = {}
			obj["websites"][website] = False if response.status_code != 200 else True
		
		pass
	except Exception, e:
		pass
	finally:
		if "websites" in obj:
			obj["websites"][website] = False
		else:
			obj["websites"] = {}
			obj["websites"][website] = False

		obj["timeout"] = True

		pass

	obj["status"] = isProxyActive(obj["websites"])

	return obj

def addToFile(entry):
	with open(confJson["result_filename"], mode='r', encoding='utf-8') as feedsjson:
		feeds = json.load(feedsjson)

	with open(confJson["result_filename"], mode='w', encoding='utf-8') as feedsjson:
		feeds.append(entry)
		json.dump(feeds, feedsjson)

def tryProxy(websites, proxy, conf):
	proxyObj = {
			"http": "http://" + proxy["full_address"],
			"https": "http://" + proxy["full_address"],
		}

	cookies = dict(cookies_are="working")
	
	responseFromWebsite = {}
	responseFromWebsite[proxy["full_address"]] = {}
	for website in websites:
		# i need to update/insert, if db connection exists, proxy's informations
		print website['url'] + ': ' + proxy["full_address"]
		try:
			for method in conf["methods"]:
				if method == "get":
					responseFromWebsite[proxy["full_address"]] = formatResponse(responseFromWebsite[proxy["full_address"]], requests.get(website["url"], proxies=proxyObj, timeout=conf["timeout"], cookies=cookies), website["name"])
				elif method == "post":
					responseFromWebsite[proxy["full_address"]] = formatResponse(responseFromWebsite[proxy["full_address"]], requests.post(website["url"], proxies=proxyObj, data={ping: True}, timeout=conf["timeout"], cookies=cookies), website["name"])

		except requests.exceptions.RequestException as e:
			print e
			responseFromWebsite[proxy["full_address"]] = formatResponse(responseFromWebsite[proxy["full_address"]], {}, website["name"]) # error
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

	if "proxy_filename" in confJson:
		proxiesResult = getJsonFile(confJson['proxy_filename'])

	if "db" in confJson:
		proxyCollection = MongoClient(w=0)[confJson["db"]["database"]][confJson["db"]["collection"]]
		proxiesResult = proxyCollection.find({"status": status})
	else:
		with open(confJson["result_filename"], mode="w", encoding="utf-8") as f:
			json.dump([], f)

	# proxyResponses = {}
	for proxy in proxiesResult:
		# proxyResponses[proxy["full_address"]] = tryProxy(confJson["websites"], proxy, confJson["proxy"])
		responseFromWebsite = tryProxy(confJson["websites"], proxy, confJson["proxy"])

		checkStatus = []
		for key, response in responseFromWebsite.items():
		#for response in responseFromWebsite:
			print response
			if "db" in confJson:
				proxyCollection.update({"_id":proxy["_id"]}, {'$set':{"status":response["status"], "websites": response["websites"]}})
				# if response["status"] != 200:
				#	checkStatus.append(False)
				#	proxyCollection.update({"_id":proxy["_id"]}, {'$set':{"websites"+key: False}})
				#else:
				#	checkStatus.append(True)
				#	proxyCollection.update({"_id":proxy["_id"]}, {'$set':{"websites"+key: True}})

		
		# statusToSet = isProxyActive(checkStatus)
		# if "db" in confJson:
		#	proxyCollection.update({"_id": proxy["_id"]}, {'$set': {"status": statusToSet}})

	# if "db" in confJson:
	# 	for responseObj in proxyResponses:
	# 		checkStatus = []
	# 		for key, response in responseObj.items():
	# 			if response["status"] != 200:
	# 				checkStatus.append(False)
	# 				proxyCollection.update({"_id":proxy["_id"]}, {'$set':{"websites."+key: False}})
	# 			else:
	# 				checkStatus.append(True)
	# 				proxyCollection.update({"_id":proxy["_id"]}, {'$set':{"websites."+key: True}})

			
	# 		statusToSet = isProxyActive()
	# 		proxyCollection.update({"_id": proxy["_id"]}, {'$set': {"status": statusToSet}})