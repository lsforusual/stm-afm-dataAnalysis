# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 09:20:36 2017

@author: jonah
"""
SKIPROWS = 166
DATAFORMAT = {"tab":'\t',
              "space":' ',
              "comma":','
              }
COL_FORCE = 2
COL_DISTANCE = 1
VERSIONS = "0.0.1 beta"



def afmForceCurce(filename,mode,forceConstant):
    import os
    import numpy as np
    from scipy import stats
 
    
    if mode =="single":
        # 读取数据，根据经验，单条力曲线的skiprows=166
        distance,force = np.loadtxt(filename,skiprows=SKIPROWS,\
                                    usecols=(COL_DISTANCE,COL_FORCE),delimiter=DATAFORMAT[DELIMITER]).T
    # 把所有数据矫正到第一象限
    force -= min(force)
    distance -= min(distance)
    # 把距离转换为nm
    distance *= 1e9
    approach = {'distance':distance[:len(distance)//2],
                                    'force':force[:len(force)//2]}
    
    if not len(force)==len(distance):
        print("data is error that len(force) != len(distance)")
        return


    # 这里的数据是倒序的，所以range从1开始，但是，作为index需要是i-1
    # 从力曲线数据中提取出扎入层状结构snap的数据
    # snap 的数据格式是x升序的，原来的格式是x逆序
    f0 = np.mean(force[5:55])
    snap = {'distance':[],
            'force':[],
            'index':[]}
    for i in range(1,len(approach['force'])):
        if approach['force'][-i]>f0:
            snap['distance'].append(approach['distance'][-i])
            snap['force'].append(approach['force'][-i])
            snap['index'].append(i)

    
    # 用线性回归的方法计算寻找峰值,假定，当deltRsquare>0.2时，线性发生畸变
    st = {'r2':[],'index':[]}
    peak = 1
    for i in range(5,len(snap['distance'])):
        # 返回值是r**2
        st['r2'].append((stats.linregress(snap['distance'][i-5:i+5],snap['force'][i-5:i+5])[2])**2)
        st['index'].append(snap['distance'][i])
        if len(st['r2'])>3:
            if (st['r2'][-2] - st['r2'][-3])>0.2:
                peak=i
                break
    
    # 根据峰值选取拟合的数据范围，
    # 为了防止峰值位置越界，后退10个数据点，如果数据少于30点，则不选用默认范围为线性区间
    # 
#    print(peak)


    peak = (peak>30 and peak-10 or peak)
    slope,intercept = stats.linregress(np.array(snap['distance'][:peak])\
                                           ,np.array(snap['force'][:peak]))[:2]
    
    # 数据转换需要传入的参数为 forceConstant，intersection point，和线性区的斜率abs(k)
    # force=f0 and force=slope*distance+fy的交点为((f0-fy)/k,f0)
    intersection = {}
    intersection['x'] = (f0-intercept)/slope
    intersection['y'] = f0
    
    # 转换核心 copyright at Mao's Group，XMU
    approach['distance'] = approach['distance'] - intersection['x'] \
    +(approach['force']-intersection['y'])/np.abs(slope)
    approach['force'] = forceConstant*(approach['force']-intersection['y'])/np.abs(slope)
        
    # 矫正回零点,此时的f0已经不是原来的f0,故需从新计算矫正
    # 此时可以得到较好的转换曲线
    approach['force'] -= min(approach['force'])
    approach['distance'] -= min(approach['distance'])  
    
    # TODO:
    # 自动统计处层状结构的力值和距离
    # 初步的想法是：对数据进行histogram，然后统计零点出现的位置
    
    storepath,originFilename = os.path.split(filename)
    storepath = os.path.join(storepath,'result')
#    print(storepath)

    if not os.path.exists(storepath):
        os.mkdir(storepath)
    if not os.path.exists(os.path.join(storepath,'transformed')):
        os.mkdir(os.path.join(storepath,'transformed'))
    
#    print(storepath)
    storeFilename = storepath +'\\transformed\\Tf_'+originFilename
#    print(approach)
    np.savetxt(storeFilename,np.array([approach['distance'],approach['force']]).T\
               ,delimiter='\t',header='distance\tforce')
            
            
if __name__ == '__main__':

    import sys,os,getopt
    import configparser
    import pandas as pd
    def usage():
        print('''
        args:
        
        -f finelame
        -v version
        -m mode
        
        
        ''')

    basePath = os.path.dirname(os.path.abspath(__file__))

    shortArgs = 'f:m:v'
    longArgs = ['file=', 'mode=', 'version']

    mode = 'single'
    filename = os.path.join(basePath,"Fc.txt")

    opts,args = getopt.getopt(sys.argv[1:],shortArgs,longArgs)


    # 读取配置文件
    confPath = os.path.join(basePath,'config.ini')
    if os.path.isfile(confPath):
        conf = configparser.ConfigParser()
        conf.read(confPath)
        filename = conf.get('Configs','File_Path')
        SKIPROWS = conf.getint('DataFormat','Skiprows')
        mode =conf.get('Configs','Mode')
        forceConst = conf.getfloat('Configs','ForceConstant')
        DELIMITER=str(conf.get('DataFormat','Delimiter')).lower()
        print('read config.ini success!')
        # print(DATAFORMAT[DELIMITER])



    if not len(opts) == 0:
        for opt, val in opts:
            if opt in ('-f', '--filename='):
                filename = val
            elif opt in ('-m', '--model='):
                modelName = val
                modelPath = os.path.join(basePath, 'Models/' + modelName + '.py')
                if not os.path.exists(modelPath):
                    print("model does not exit", file=sys.stdout)
                    sys.exit(2)
            elif opt in ('-v', '--version'):
                    print('VERSION %s'.format(VERSIONS))
                    usage()
                    sys.exit(2)



#    判断力常数，如果为1.0则认为力常数未作修改，抛出警告
#    并且，力常数不能小于零
    if forceConst == 1.0:
        print('you MAY NOT set the proper ForceConstant, but the programme will keep going' )
    elif forceConst <0:
        print("ForceConstant < 0 ,it is illegal")
        sys.exit(3)
   

    if os.path.isfile(filename):
        print("data is file")
        afmForceCurce(filename,mode,forceConst)

    elif os.path.isdir(filename):
        print("data is dir")
        print("Now dealing...")
        sys.stdout.write("#"*int(80)+'|')
        j=0
        for file in os.listdir(filename):
            _filename = os.path.join(filename,file)
            if os.path.isfile(_filename):
#                print(_filename)
                afmForceCurce(_filename,mode,forceConst)
                j+=1
                sys.stdout.write('\r'+(j*80//len(os.listdir(filename)))*'-'+'-->|'+"\b"*3)
                sys.stdout.flush()

        # 对参数文档进行分析
        # 这部分等TODO完善之后再进行uncomment
#        paraFile = os.path.join(filename,"result/paras.txt")
#        stat = pd.read_csv(paraFile,sep='\t',index_col=-1)
#        gp = stat.groupby('potential')
#        gpStat = gp.describe()
#        gpStat.to_csv(os.path.join(filename,"result/statstistic.txt"),sep='\t')
        
        sys.stdout.write("\nFINISHED! at %s\\result \n"%filename)
        
        

    else:
        print("Parameter of programme error")
        sys.exit(2)



           
    

        
        
        
        
        
        
        
        
        
        
    
    
    