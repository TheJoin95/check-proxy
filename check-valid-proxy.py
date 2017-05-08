#!/usr/bin/python

#author: thejoin

import re, sys, getopt, requests, json, datetime
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
				"protocols": ["http", "https"]
			},
			"websites": [
				{
					"name":"google", 
					"url": "www.google.com"
				}, {
					"name":"lagado",
					"url": "www.lagado.com/proxy-test"
				}, {
					"name":"amazon",
					"url": "www.amazon.com"
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

def isProxyActive(status, value):
	# valutare se aggiungere status: error
	if find_value(status, value):
		statusToSet = "active"
	else:
		statusToSet = "draft"

	return statusToSet

def formatResponse(obj, response, website, method, protocol):
	# anonymityLevel: 1,
	# supportsHttps: true,
	# protocol: 'http',
	# country: 'MX',
	print response

	try:
		if "cookies" in response:
			if "cookies_are" in response.cookies:
				obj["cookies"] = True
			else:
				obj["cookies"] = False

		print "website"
		if "websites" in obj:
			obj["websites"][website] = response.ok
		else:
			obj["websites"] = {}
			obj["websites"][website] = response.ok
		
		print "protocols"
		if "protocols" in obj:
			if website in obj["protocols"]:
				obj["protocols"][website] = obj["protocols"][website] + [protocol]
			else:
				obj["protocols"][website] = [protocol]
		else:
			obj["protocols"] = {}
			#obj["protocols"][website] = protocol
			obj["protocols"][website] = [protocol]

		print "variables"
		obj["elapsed"] = response.elapsed.total_seconds()
		obj["headers"] = response.headers
		if ("X-Forwarded-For" not in response.headers) and ("Forwarded" not in response.headers) and ("Via" not in response.headers) and ("X-Forwarded-Proto" not in response.headers) and ("Proxy-Connection" not in response.headers):
			obj["anonymityLevel"] = "anonymous"
		else:
			obj["anonymityLevel"] = "transparent"

		obj[method] = obj["websites"][website]

		print response.ok
		# print obj["protocols"]
		
		pass
	except Exception, e:
		print "exception"
		print e
		print response
		if "websites" in obj:
			obj["websites"][website] = False
		else:
			obj["websites"] = {}
			obj["websites"][website] = False

		if "protocols" not in obj:
			obj["protocols"] = {}

		obj["timeout"] = True
		if "elapsed" not in obj:
			obj["elapsed"] = None
		if "headers" not in obj:
			obj["headers"] = None

		obj[method] = obj["websites"][website]

		pass

	obj["status"] = isProxyActive(obj["websites"], True)
	try:
		if website in obj["protocols"]:
			obj["http"] = isProxyActive(obj["protocols"][website], "http")
			obj["https"] = isProxyActive(obj["protocols"][website], "https")
	except Exception, e:
		print "exception protocols"
		pass
	finally:
		obj["http"] = "draft"
		obj["https"] = "draft"
		pass

	obj["status"] = obj["status"] == "active" or (obj["https"] == "active" or obj["http"] == "active")

	if obj["status"] == True:
		obj["status"] = "active";
	else:
		obj["status"] = "draft"

	# print obj

	return obj

def reserveProxy(proxies, collection):
	for proxy in proxies:
		collection.update({"_id": proxy["_id"]}, {'$set': {"statustemp": "processing"}})

def addToFile(entry):
	with open(confJson["result_filename"], mode='r', encoding='utf-8') as feedsjson:
		feeds = json.load(feedsjson)

	with open(confJson["result_filename"], mode='w', encoding='utf-8') as feedsjson:
		feeds.append(entry)
		json.dump(feeds, feedsjson)

def testProxy(websites, proxy, conf):
	proxyObj = {
			"http": "http://" + proxy["full_address"],
			"https": "http://" + proxy["full_address"],
		}

	cookies = dict(cookies_are="working")
	
	responseFromWebsite = {}
	responseFromWebsite[proxy["full_address"]] = {}
	for website in websites:
		# i need to update/insert, if db connection exists, proxy's informations
		for protocol in conf["protocols"]:
			urlToCheck = protocol + "://" + website["url"]

			print urlToCheck + ': ' + proxy["full_address"]
			try:
				for method in conf["methods"]:
					if method == "get":
						responseFromWebsite[proxy["full_address"]] = formatResponse(responseFromWebsite[proxy["full_address"]], requests.get(urlToCheck, proxies=proxyObj, timeout=conf["timeout"], cookies=cookies), website["name"], "get", protocol)
					elif method == "post":
						responseFromWebsite[proxy["full_address"]] = formatResponse(responseFromWebsite[proxy["full_address"]], requests.post(urlToCheck, proxies=proxyObj, data={ping: True}, timeout=conf["timeout"], cookies=cookies), website["name"], "post", protocol)

				pass
			except requests.exceptions.RequestException as e:
				print e
				responseFromWebsite[proxy["full_address"]] = formatResponse(responseFromWebsite[proxy["full_address"]], {}, website["name"], "get", protocol) # error
				# proxyCollection.update({'_id':proxy['_id']}, {'$set':{'websites.'+websites['name']: False}})
				pass
			except RuntimeError as eR:
				print "runtimeError"
				print eR
				pass
			except TypeError as eT:
				print "typeError"
				print eT
				pass
			except NameError as eN:
				print "nameError"
				print eN
				pass

	return responseFromWebsite



if __name__ == '__main__':

	argv = sys.argv[1:]
	conf = ""
	queryProxies = {"statustemp":{'$nin':['processing', 'error']}, "updatetime":{'$lt': datetime.datetime.now() - datetime.timedelta(minutes=90)}}
	queryLimit = 20

	try:
  		opts, args = getopt.getopt(argv,"hi:o:s:c:db:d:t:f:conf:r:l:q:v",["status=","db=", "collection=", "psw=", "learn=", "timeout=", "websites=", "filename=", "conf=", "limit=", "refresh=", "query="])
	except getopt.GetoptError:
  		print 'check-valid-proxy.py -status <status> -db <database> -c <collection> -l <learn> -t <timeout> -w <websites> -f <filename> -conf <config> -r <refresh> -l <limit> -q <query>'
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
  		elif opt in ("-t", "--timeout"):
 			timeout = arg
  		elif opt in ("-w", "--websites"):
			websites = arg
  		elif opt in ("-conf", "--conf"):
			conf = arg
  		elif opt in ("-r", "--refresh"):
			queryProxies = {"status": "active", "statustemp": {'$nin':["processing", "error"]}, "updatetime":{'$lt': datetime.datetime.now() - datetime.timedelta(minutes=240)}}
  		elif opt in ("-l", "--limit"):
			queryLimit = int(arg)
  		elif opt in ("-q", "--query"):
			queryProxies = json.loads(arg)

	status = {'$in': ["draft", "active"]} # add more status like error
	confJson = getDefaultConfig(conf)

	print queryProxies
	print queryLimit

	if "proxy_filename" in confJson:
		proxiesResult = getJsonFile(confJson['proxy_filename'])

	if "db" in confJson:
		proxyCollection = MongoClient(w=0)[confJson["db"]["database"]][confJson["db"]["collection"]]
		#proxiesResult = proxyCollection.find({"status": status})
		proxiesResult = proxyCollection.find(queryProxies, no_cursor_timeout=True).sort("updatetime", 1).limit(queryLimit)
		proxiesResult = list(proxiesResult)
		reserveProxy(proxiesResult, proxyCollection)
	else:
		with open(confJson["result_filename"], mode="w", encoding="utf-8") as f:
			json.dump([], f)

	for proxy in proxiesResult:
		# proxyResponses[proxy["full_address"]] = tryProxy(confJson["websites"], proxy, confJson["proxy"])
		responseFromWebsite = testProxy(confJson["websites"], proxy, confJson["proxy"])

		checkStatus = []
		for key, response in responseFromWebsite.items():
			if "db" in confJson:
				if "post" not in response:
					response["post"] = True # assuming if not set

				if "protocols" not in response:
					response["protocols"] = []

				if "http" not in response:
					response["http"] = "draft"

				if "https" not in response:
					response["https"] = "draft"

				if "anonymityLevel" not in response:
					response["anonymityLevel"] = "nd"

				# try:
				# 	countryCode = json.loads(requests.get("http://ip-api.com/json", proxies={
				# 							"http": "http://" + proxy["full_address"],
				# 							"https": "http://" + proxy["full_address"],
				# 						}).content)["countryCode"]
				# 	pass
				# except Exception, e:
				# 	print e
				# 	countryCode = "nd"
				# 	pass

				if "status" in response:
					proxyCollection.update({"_id":proxy["_id"]}, {'$set':{"status":response["status"], "statustemp": "checked", "anonymityLevel": response["anonymityLevel"],"http": response["http"], "https":response["https"], "protocols":response["protocols"], "get": response["get"], "post": response["post"], "updatetime": datetime.datetime.utcnow(),"headers": str(response["headers"]), "elapsed":response["elapsed"],"websites": response["websites"]}})
				else:
					proxyCollection.update({"_id":proxy["_id"]}, {'$set': {"status":"draft","statustemp": "error"}})
