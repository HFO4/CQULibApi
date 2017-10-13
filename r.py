# -*- coding: UTF-8 -*-
import requests
import sys
import json
import codecs
import time
import datetime
from bs4 import BeautifulSoup
import re
from flask import render_template,Flask,request,url_for,make_response,send_from_directory
reload(sys)
sys.setdefaultencoding('utf-8')
s = requests.session()
app = Flask(__name__)
userSession = {}
def getToken():
	global s
	r = s.get('https://sso.lib.cqu.edu.cn:8949/adlibSso/login?service=http%3a%2f%2flib.cqu.edu.cn%2findex.aspx')
	#print r.text.encode("GBK","ignore")
	soup = BeautifulSoup(r.text, "html.parser")
	token = []
	token.append(soup.find("input",attrs={"name": "lt"}).get('value'))
	token.append(soup.find("input",attrs={"name": "execution"}).get('value'))
	return token
def login(id,pwd):
	global s
	global userSession
	loginToken = getToken()
	payload = {
				'username': id, 
				'password': pwd,
				'id': 'null',
				'lt': loginToken[0], 
				'execution': loginToken[1],
				'_eventId': 'submit',
				'submit': '登录'
				}
	r = s.post("https://sso.lib.cqu.edu.cn:8949/adlibSso/login?service=http%3A%2F%2Flib15.cqu.edu.cn%2Fmetro%2Freception%2FfrontDask.htm", data=payload)
	if "tishi" in r.text:
		return False
	else:
		userSession["20173658"] = s.cookies
		return True
def getBookList(id,pwd):
	global s
	global userSession
	if not userSession.has_key(id):
		if not login(id,pwd):
			return json.dumps({ 'error' : 403, 'msg' : "登陆失败"} )
	mylist = requests.get('http://lib15.cqu.edu.cn/metro/readerNowBorrowInfo.htm',cookies=s.cookies )
	if "重庆大学图书馆统一身份认证平台" in mylist.text:
		if not login(id,pwd):
			return json.dumps({ 'error' : 403, 'msg' : "登陆失败"} )
			mylist = requests.get('http://lib15.cqu.edu.cn/metro/readerNowBorrowInfo.htm',cookies=s.cookies )
	soup = BeautifulSoup(mylist.text, "html.parser")
	try:
		tab = soup.find_all('table')[1]
	except:
		return json.dumps( { 'error' : 400, 'msg' : "无法获取，账号可能未激活,请前往“我的书斋”设置密码并激活"} )
	data_list = []
	for tr in tab.findAll('tr'):
		i=0
		single_info={}
		for td in tr.findAll('td'):
			if(i==1):
				try:
					key = td.find("a")["href"]
				except:
					return json.dumps([ { 'error' : 200, 'msg' : "无借阅记录"} ])
				p1 = r"(?<=bookId=).+?(?=&bookType)"
				pattern1 = re.compile(p1)
				matcher1 = re.search(pattern1,key)
				single_info['bookId']=matcher1.group(0)
				single_info['bookName']=td.find("a").getText()
			elif(i==2):
				single_info['bookIndex']=td.getText()
			elif(i==3):
				single_info['bookPosition']=td.getText()
			elif(i==4):
				single_info['renewalTime']=td.getText()
			elif(i==5):
				single_info['borrowTime']=td.getText()
			elif(i==6):
				single_info['returnTime']=td.getText()
			elif(i==7):
				key2 = td.find("input")["onclick"]
				p2 = r"(?<=delAlert\(\').+?(?=\',\'true)"
				pattern2 = re.compile(p2)
				matcher2 = re.search(pattern2,key2)
				single_info['renewalId']=matcher2.group(0)
			i=i+1
		if single_info:
			data_list.append(single_info)
		else:
			p=1
	return json.dumps(data_list)
def renewal(id,pwd,bid):
	global s
	global userSession
	if not userSession.has_key(id):
		if not login(id,pwd):
			return json.dumps({ 'error' : 403, 'msg' : "登陆失败"} )
	r = requests.get('http://lib15.cqu.edu.cn/metro/renewbook.htm?stripNumber='+bid,cookies = userSession[id])
	if "重庆大学图书馆统一身份认证平台" in r.text:
		if not login(id,pwd):
			return json.dumps({ 'error' : 403, 'msg' : "登陆失败"} )
		r = requests.get('http://lib15.cqu.edu.cn/metro/renewbook.htm?stripNumber='+bid,cookies = userSession[id])
	if "续借操作失败！" in r.text:
		return json.dumps({ 'error' : 404, 'msg' : "续借失败，ID可能不存在"} )
	if "已经被" in r.text:
		return json.dumps({ 'error' : 400, 'msg' : "续借失败，请24小时后再试"} )
	if "成功" in r.text:
		return json.dumps({ 'error' : 0, 'msg' : "续借成功"} )
@app.route('/getList', methods=['POST'])
def getList():
	if request.method == 'POST':
		return getBookList(request.form['uid'],request.form['pwd']), 200, {'Content-Type': 'application/json'}
@app.route('/renewalBook', methods=['POST'])
def renewalBook():
	if request.method == 'POST':
		return renewal(request.form['uid'],request.form['pwd'],request.form['bid']), 200, {'Content-Type': 'application/json'}
if __name__ == '__main__':
	app.run(port=5001)