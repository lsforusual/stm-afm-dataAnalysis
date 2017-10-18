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

D0 = {'MIN': 10.0, # 末端distance区间
      'MAX': 20.0
     }
F0 = {'MIN':10.0,
      'MAX':12.5
      }




VERSIONS = "0.0.1 beta"


def getData(filename,mode='single',delimiter='tab'):
    import numpy as np
    if mode == 'single':
        # 读取数据，根据经验，单条力曲线的skiprows=166
        distance,force = np.loadtxt(filename,skiprows=SKIPROWS,\
                                    usecols=(COL_DISTANCE,COL_FORCE),delimiter=DATAFORMAT[delimiter]).T
    
    return distance,force  


def getApproach(distance,force):
    approach = {'distance':distance[:len(distance)//2],
                'force':force[:len(force)//2]}
    
    return approach                           


def unit_m2nm(distance):
    distance *= 1e9
    
    return distance


def getSnap(approach,f0):
    # 这里的数据是倒序的，所以range从1开始，但是，作为index需要是i-1
    # 从力曲线数据中提取出扎入层状结构snap的数据
    # snap 的数据格式是x升序的，原来的格式是x逆序
    snap = {'distance':[],
            'force':[],
            'index':[]}
    for i in range(1,len(approach['force'])):
        if approach['force'][-i]>f0:
            snap['distance'].append(approach['distance'][-i])
            snap['force'].append(approach['force'][-i])
            snap['index'].append(i)
    
    return snap
    

def getPeakByLNR(snap,stepLength=11):
    import numpy as np
    from scipy import stats
    st = {'r2':[],'index':[]}
    peak = 1
    # 用线性回归的方法计算寻找峰值,假定，当deltRsquare>0.2时，线性发生畸变
    for i in range(stepLength,len(snap['distance'])-stepLength):
        # 返回值是r**2
        st['r2'].append((stats.linregress(snap['distance'][i-stepLength:i+stepLength], \
                          snap['force'][i-stepLength:i+stepLength])[2])**2)
        st['index'].append(snap['distance'][i])
        # 先赋值，防止出错
        peak = i
        if len(st['r2'])>3 and np.abs(st['r2'][-2] - st['r2'][-3])>0.2:
            break
 
    return int(peak)


def getIntersectionByR2(snap,f0,stepLength=11):
    import numpy as np
    from scipy import stats
    # 用线性回归的方法计算寻找峰值,假定，当deltRsquare>0.2时，线性发生畸变
    
    stepPos = getPeakByLNR(snap,stepLength)
    # 根据峰值选取拟合的数据范围，
    # 为了防止峰值位置越界，后退10个数据点，如果数据少于30点，则不选用默认范围为线性区间
    stepPos = stepPos > 30 and stepPos-10 or stepPos
#    print(peak)
    slope,intercept = stats.linregress(np.array(snap['distance'][:stepPos])\
                                           ,np.array(snap['force'][:stepPos]))[:2]
    
    # 数据转换需要传入的参数为 forceConstant，intersection point，和线性区的斜率abs(k)
    # force=f0 and force=slope*distance+fy的交点为((f0-fy)/k,f0)
    intersection = {}
    intersection['x'] = (f0-intercept)/slope
    intersection['y'] = f0
    
    return intersection,slope

def getDefSensByR2(snap,stepLength=11):
    import numpy as np
    from scipy import stats
    # 用线性回归的方法计算寻找峰值,假定，当deltRsquare>0.2时，线性发生畸变
    
    stepPos = getPeakByLNR(snap,stepLength)
    # 根据峰值选取拟合的数据范围，
    # 为了防止峰值位置越界，后退10个数据点，如果数据少于30点，则不选用默认范围为线性区间
    stepPos = stepPos > 30 and stepPos-10 or stepPos
#    print(peak)
    slope  = stats.linregress(np.array(snap['distance'][:stepPos])\
                                           ,np.array(snap['force'][:stepPos]))[0]
    
    return 1./float(slope)

def getDefSensByFixedLength(snap,length = 50):
    import numpy as np
    from scipy import stats
    # 固定步长的方式计算Slope & intercept
    slope = stats.linregress(np.array(snap['distance'][:length:2])\
                                           ,np.array(snap['force'][:length:2]))[0]
    
    return 1./float(slope)
    
    

def getIntersectionByDefSens(snap,f0,DefSens):
    import numpy as np
    # 另一种矫正方式时采用Deflenction Sensitive直接进行校正，这种情况适用于噪音比较大的时候
    slope =- np.abs(1./DefSens)
    _f0 = np.mean(snap['force'][:50])
    _d0 = np.mean(snap['distance'][:50])
    # force=f0 and force=slope*(distance-_d0)+_f0的交点为((f0-_f0)/slope+_d0,f0)
    intersection = {}
    intersection['x'] = (f0-_f0)/slope +_d0
    intersection['y'] = f0

    return intersection,slope

def convert2ForceSeparation(approach,intersection,slope,forceConstant): 
    import numpy as np
    # 转换核心 copyright at Mao's Group，XMU
    approach['distance'] = approach['distance'] - intersection['x'] \
    -(approach['force']-intersection['y'])/np.abs(slope)
    approach['force'] = forceConstant*(approach['force']-intersection['y'])/np.abs(slope)
    
    return approach
     

def dataWashing(approach):
    import numpy as np
    # 数据清洗
    # 主要清洗异常的基线点
    f0 = []
    d0 = []
    
    # 获取基线数据
    for _d,_f in zip(approach['distance'],approach['force']):
        if _d > 10.0:
            f0.append(_f)
            d0.append(_d) 
    # 移除异常点
    # 异常点的判定方法：2 * sigma .= 0.95 
    # 用全部基线的mean 和std应该可以较好的排除异常点较多的情况(还是不行)
    fsigma = np.std(f0)
    fmean = np.mean(f0)
   
    for _f,_d in zip(f0,d0):
        if np.abs(_f - fmean) > 2.0*fsigma:
             f0.remove(_f)
             d0.remove(_d)
#         进一步缩小到（10.0，20。0）
        
#    f0[:] = [_f for _f,_d in zip(f0,d0) if _d<20.0 and np.abs(_f-fmean) < 2.0]
#            
#    
#    approach['force'] -= np.mean(f0)
#    
    return approach



def correct2Zero(approach,D0,F0):
    import numpy as np
    # 先清洗数据
    approach = dataWashing(approach)
    # 矫正回零点,此时的f0已经不是原来的f0,故需从新计算矫正
    # 此时可以得到较好的转换曲线
    # 在基线不漂移的情况下，这样做没什么问题，但是仍然不能保证零点位置
    # 最好的放法还是要先求出零点（台阶）位置，然后根据台阶位置计算
    # 这样distance在数据不是很好的时候不能很好的矫正到零点
    # approach['distance'] -= np.mean(approach['distance'][-peak:-5])
    d0 = []
    f_max = np.max(approach['force']) > F0['MAX'] and F0['MAX'] or np.max(approach['force'])
    f_min = np.max(approach['force']) < F0['MIN'] and f_max-0.3 or F0['MIN']
    [d0.append(_d) for _d,_f in zip(approach['distance'],approach['force']) if f_min<_f<f_max]
    approach['distance'] -= np.mean(d0)
    
    # 进一步的矫正f*0.800,区距离在20.0 ～30.0 之间的基线
    f0 = []
    d_max = np.max(approach['distance']) > D0['MAX'] and D0['MAX'] or np.max(approach['distance'])
    d_min = 10.0 
    f0[:] =  [_f for _d,_f in zip(approach['distance'],approach['force']) if d_min<_d<d_max]
    approach['force'] -= np.mean(f0)
    return approach


def DefSensAnalysis(folder):
    import os
    import numpy as np
    from scipy import stats
    if not os.path.isdir(folder):
        print('%s MUST BE a folder!'%folder)
        return
    
    DefSenses = []
    sys.stdout.write("#"*int(82)+'|')
    j=0
    
    for file in os.listdir(folder):
        _f = os.path.join(folder,file)
        
        if not _f.endswith('.txt') or os.path.isdir(_f):
            continue
#        print(_f)
        distance,force = getData(_f)
        # 把所有数据矫正到第一象限
        force -= min(force)
        distance -= min(distance)
        # 把距离转换为nm
        distance = unit_m2nm(distance)
        approach = getApproach(distance,force)
    
    #    f0 = stats.linregress(distance[55:105],force[55:105])[1]
        f0 = np.mean(force[55:105])
        snap = getSnap(approach,f0)
            
        stepPos = getPeakByLNR(snap)
#        print(stepPos)
        # 根据峰值选取拟合的数据范围，
        # 为了防止峰值位置越界，后退10个数据点，如果数据少于30点，则不选用默认范围为线性区间
        stepPos = stepPos > 30 and stepPos-10 or stepPos
    #    print(peak)
        slope = stats.linregress(np.array(snap['distance'][:stepPos])\
                                               ,np.array(snap['force'][:stepPos]))[0]
        
        DefSenses.append(np.abs(1./slope))
        
        j+=1
        sys.stdout.write('\r'+(j*80//len(os.listdir(filename)))*'-'+'-->|'+"\b"*3)
        sys.stdout.flush()
        
    
    storePath = os.path.join(folder,'result')
#    print(folder)
#    print(storePath)
    if not os.path.exists(storePath):
        os.mkdir(storePath)
        
    storeFilename = os.path.join(storePath , 'DefSenses.txt')
        
    with open(storeFilename,'w') as f:
        print('DefSens',file=f)
        for _df in DefSenses:
            print('%.13f'%_df,file=f)
            
            
    # 对数据进行清理，避免出现outlier
    DefSens_mean = np.mean(np.array(DefSenses))
    DefSens_std = np.std(np.array(DefSenses))
#    for _df in DefSenses:
#        if np.abs(_df-DefSens_mean) > 1.0*DefSens_std:
#            DefSenses.remove(_df)
    DefSenses[:] = [_df for _df in DefSenses if np.abs(_df-DefSens_mean) < 2.0*DefSens_std]
            
    DefSens_mean = np.mean(np.array(DefSenses))
    DefSens_std = np.std(np.array(DefSenses))
    
    
    
    return DefSens_mean,DefSens_std



def afmForceCurce(filename,mode,forceConstant,DefSens_mean=-1,DefSens_std=-1,method = 'FixedLength',stepLength=7):
    import os
    import numpy as np
    import matplotlib.pyplot as plt
    
    method = method.lower()

    distance,force = getData(filename,mode)
    # 把所有数据矫正到第一象限
    force -= min(force)
    distance -= min(distance)
    # 把距离转换为nm
    distance = unit_m2nm(distance)
    approach = getApproach(distance,force)

#    f0 = stats.linregress(distance[55:105],force[55:105])[1]
    f0 = np.mean(force[55:105])
    snap = getSnap(approach,f0)
  
#    intersection,slope = getIntersectionByR2(snap,f0,stepLength=21)
    if method == 'r2': 
        DefSens = getDefSensByR2(snap,stepLength=stepLength)
    else:
        # 
        DefSens = getDefSensByFixedLength(snap,length=50)

#    if DefSens_mean != DefSens_std and np.abs(DefSens_mean - DefSens) > 3.0 * DefSens_std:
#        # 如果用默认的DefSens会造成一部分曲线偏些
#        DefSens = DefSens_mean



    intersection,slope = getIntersectionByDefSens(snap,f0,DefSens)
    
    approach = convert2ForceSeparation(approach,intersection,slope,forceConstant)

    approach = correct2Zero(approach,D0,F0)



    

    # TODO:
    # 自动统计处层状结构的力值和距离
    # 初步的想法是：对数据进行histogram，然后统计零点出现的位置
#    d = [];f=[]
#    for _d,_f in zip(reversed(approach['distance']),reversed(approach['force'])):
#         if _d<10.0 and _f<5.0:
#             d.append(_d)
#             f.append(_f)
#             
#    stepsRange = []
#    h = np.histogram(d,bins=200)
#    for i in range(4,len(h[0][:])-4):
#        if h[0][i] != 0 and h[0][i-1]==0 and h[0][i-2]==0 and h[0][i-3]==0:
#            stepsRange.append([h[1][i],h[1][i+1]])
#            break
#            
#    
#    paras={'forces':[],
#               'separation':[]}
#    for _d,_f in zip(d,f) :
##        if len(stepsRange)>3:
##            for i in range(0,3):
##                if _d in stepsRange[i]:
##                    statParas['forces'].append(_f)
##                    statParas['separation'].append(_d)
##                    break
#        if stepsRange[0][0] < _d < stepsRange[0][1]:
#            paras['forces'].append(_f)
#            paras['separation'].append(_d)
#            break
#    
    
            
            
            
            
            
            
    # 文件的检查与处理
    storepath,originFilename = os.path.split(filename)
    
    storepath = os.path.join(storepath,'result')
    originFilename = originFilename[:-4] # 去掉'.txt'
#    print(storepath)

    if not os.path.exists(storepath):
        os.mkdir(storepath)
    if not os.path.exists(os.path.join(storepath,'transformed')):
        os.mkdir(os.path.join(storepath,'transformed'))
    
#    parasFilename = storepath + '/paras.txt'
#    
#    with open(parasFilename,'w') as f:
#        print('1st_Layer_Force \t 1st_Layer_Separation',file=f)
#        for _f,_s in zip(paras['forces'],paras['separation']):
#            print('%.13f \t %.13f'%(_f,_s),file=f)
            
#    np.savetxt(parasFilename,np.array([paras['forces'],paras['separation']]).T \
#                ,delimiter='\t',header='1st_Layer_Force \t 1st_Layer_Separation')
#    print(storepath)
    storeFilename = storepath +'/transformed/Tf_'+originFilename
    
    plt.close('all')
    plt.figure(1)
    plt.plot(approach['distance'],approach['force'],'.')
    plt.plot([0,0],[-1,6],'--')
    plt.plot([-1,20.0],[0,0],'--')
    plt.xlim([-1,15])
    plt.ylim([-0.5,6])
    plt.xlabel('Separation (nm)')
    plt.ylabel('Force (nN)')
    plt.savefig(storeFilename + '_fig.jpg')
#    print(approach)
#    np.savetxt(storeFilename,np.array([approach['distance'],approach['force']]).T\
#               ,delimiter='\t',header='distance\tforce')
    with open(storeFilename+'.txt','w') as f:
        print('Separation(nm) \t Force(nN)',file=f)
        for _d,_f in zip(approach['distance'],approach['force']):
            print('%.13f \t %.13f'%(_d,_f),file=f)
            
            
if __name__ == '__main__':

    import sys,os,getopt
    import configparser
    import pandas as pd
    import time
    startTime = time.clock()


    def usage():
        print('''
        args:
        
        -f finelame
        -v version
        -m mode
        
        
        ''')

    basePath = os.path.dirname(os.path.abspath(__file__))

    shortArgs = 'f:m:v:tfm'
    longArgs = ['file=', 
				'mode=', 
				'version',
				'noDSA',
				'onlyDSA','DSA'
				'tfMethod=',
				'stepLength=',
				'ForceConstant=']

    mode = 'single'
    filename = os.path.join(basePath,"Fc.txt")

    opts,args = getopt.getopt(sys.argv[1:],shortArgs,longArgs)

    transformMethod = 'FixedLength'

    # 读取配置文件
    confPath = os.path.join(basePath,'config.ini')
    if os.path.isfile(confPath):
        conf = configparser.ConfigParser()
        conf.read(confPath)
        filename = conf.get('Configs','File_Path')
        SKIPROWS = conf.getint('DataFormat','Skiprows')
        mode = conf.get('Configs','Mode')
        forceConst = conf.getfloat('Configs','ForceConstant')
        DELIMITER = str(conf.get('DataFormat','Delimiter')).lower()
        DefSens = conf.getfloat('Configs','Deflection_Sensitive')
        transformMethod = str(conf.get('Configs','Transform_Method')).lower()
        stepLength = int(conf.get('Configs','Step_Length'))
        print('read config.ini success!')
        # print(DATAFORMAT[DELIMITER])


    DSA = True
    onlyDSA = False
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
            elif opt in ('--noDSA'):
                DSA = False
            elif opt in ('--onlyDSA','--DSA'):
                onlyDSA = True
            elif opt in ('-tfm','--tfMethod='):
                transformMethod = str(val).lower()
            elif opt in ('--stepLength=','--steplength='):
                stepLength = int(val)
            elif opt in ('--ForceConstant='):
                forceConst = float(val)



#    判断力常数，如果为1.0则认为力常数未作修改，抛出警告
#    并且，力常数不能小于零
    if forceConst == 1.0:
        print('you MAY NOT set the proper ForceConstant, but the programme will keep going' )
    elif forceConst <0:
        print("ForceConstant < 0 ,it is illegal")
        sys.exit(3)
   

    if os.path.isfile(filename):
        print("data is file")
        if filename.endswith('.txt'):
            afmForceCurce(filename,mode,forceConst)

    elif os.path.isdir(filename):
        print("data is dir")
        
        if DSA:
            # 对力曲线进行预分析
            print("Analysing Deflection Sensitive...")
            DefSens_mean, DefSens_std= DefSensAnalysis(filename)
            times = time.clock()-startTime
            sys.stdout.write('\nDef Sens Analysis Completed, use time:%.2f s\n'%times)
            print("Get DefSens:%.3f +- %.3f"%(DefSens_mean,DefSens_std))
            
            if onlyDSA:
                sys.exit()
        else:
            DefSens_mean = -1
            DefSens_std = -1

        print("Now dealing...")
        sys.stdout.write("#"*int(80)+'|')
        j=0
        for file in os.listdir(filename):
            _filename = os.path.join(filename,file)
            if os.path.isfile(_filename):
#                print(_filename)
                if file.endswith('.txt'):
                    afmForceCurce(_filename,mode,forceConst,DefSens_mean,DefSens_std,method=transformMethod,stepLength=stepLength)
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
        

        times = time.clock() - startTime
        
        sys.stdout.write("\nFINISHED! at %s/result \n Times: %.2f s\n"%(filename,times))


    else:
        print("Parameter of programme error")
        sys.exit(2)



           
    

        
        
        
        
        
        
        
        
        
        
    
    
    
