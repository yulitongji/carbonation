# -*- coding: utf-8 -*-
'''
Sript for both CH and CSH systems
'''

#%% PYTHON MODULES
from __future__ import division  #using floating everywhere
import sys,os
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)
import matplotlib.pylab as plt
import numpy as np
import time
import copy
np.set_printoptions(precision=5, threshold=np.inf)

#%% CUSTOM MODULES
#sys.path.append('C:\\Users\\mat\\Documents\\Python_Projects\\yantra') # change the path
import yantra
import cell_type as ct # change the path to cell_type file
import func as fn
import classes as cl

#%% PROBLEM DEFINITION
__doc__= """ 
Carbonation of cement. 
Portlandite only.

"""
#problem type
m = 'CH' #or 'CSH'

#%% GEOMETRY
l = 25
lx = l*1.0e-6
ly = 2.0e-6
dx = 1.0e-6
rad = 6*dx
#wall_len_y = wall_len_x 

domain = yantra.Domain2D(corner=(0, 0), 
                         lengths=(lx, ly), 
                         dx=dx, 
                         grid_type='nodal')
domain.nodetype[:, 5:l] = ct.Type.MULTILEVEL

domain.nodetype[0,:] = ct.Type.SOLID
domain.nodetype[-1,:] = ct.Type.SOLID
domain.nodetype[:,-1] = ct.Type.SOLID

plt.figure(figsize=(5,5))
plt.imshow(domain.nodetype) 
plt.show()
#%%  VALUES

init_porosCH = 0.05

mvol_ratio = 3.69e-5/3.31e-5
mvolCH = 20
mvol = [mvolCH, mvolCH*mvol_ratio]

mvol = fn.set_mvols(mvol, ptype = m) #m3/mol
max_pqty = fn.get_max_pqty(mvol) #mol/m3
init_conc = fn.set_init_pqty(mvol, init_porosCH)
pqty = fn.get_pqty(init_conc, domain)

slabels = fn.set_labels(domain, m)          
D = 1.0e-09 # default diffusion coefficient in pure liquid
porosity = fn.get_porosity(domain, pqty, mvol, m)
app_tort = 1. * porosity ** (1./3.)

#%% PARAMETERS (DOMAIN, BC, SOLVER)

domain_params = fn.set_domain_params(D, mvol, pqty, porosity, app_tort, slabels,
                                     input_file = root_dir +'\\phreeqc_input\\CH_CC_nat.phrq')#'CH_CC-1percent.phrq'
                                     #input_file = 'CH_CC_-2.phrq')
bc_params={'solution_labels':{'left':100001}, 
           'top':['flux', 0.0],
           'bottom':['flux', 0.0],
           'left':['flux', 0.0],
           'right':['flux', 0.0],}

solver_params = fn.set_solver_params(tfact = 1./6.*2)

domain.nodetype[domain.nodetype == ct.Type.MULTILEVEL_CH] = ct.Type.MULTILEVEL

#%% INITIATE THE SOLVER

rt= cl.MyPhrqcReactiveTransport('MultilevelAdvectionDiffusion',  domain, domain_params, bc_params, solver_params) 
print(rt.solid.nodetype)
#fn.set_feq(rt)
#%% SETTINGS

nn='low_conc_order_2'#'acc10'
path = root_dir+'\\results\\output\\'
 
rt.settings = {'precip_mechanism': 'interface',#interface_dissolve_only' for all active cells or 'interface' 
               'diffusivity':{'type':'fixed', #'fixed' or 'archie
                              'calcite': 9e-12,
                              'portlandite': 1e-12},
               'si_params': {'N': 20000, #pore density per um3
                             'threshold': 'radius', #radius/porosity or si
                             'threshold_SI': 1.0, 
                             'threshold_distance':1e-3*dx, #maximum pore radius
                             'threshold_crystal':0.1*dx,
                             'L': 0.2*dx, #pore length
                             'mvol':3.69e-5,
                             'iene': 0.485, # internal energy
                             'R': 8.314, # gas constant
                             'T':298.3, # temperature in kelvin
                             'm':1,
                             'angle':1.0, #(angle in degrees / 180)
                             'dx':dx}, # +pore_factor?
               'velocity': False, #True #
               'pores': 'blocks' # 'cylinders or cubes
               
               }

fn.apply_settings(rt)
fn.save_settings(rt.settings, bc_params, solver_params, path, nn)

rt.solid._prev_vol = copy.deepcopy(rt.solid._vol)
rt.solid._dvol = rt.solid._vol-rt.solid._prev_vol

#%% PARAMETERS
plist =  [(1,2), (1,3), (1,4), (1,5), (1,6), (1,7), (1,8), (1,9), (1,10)]#[(1,n) for n in np.array([1, 2, 3])] #v
pavglist = ['avg_poros', 'avg_D_eff']
results = fn.init_results(pavg=True, pavg_list=pavglist, points=plist, ptype=m)
#%% TIME SETTINGS
itr = 0 
j = 0
ni = 100
nitr = 20
Ts = 1.0#10.001
step = 1.0
#time_points = np.arange(0, Ts+step, step)
time_points = np.concatenate((np.arange(0, step, step/10.), np.arange(step, Ts+step, step)))
it=time.time()

#%% RUN SOLVER

while rt.time <=Ts: #itr < nitr: # 
    if(False):
        if ( (rt.time <= time_points[j]) and ((rt.time + rt.dt) > time_points[j]) ):  
            print(time_points[j])
            #fn.save_figures_minerals(rt,  max_pqty, time_points[j], path, nn, ptype=m)  
            #save_figures_mols(rt, time_points[j], path, nn, ptype=m) 
            #save_vti(rt, phases, time_points[j], path, nn, m)
            #save_pickle(rt, phases, time_points[j], path, nn)
            if(j>0):
                points = [(1,n) for n in np.arange(1,15)]
                fn.print_points(rt, points, names=['calcite', 'portlandite'])
                print('SI %s' %rt.phrqc.selected_output()['SI_calcite'][1,:])
                print('C %s' %rt.fluid.C.c[1,:])
                print('Ca %s' %rt.fluid.Ca.c[1,:])
            j +=1
        
    rt.advance()    
    results = fn.append_results(rt, results)
    itr += 1
#%% SIMULATION TIME

simulation_time = time.time()-it
fn.print_time(simulation_time, rt)
            
#%%  SAVE

fresults  = fn.filter_results(results, path, nn)
#fn.save_obj(fresults, path + str(nn) +'_results')
#%% PLOT 
fn.plot_species(results, names=[])#['calcite']
fn.plot_avg(results, names=['avg_poros', 'avg_D_eff'])
fn.plot_points(results, names=['calcite', 'portlandite', 'poros', 'Ca', 'C'])
fn.plot_fields(rt, names=['calcite', 'Ca', 'poros'],fsize=(15,1))

#%% PRINT
points = [(1,n) for n in np.arange(2,15)]
#fn.print_points(rt, points)