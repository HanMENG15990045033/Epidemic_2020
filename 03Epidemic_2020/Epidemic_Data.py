#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb  2 19:00:58 2020

@author: bob
"""

import pandas as pd
import numpy as np
import requests
import folium
import webbrowser
from folium.plugins import HeatMap

def city(province):
    '''
    处理港澳地区无城市的情况
    province: 类型:字典型
    return:   包含以下内容的 list
    '''
    d = {}                                          #创建字典保存数据
    #d['province'] = province['provinceName']
    d['cityName'] = province['provinceName']        #获取省份名称
    d['confirmed'] = province['confirmedCount']     #确诊数
    d['suspected'] = province['suspectedCount']     #疑似数
    d['cured'] = province['curedCount']             #治愈数
    d['dead'] = province['deadCount']               #死亡数
    
    return list(d.values())                         #返回上述内容list

def requestData():
    '''
    获取最新疫情数据, 保存至当前目录为 日期.csv 文件
    return: 文件名(日期.csv)
    '''
    #数据更新网址
    url = 'http://tianqiapi.com/api?version=epidemic&appid=23035354&appsecret=8YvlPNrz'
    #返回 json 格式数据
    data = pd.read_json(url, orient='colums')
    
    #提取到总数据 待提取相关详细数据
    Epidemic_data = data['data'] 
    #数据日期
    Data_date = Epidemic_data['date'].split()[0]
    #columns = ['provinceName', 'cityName', 'confirmed', 'suspected', 'cured', 'dead']
    columns = ['cityName', 'confirmed', 'suspected', 'cured', 'dead']
    
    #创建全国疫情数据 DataFrame
    China_Data = pd.DataFrame(columns=['provinceName', 
                                       'cityName', 
                                       'confirmed', 
                                       'suspected', 
                                       'cured', 
                                       'dead'])
    #获取所有省份数据
    Country_Data = Epidemic_data['area']
    
    for province in Country_Data:                           #遍历每一个省份
        provinceName = province['preProvinceName']          #获取省份名称
        try:
            ProvinceData = province['cities']               #获取该省份下所有城市数据
            city_Data = []
            for province in ProvinceData:                   #遍历所有城市
                city_Data.append(list(province.values()))
            #构建 DataFrame 格式
            CityData = pd.DataFrame(np.array(city_Data), columns=columns)
            #新增省份列属性, 设置省份名称
            CityData['provinceName'] = provinceName
            #更新至总数据中
            China_Data = pd.concat([China_Data, CityData], ignore_index=True)
        except:#处理香港, 澳门等单一城市的数据 代码类似
            CityData = pd.DataFrame(np.array([city(province)]), columns=columns)
            CityData['provinceName'] = provinceName
            China_Data = pd.concat([China_Data, CityData], ignore_index=True)
            #print(CityData)
            #print(pd.DataFrame(np.array([city(province)]), columns=columns))
            #none_City.append(city(province))
    
    #将省份和城市作分级 保存 csv
    China_Data.set_index(['provinceName', 'cityName'], inplace=True)
    
    #保存文件名称以数据日期为准
    fileName = Data_date + '.csv'
    China_Data.to_csv(fileName)
    return fileName

def getCityLocation(cityList):
    '''
    用于获取城市经纬度
    cityList: 全国城市名称的 list
    return: 城市经纬度的 DataFrame
    '''
    url = "http://api.map.baidu.com/geocoder/v2/"
    header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36'}
    payload = {
        'output':'json',
        'ak':'X8zlxPUdSe2weshrZ1WqnWxb43cfBI2N'
        }
    addinfo = []
    for city in cityList:
        payload['address'] = city
        try:
            content =  requests.get(url,params=payload,headers=header).json()
            longitude = content['result']['location']['lng']
            latitude = content['result']['location']['lat']
            addinfo.append([city, longitude, latitude])
            #addinfo.append(content['result']['location'])
            print("正在获取{}的地址！".format(city))        
        except:
            print("地址{}获取失败，请稍后重试！".format(city))    
            pass
        #time.sleep(.1)
        
    columns = ['cityName', 'longitude', 'latitude']
    data = pd.DataFrame(np.array(addinfo), columns=columns)
    #print(data)
    print("所有地址均已获取完毕！！！")
    return(data)

def Visualization(UpdateData):
    latitude = np.array(UpdateData["latitude"])
    longitude = np.array(UpdateData["longitude"])
    confirmed = np.array(UpdateData["confirmed"],dtype=float)
    
    Vis_Data = [[latitude[i],longitude[i],confirmed[i]] for i in range(len(UpdateData))]
    
    map_osm = folium.Map(location=[30,114],zoom_start=10)
    HeatMap(Vis_Data).add_to(map_osm) 
    file_path = r"Visualization.html"
    map_osm.save(file_path)   #保存本地
    webbrowser.open(file_path) #在本地浏览器打开
    


fileName = requestData()                #获取当天数据 并返回文件名

data = pd.read_csv(fileName)            #读取原始数据
cityList = data['cityName'].tolist()    #获取所有城市列表
location = getCityLocation(cityList)    #获取城市经纬度
UpdateData = pd.merge(data, location,   #更新经纬度
                      on='cityName', 
                      how = 'left')

#保存可视化数据
#UpdateData.to_csv('Visualization_Data.csv')
VisualData = UpdateData.dropna()        #剔除缺失值 可视化数据

Visualization(VisualData)

