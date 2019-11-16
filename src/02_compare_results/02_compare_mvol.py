# -*- coding: utf-8 -*-
'''
Compare the results for different IE
'''
#%% MODULES
from __future__ import division  #using floating everywhere
import sys,os
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(src_dir)
import matplotlib.pylab as plt
import numpy as np
np.set_printoptions(precision=5, threshold=np.inf)
import misc_func as fn
import func as cf
#%% SETTINGS
Ts =1000.
fname = 'compare_mvol'
fpath = root_dir+'\\results\\output\\02_molar_volume\\'
fn.make_output_dir(fpath)
names = np.array([#'01_mvol1_subgrid',
                  '02_mvol5_subgrid',
                  '03_mvol10_subgrid', 
                  '04_mvol50_subgrid', 
                  '05_mvol100_subgrid', 
                   ])
label = np.array([# '1', 
                  '5', '10', '50', '100'])
linetype = np.array(['-', '--', '-.', ':', '-'])

results = {}
for nn in names:
    path = root_dir+'\\results\\output\\02_molar_volume\\' + nn + '\\'
    results[nn] = fn.load_obj(path + nn +'_results')

#%% SCALE
scale = [5., 10, 50, 100]
#dtime = [350,350,350,350,200,0]
keys = ['portlandite', 'calcite', 'Ca', 'C', 'pH', 'time',
        'C (1, 0)', 'C (1, 1)', 'avg_poros', 
        'portlandite_cells', 'calcite_cells',
        'vol_CH (1, 1)', 'vol_CH (1, 2)', 'vol_CH (1, 3)',
        'vol_CC (1, 1)', 'vol_CC (1, 2)', 'Ca (1, 1)']
sres = {}
for i in range(0, len(names)):
    temp = {}
    a =np.array(results[names[i]]['time']) <= Ts/scale[i]
    s = np.size(results[names[i]]['time'])
    for k in keys:
        if(np.size(results[names[i]][k])==s):
            temp[k] = np.array(results[names[i]][k])[a]
    temp['time'] *= scale[i] 
    #temp['time']+=dtime[i]
    temp['portlandite'] *=scale[i]
    temp['calcite'] *=scale[i]
    sres[names[i]] = temp
#%%   
    '''
plt.figure(figsize=(8,4))
for i in range(0, len(names)):
    plt.plot(sres[names[i]]['time'], sres[names[i]]['Ca (1, 1)'],
             ls=linetype[i], label = label[i])
plt.legend()
plt.show() 

plt.figure(figsize=(8,4))
for i in range(0, len(names)):
    plt.plot(sres[names[i]]['time'], sres[names[i]]['C (1, 1)'],
             ls=linetype[i], label = label[i])
plt.legend()
plt.show() 


plt.figure(figsize=(8,4))
for i in range(0, len(names)):
    plt.plot(sres[names[i]]['time'], sres[names[i]]['vol_CH (1, 1)'],
             ls=linetype[i], label = label[i])
plt.legend()
plt.show() 
plt.figure(figsize=(8,4))
for i in range(0, len(names)):
    plt.plot(sres[names[i]]['time'], sres[names[i]]['vol_CC (1, 1)'],
             ls=linetype[i], label = label[i])
plt.legend()
plt.show()
''' 
#%% CH DISSOLUTION 
titles = ['Portlandite', 'Calcite', 'Calcium', 'Carbon',
          'Average pH', 'Input C', 'Porosity']
comp =  ['portlandite', 'calcite', 'Ca', 'C', 'pH', 
         'C (1, 0)', 'avg_poros']
suffix = ['_portlandite', '_calcite', '_calcium', '_carbon',
          '_average ph', '_input_c', '_poros']
for k in range(0, len(comp)):
    plt.figure(figsize=(8,4))
    for i in range(0, len(names)):
        plt.plot(sres[names[i]]['time'], sres[names[i]][comp[k]],
                 ls=linetype[i], label = label[i])
    plt.title(titles[k])
    plt.xlabel('Time (s)')
    plt.legend()
    plt.savefig(fpath + fname + suffix[k])
    plt.show() 

