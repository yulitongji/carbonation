# -*- coding: utf-8 -*-
'''
Sript for both CH and CSH systems
'''

#%% PYTHON MODULES
from __future__ import division  #using floating everywhere
import sys,os
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(src_dir)
import matplotlib.pylab as plt
import numpy as np
np.set_printoptions(precision=5, threshold=np.inf)
import time
import yantra
import cell_type as ct # change the path to cell_type file
import misc_func as fn
import rt 
import mass_balance as mb
#import phrqc
#%% PROBLEM DEFINITION
__doc__= """ 
Carbonation of cement. 
Portlandite only.

"""
#problem type
m = 'CH' #or 'CSH'

#%% GEOMETRY
ll = 1
l = 25 + ll
lx = l*1.0e-6
ly = 2.0e-6
dx = 1.0e-6
rad = 6*dx
#wall_len_y = wall_len_x 

domain = yantra.Domain2D(corner=(0, 0), 
                         lengths=(lx, ly), 
                         dx=dx, 
                         grid_type='nodal')
domain.nodetype[:, (1+ll):(l+ll)] = ct.Type.MULTILEVEL

domain.nodetype[0,:] = ct.Type.SOLID
domain.nodetype[-1,:] = ct.Type.SOLID
domain.nodetype[:,-1] = ct.Type.SOLID

plt.figure(figsize=(5,5))
plt.imshow(domain.nodetype) 
plt.show()
#%%  VALUES
scale = 50
init_porosCH = 0.05
nn='example_13'
#fn.make_output_dir(root_dir+'\\results\\output\\simulations\\')
path = root_dir+'\\results\\output\\' + nn
fn.make_output_dir(path)

phrqc_input = {'c_bc':{'type':'pco2', 'value': 3.4}, #3.05E-02, 3.74E-02, 4.30E-02
               'c_mlvl':{'type':'eq', 'value': 'calcite'}, 
               'c_liq':{'type':'eq', 'value': 'calcite'},
               'ca_mlvl':{'type':'eq', 'value': 'portlandite'}, 
               'ca_liq':{'type':'eq', 'value': 'calcite'}}#calcite
phrqc = fn.set_phrqc_input(phrqc_input)            
fn.save_phrqc_input(phrqc,root_dir, nn)   

tfact =  1./6.
default_porosCH = 0.05

mvol_ratio = 3.69/3.31
mvolCH = 0.0331*scale * (1-init_porosCH) / (1-default_porosCH)
mvol = [mvolCH, mvolCH*mvol_ratio]
mvol = fn.set_mvols(mvol, ptype = m) #m3/mol
max_pqty = fn.get_max_pqty(mvol) #mol/m3
init_conc = fn.set_init_pqty(mvol, init_porosCH)
pqty = fn.get_pqty(init_conc, domain)

slabels = fn.set_labels(domain, m)          
D = 1.0e-09 # default diffusion coefficient in pure liquid
porosity = fn.get_porosity(domain, pqty, mvol, m)
app_tort = 1. * porosity ** (1./3.)

settings = {'precipitation': 'interface', # 'interface'/'all'/'mineral' nodes
            'active': 'all', # 'all'/'smart'/'interface'
            'diffusivity':{'type':'cc_archie', #'fixed' or 'archie'
                           'D_CC': 3e-12,
                           'D_CH': 1e-10},
            'pcs': {'pcs': True, 
                    'pores': 'block', #'block'/'cylinder'
                    'int_energy': 0.5, # internal energy
                    'pore_size': 0.01*dx, # threshold radius or distance/2
                    'crystal_size': 0.5*dx, # crystal or pore length
                    'pore_density': 20000, #pore density per um3 - only for cylinder type
                    }, 
           'velocity': False, 
           'bc': phrqc_input['c_bc'],
           'dx': dx 
           }
               

#%% PARAMETERS (DOMAIN, BC, SOLVER)
domain_params = fn.set_domain_params(D, mvol, pqty, porosity, app_tort, slabels,
                                     input_file = root_dir +'\\phreeqc_input\\' + nn + '.phrq')#'CH_CC-1percent.phrq'
                                     #input_file = 'CH_CC_-2.phrq')
bc_params = fn.set_bc_params(bc_slabels = {'left':100001})
solver_params = fn.set_solver_params(tfact = tfact)
domain.nodetype[domain.nodetype == ct.Type.MULTILEVEL_CH] = ct.Type.MULTILEVEL
fn.save_settings(settings, bc_params, solver_params, path, nn)

#%% INITIATE THE SOLVER
carb_rt= rt.CarbonationRT('MultilevelAdvectionDiffusion',  domain, domain_params, bc_params, solver_params, settings) 

#%% OUTPUT PARAMETERS
plist =  [(1,0), (1,1), (1,2), (1,3), (1,4), (1,5), (1,6), (1,7), (1,8)]#[(1,n) for n in np.array([1, 2, 3])] #v
#plist =  [(1,4), (1,5), (1,6), (1,7), (1,8), (1,9), (1,10), (1,11), (1,12)]
pavglist = ['avg_poros', 'avg_D_eff']
results = fn.init_results(pavg=True, pavg_list=pavglist, points=plist, ptype=m)

#%% TIME SETTINGS
itr = 0 
ni = 100
nitr = 2000
Ts = 0.01#51#1.001#1.01
step = 0.1
#time_points = np.arange(0, Ts+step, step)
time_points = np.concatenate((np.arange(0, step, step/10.), np.arange(step, Ts+step, step)))
it=time.time()

N = Ts/carb_rt.dt
N_res = 1e+4
S = max(1,int(N/N_res))
#%% RUN SOLVER
while itr < nitr: # carb_rt.time <=Ts: #
    carb_rt.advance()    
    results = fn.append_results(carb_rt, results, step=S)
    itr += 1
    
#%% SIMULATION TIME
simulation_time = time.time()-it
fn.print_time(simulation_time, carb_rt)

#%% PRINT
print(carb_rt.fluid.Ca.De[1,:])
print(carb_rt.solid.portlandite.c[1,:])
print(carb_rt.solid.calcite.c[1,:])
