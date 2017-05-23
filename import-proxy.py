#!/usr/bin/python

#author: thejoin

import re, sys, getopt, requests, json, datetime, time
from lxml import etree
from lxml.etree import fromstring
from pymongo import MongoClient

scrapingDb = MongoClient(w=0).scraping
limit = "100"

for i in range(0, 5):
	offset = str(i * 100)
	nordVpnUrl = "https://nordvpn.com/wp-admin/admin-ajax.php?searchParameters%5B0%5D%5Bname%5D=proxy-country&searchParameters%5B0%5D%5Bvalue%5D=&searchParameters%5B1%5D%5Bname%5D=proxy-ports&searchParameters%5B1%5D%5Bvalue%5D=&searchParameters%5B2%5D%5Bname%5D=http&searchParameters%5B2%5D%5Bvalue%5D=on&searchParameters%5B3%5D%5Bname%5D=https&searchParameters%5B3%5D%5Bvalue%5D=on&offset="+offset+"&limit="+limit+"&action=getProxies"
	request = requests.get(nordVpnUrl)
	proxies = []
	for proxy in request.json():
		ptype = proxy["type"].lower()
		proxies.append({
				"full_address": proxy['ip'] + ':' + proxy['port'],
				"address": proxy['ip'],
				"port": proxy['port'],
				"updatetime": datetime.datetime.utcnow(),
				"country": proxy["country"],
				"country_code": proxy["country_code"],
				ptype : "active",
				"source": "nordvpn"
			})

try:
	scrapingDb.proxy.insert(proxies, continue_on_error=True)
	print "importo da nordvpn"
	pass
except Exception, e:
	print e
	pass

now = datetime.datetime.now()
day = str(now.strftime("%d"))
month = str(now.strftime("%m"))
year = str(now.year)
text = requests.get("http://proxyserverlist-24.blogspot.it/"+year+"/"+month+"/"+day+"-"+month+"-"+year[2:]+"-fast-proxy-server-list.html").text
match = re.findall(r"\d+\.\d+\.\d+\.\d+:\d+", text)
proxies = []
for full_address in match:
	proxies.append({
				"full_address": full_address,
				"address": full_address.split(":")[0],
				"port": full_address.split(":")[1],
				"updatetime": datetime.datetime.utcnow(),
				"source": "proxyserverlist24"
			})

try:
	scrapingDb.proxy.insert(proxies, continue_on_error=True)
	print "importo da proxtserverlist24"
	pass
except Exception, e:
	print e
	pass


now = datetime.datetime.now()
day = str(now.strftime("%d"))
month = str(now.strftime("%m"))
year = str(now.year)
hour = now.strftime("%-H")

if int(hour) == 0:
	hour = ""
else:
	hour = "-2"

text = requests.get("http://proxy-daily.com/"+year+"/"+month+"/"+day+"-"+month+"-"+year+"-proxy-list"+hour+"/").text
match = re.findall(r"\d+\.\d+\.\d+\.\d+:\d+", text)
proxies = []
for full_address in match:
	proxies.append({
				"full_address": full_address,
				"address": full_address.split(":")[0],
				"port": full_address.split(":")[1],
				"updatetime": datetime.datetime.utcnow(),
				"source": "proxydayly"
			})

try:
	scrapingDb.proxy.insert(proxies, continue_on_error=True)
	print "importo da proxydayly"
	pass
except Exception, e:
	print e
	pass

# print "http://sslproxies24.blogspot.it/"+year+"/"+month+"/"+day+"-"+month+"-"+year[2:]+"-free-google-proxies-140.html"
xml = etree.fromstring(requests.get("http://sslproxies24.blogspot.com/feeds/posts/default?alt=rss").content)
proxies = []
for c in xml.findall('channel'):
	for text in [c.findall('item')[0].findtext('description'), c.findall('item')[1].findtext('description')]:
		match = re.findall(r"\d+\.\d+\.\d+\.\d+:\d+", text)
		for full_address in match:
			proxies.append({
						"full_address": full_address,
						"address": full_address.split(":")[0],
						"port": full_address.split(":")[1],
						"updatetime": datetime.datetime.utcnow(),
						"source": "sslproxies24"
					})
try:
	scrapingDb.proxy.insert(proxies, continue_on_error=True)
	print "Importo da sslproxies24"
	pass
except Exception, e:
	print e
	pass


with open('/home/pi/proxy_formatter/test/proxies.json') as data_file:    
    data = json.load(data_file)
    proxyToInsert = []
    for i in range(0, len(data)):
    	proxyToInsert.append({
    			"full_address": data[i]['ipAddress'] + ':' + str(data[i]['port']),
				"address": data[i]['ipAddress'],
				"port": data[i]['port'],
				"updatetime": datetime.datetime.utcnow(),
				"country_code": data[i]["country"].upper(),
				"source": "nodejs"
    		})

        if i % 1000 == 0 or i == len(data):
			scrapingDb.proxy.insert(proxyToInsert, continue_on_error=True)
			proxyToInsert = []
			print "inseriti 1000"
			time.sleep(15)


    print "importo da nodejs: " + str(len(data))
	#scrapingDb.proxy.insert(proxies, continue_on_error=True)

    # {u'country': u'it', u'port': 1189, u'source': u'incloak', u'anonymityLevel': u'transparent', u'ipAddress': u'212.237.25.23', u'protocols': [u'http']}