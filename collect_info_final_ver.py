# __*__ coding: utf-8 __*__
'''
爬取消防检测报告，并保存信息。
'''

#----导入模块----
import requests
import time
import bs4
import csv
import codecs
import random

#----常量声明----
main_url = 'http://jsfw.gdfire.gov.cn/WebPage/SSJC_SearchXM.aspx'    #报告网站主页
page_start = 1 #584   #报告搜集起始页
page_end = 1 #739     #报告搜索终止页
create_switch = False  #生成csv开关

#----定义函数----
def get_html(url):
#功能：通过给定的url获取其html
#随机取等待时间，延迟响应
    while True:
        try:
            waittime = random.randint(2,3)
            print('break {}s...'.format(waittime))
            time.sleep(waittime)
            html = requests.get(url,timeout = waittime).text
            return(html)
        except:
            print('Connecting timeout,waiting for next connect...')

def collect_post_info(html):
#功能：搜集页面中的动态信息，用于post请求。
#需要的信息为'__VIEWSTATE'和'__EVENTVALIDATION'
    soup = bs4.BeautifulSoup(html,"html.parser")
    viewstate = soup.find('input',id='__VIEWSTATE').get('value')
    #****打印监控信息****
    print('__VIEWSTATE was found.')
    eventvalidation = soup.find('input',id='__EVENTVALIDATION').get('value')
    #****打印监控信息****
    print('__EVENTVALIDATION was found.')
    return viewstate,eventvalidation

def go_to_page(url,vs,ev,page_num):
#功能：通过post请求上传信息，实现页面跳转功能。
#content-type：application/x-www-form-urlencoded
#需要post的信息：
#    __VIEWSTATE ：随网页动态生成
#    __EVENTVALIDATION ：随网页动态生成
#    ShowPager_input ：需要去往的页码
#    ShowPager ： 操作类型
    d = {'__VIEWSTATE': vs, 
        '__EVENTVALIDATION': ev,
        'ShowPager_input':str(page_num),
        'ShowPager':'go'}
    while True:
        try:
            response = requests.post(url, data=d)
            html = response.text
            return html
        except:
            print('Failed to update current page.')
            print('break 2s...')
            time.sleep(2)

def collect_info_in_page(page_html,info_list,pages):
#功能：通过循环实现当前列表页中的报告信息搜集，并记录出现的访问异常信息。
#关联函数：get_html(),collect_info(),write2txt()
    rpt_list = collect_report_url(page_html)
    #****打印监控信息****
    print('report list updated')
    #报告序号计数器
    count = 1
    for short_rpt_url in rpt_list:
        try:
            full_rpt_url = 'http://jsfw.gdfire.gov.cn/WebPage/' + short_rpt_url
            rpt_html = get_html(full_rpt_url)
            
            #随机取等待时间，延迟响应
            #waittime = random.randint(1,2)
            #print('break another {}s...'.format(waittime))
            #time.sleep(waittime)
            
            #****打印监控信息****
            print('processing report ' + str(count))
            #搜集报告子页面中的信息
            single_report_info = collect_info(rpt_html,full_rpt_url)
            info_list.append(single_report_info)
        #记录异常信息
        except:
            write2txt(count,pages,short_rpt_url)
        count += 1
    pass
	
def collect_report_url(html):
#功能：从报告列表页中搜集每个报告详细页面的url。
    report_url_list = []
    soup = bs4.BeautifulSoup(html,"html.parser")
    #****打印监控信息****
    print("Collecting reports' href...")
    for project in soup.find_all('td'):
        #部分‘a’标签为无效信息，选有用信息取href
        if (project.find('a')):
            report_url_list.append(project.find('a').get('href'))
    #最后一项为无效信息，删除
    del report_url_list[-1]
    return report_url_list
     
def collect_info(html,url):
#功能：从每个报告子页面中搜集其详细信息。
    soup = bs4.BeautifulSoup(html,'html.parser')
    #project id 项目编号
    p_id = soup.find(id="lb_GCBH").get_text()
    #report id 报告编号
    r_id = soup.find(id="lb_SQBH").get_text()
    #project name 项目名称
    name = soup.find(id="lb_GCMC").get_text()
    #construct company 建设单位
    c_cmpy = soup.find(id="lb_SJDW").get_text()
    #address 项目地址
    addr = soup.find(id="lb_DWDZ").get_text()
    #detect company 检测单位
    d_cmpy = soup.find(id="lb_DWMC").get_text()
    #report result 检测结论
    result = soup.find(id="lb_JCJL").get_text()
    #completed time 完成日期
    time = soup.find(id="lb_WCRQ").get_text()
    #form info list
    info_list = [p_id,r_id,name,c_cmpy,addr,d_cmpy,result,time,url]
    return info_list

def write2txt(report_count,page,url):
#功能：将异常信息写入txt文件。
    f = codecs.open('Error_info.txt','a','utf-8')
    f.write('The {} report in page {} failed.Its url is {}'.format(report_count,page,url) + '\r\n')
    f.close()

def write_to_csv(list,create_switch=False):
#功能：将报告信息写入csv，由开关控制是否需要生成新文件
#关联函数：create_csv(),add_to_csv()
    if create_switch:
        #表头信息
        head =  ['项目编号','报告编号','项目名称','委托单位(建设单位)','单位地址','检测单位','检测结论','完成日期','页面链接']   
        create_csv(head)
        print('cvs created')		
    add_to_csv(list)
    print('cvs added')
  
def create_csv(list):
#功能：生成存放报告的csv文件
    with codecs.open("raw_report_info_test.csv","w","utf_8_sig") as datacsv:
        csvwriter = csv.writer(datacsv,dialect=("excel"))
        csvwriter.writerow(list)

def add_to_csv(list):
#功能：将搜集到的报告信息写入csv格式
    with codecs.open("raw_report_info.csv","a","utf_8_sig") as datacsv:
        csvwriter = csv.writer(datacsv,dialect=("excel"))
        for index in range(len(list)):
            csvwriter.writerow(list[index])
	
#----运行主函数----
 
#--起始主页--
fornt_html = get_html(main_url)
#****打印监控信息****
print('front page html got')
print('----------------------------------------')
#--从起始主页获取第一次跳转所需信息--
vs,ev = collect_post_info(fornt_html)
#****打印监控信息****
print('first vs&ev updated')
print('----------------------------------------')
#--在起始页和终止页间搜集信息--
for pages in range(page_start,page_end+1):
    #****打印监控信息****
    print('process page {}...'.format(pages))
    #--页面跳转--
    cur_page_html = go_to_page(main_url,vs,ev,pages)
    #****打印监控信息****
    print('current page html updated')
    #--更新信息搜集表--
    report_info = []
    #****打印监控信息****
    print('info collect list updated')
    #--页面信息搜集--
    collect_info_in_page(cur_page_html,report_info,pages)
    #****打印监控信息****
    print('information in current page all collected')
    #--搜集信息的写入--
    write_to_csv(report_info,create_switch)
    #****打印监控信息****
    print('writen to csv')
    print('-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-')
    #--准备下次跳转
    vs,ev = collect_post_info(cur_page_html)
    #****打印监控信息****
    print('current page vs&ev updated')
print('----------------------------------------')
if create_switch:
    expect_report_num = (page_end - page_start + 1) * 20
    print('Expect {} report information in csv file.'.format(expect_report_num))
else:
    expect_report_num = (page_end - page_start + 1) * 20 + 20
    print('Expect {} report information in csv file.'.format(expect_report_num))
#****打印监控信息****
print('OK!')