#%% DISSOLUTION RATE

titles = ['Dissolution rate', 'Precipitation rate' ]
comp =  ['portlandite', 'calcite']
suffix = ['_CH_rate', '_CC_rate' ]
for k in range(0, len(comp)):
    plt.figure(figsize=(8,4))
    for i in range(0, len(names)):
        plt.plot(sres[names[i]]['time'], 
                 cf.get_rate(sres[names[i]][comp[k]],
                             sres[names[i]]['time'][2] - sres[names[i]]['time'][1]),
                 ls=linetype[i], label = label[i])
    plt.title(titles[k])
    plt.xlabel('Time (s)')
    plt.ylabel('Rate (mol/s)')
    plt.legend()
    plt.savefig(fpath + fname + suffix[k])
    plt.show()
#plt.savefig(fpath + fname + '_CH_rate')

#%% INTERPOLATION
from scipy.interpolate import interp1d
name = '02_mvol5_subgrid'
t = {}
p = {}
for n in names:
    t[n] = sres[n]['time']
    p[n] = sres[n]['portlandite']
f = interp1d(t[name], p[name], kind = 'cubic', fill_value="extrapolate")
pi = {}
diff = {}
for i in range(0, len(names)-1):
    pi[names[i]] = f(t[names[i]])
    diff[names[i]] = np.abs(p[names[i]] - pi[names[i]])

#%% ERROR NORM
def l2_norm(v, o):
    '''
    v - vector
    o - original solution vector
    '''
    return np.sqrt(np.sum((v - o)**2)/ np.sum(o**2))

s = []
npnorm = []
l2norm = []
for i in range(0, len(names)-1):
    #print('Scale %s' %scale[i])
    s.append(scale[i])
    npnorm.append(np.linalg.norm(diff[names[i]], ord = 1))
    l2norm.append(l2_norm(p[names[i]], pi[names[i]]))
#%% PLOT NORM
plt.figure(figsize=(8,4))
plt.plot(s, npnorm)
plt.title('L2 norm')
plt.xlabel('Scale')
plt.ylabel('Numpy L2 norm')
plt.savefig(fpath + fname + '_np_l2_norm')
plt.show()

plt.figure(figsize=(8,4))
plt.plot(s, l2norm)
plt.title('Relative error')
plt.xlabel('Scale')
plt.ylabel('Relative error')
plt.savefig(fpath + fname + '_rel_error')
plt.show()

#%%
k = 'calcite'# 'avg_poros' #'portlandite''calcite'
er = np.array([])
for nn in names:
    d_ch = sres[nn][k][0]- sres[nn][k][-2]
    er = np.append(er, d_ch)
print(er)
for i in range(0,len(er)):
    e = (er[i]-er[-1])/er[-1] * 100    
    print('%s, %s ' %(names[i], str(e)))
    
 
#%% 
for nn in names:
    ch24 = np.array(sres[nn]['portlandite_cells'])==24
    ch23 = np.array(sres[nn]['portlandite_cells'])==23
    cross = np.roll(ch24,-1) + ch23
    t = np.array(sres[nn]['time'])[~cross]
    print(t)
    
#%%
    
titles = ['Volume CH in (1,1)', 'Volume CH in (1,2)', 'Volume CH in (1,3)']
comp =  ['vol_CH (1, 1)', 'vol_CH (1, 2)', 'vol_CH (1, 3)']
for k in range(0, len(comp)):
    plt.figure(figsize=(8,4))
    for i in range(0, len(names)):
        plt.plot(sres[names[i]]['time'], sres[names[i]][comp[k]],
                 ls=linetype[i], label = label[i])
    plt.title(titles[k])
    plt.xlabel('Time (s)')
    plt.legend()
    plt.show() 
