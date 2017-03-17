#!/usr/bin/python

#author: thejoin

import re, sys, getopt, requests, json
from pymongo import MongoClient

def find_value(obj, val):
	for v in obj:
		if v == val:
			return True

if __name__ == '__main__':

	argv = sys.argv[1:]

	timeout = 20
	status = {'$in': ['draft', 'active']} # add more status like error
	websites = [
					{
						'name':'google', 
						'url': 'http://www.google.com'
					}, {
						'name':'lagado',
						'url': 'http://www.lagado.com/proxy-test'
					}, {
						'name':'amazon',
						'url': 'http://www.amazon.com'
					}
				] # add more website sample like amazon.com

	methods = ['get']
	userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36'

	learn = False
	database = 'scraping'
	collection = 'proxy'
	filename = ''
	
	try:
  		opts, args = getopt.getopt(argv,"hi:o:s:c:db:d:t:f:v",["status=","db=", "collection=", "psw=", "learn=", "timeout=", "websites=", "filename="])
	except getopt.GetoptError:
  		print 'check-valid-proxy.py -status <status> -db <database> -c <collection> -l <learn> -t <timeout> -w <websites> -f <filename>'
  		sys.exit(2)
	for opt, arg in opts:
  		if opt == '-h':
     			print 'dns.py -u <usr> -p <psw> -d <domain> -t <recordType> -v <value>'
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
  		elif opt in ("-f", "--file"):
    			 filename = arg

    # need to validate and make sure the parsing it will work
	if filename != '':
		fileContent = []
		f = open(filename,"r")
		try:
			fileContent = json.loads(f.read())
			pass
		except Exception, e:
			print 'error: filename - invalid json'
			pass
		finally:
			print 'warning: try to read splitline from filename'
			fileContent = f.read().splitlines()
			pass

		f.close()

	proxyCollection = MongoClient(w=0)[database][collection]
	proxiesResult = proxyCollection.find({"status": status})

	for proxy in proxiesResult:
		print proxy
		proxyObj = {
			'http': 'http://' + proxy['full_address'],
			'https': 'http://' + proxy['full_address'],
		}
		
		if len(websites) > 0:
			responseFromWebsite = {}
			for website in websites:
				# i need to update/insert, if db connection exists, proxy's informations
				print website['url'] + ': ' + proxy['full_address']
				try:
					response = requests.get(website['url'], proxies=proxyObj, timeout=timeout)
					#print response.text
					responseFromWebsite[website['name']] = response.status_code
					if(response.status_code != 200):
						print 'error:' + str(response.status_code)
						#proxyCollection.update({'_id':proxy['_id']}, {'$set':{'status':'draft'}, '$addToSet':{'websites': website['name']}})
					else:
						print 'ok'
						#proxyCollection.update({'_id':proxy['_id']}, {'$set':{'status':'active'}})
				except requests.exceptions.RequestException as e:
					print e
					responseFromWebsite[website['name']] = 'error'
					proxyCollection.update({'_id':proxy['_id']}, {'$set':{'status':'error'}})
					pass

			checkStatus = []
			for (key, val) in responseFromWebsite:
				print responseFromWebsite
				print key
				if val != 200:
					checkStatus.append(False)
					proxyCollection.update({'_id':proxy['_id']}, {'$set':{'websites.'+key: False}})

			# valutare se aggiungere status: error
			if find_value(checkStatus, True):
				statusToSet = 'active'
			else:
				statusToSet = 'draft'

			proxyCollection.update({'_id': proxy['_id']}, {'$set': {'status': statusToSet}})
