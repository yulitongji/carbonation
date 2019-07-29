# -*- coding: utf-8 -*-
'''
Test the case with pores treated as blocks
'''
#python -m unittest discover -s test run all tests
from __future__ import division  #using floating everywhere
import sys,os
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
import numpy as np
np.set_printoptions(precision=5, threshold=np.inf)
import yantra
import src.cell_type as ct # change the path to cell_type file
import src.misc_func as fn
import src.rt  as rt
import unittest

class TestSum(unittest.TestCase):
    def test_run(self):
        """
        Test that it can run
        """
        m = 'CH' #or 'CSH'
        l = 25
        lx = l*1.0e-6
        ly = 2.0e-6
        dx = 1.0e-6
        #wall_len_y = wall_len_x 
        
        domain = yantra.Domain2D(corner=(0, 0), 
                                 lengths=(lx, ly), 
                                 dx=dx, 
                                 grid_type='nodal')
        domain.nodetype[:, 5:l] = ct.Type.MULTILEVEL
        
        domain.nodetype[0,:] = ct.Type.SOLID
        domain.nodetype[-1,:] = ct.Type.SOLID
        domain.nodetype[:,-1] = ct.Type.SOLID
        
        init_porosCH = 0.05

        mvol_ratio = 3.69e-5/3.31e-5
        mvolCH = 20
        mvol = [mvolCH, mvolCH*mvol_ratio]        
        mvol = fn.set_mvols(mvol, ptype = m) #m3/mol
        #max_pqty = fn.get_max_pqty(mvol) #mol/m3
        init_conc = fn.set_init_pqty(mvol, init_porosCH)
        pqty = fn.get_pqty(init_conc, domain)
        
        slabels = fn.set_labels(domain, m)          
        D = 1.0e-09 # default diffusion coefficient in pure liquid
        porosity = fn.get_porosity(domain, pqty, mvol, m)
        app_tort = 1. * porosity ** (1./3.)
        
        tfact =  1./6.*2  
                    
        domain_params = fn.set_domain_params(D, mvol, pqty, porosity, app_tort, slabels,
                                     input_file = root_dir +'\\phreeqc_input\\CH_CC_nat.phrq')#'CH_CC-1percent.phrq'
                                     #input_file = 'CH_CC_-2.phrq')
        bc_params={'solution_labels':{'left':100001}, 
                   'top':['flux', 0.0],
                   'bottom':['flux', 0.0],
                   'left':['flux', 0.0],
                   'right':['flux', 0.0],}
        
        solver_params = fn.set_solver_params(tfact = tfact)
        
        settings = {'precipitation': 'interface', # 'interface'/'all'/'mineral' nodes
                    'active': 'smart', # 'all'/'smart'/'interface'
                    'diffusivity':{'type':'fixed', #'fixed' or 'archie'
                                   'D_CC': 9e-12,
                                   'D_CH': 1e-12},
                    'pcs': {'pcs': True, 
                            'pores': 'block', #'block'/'cylinder'
                            'int_energy': 0.485, # internal energy
                            'pore_size': 0.01*dx, # threshold radius or distance/2
                            'crystal_size': 0.5*dx, # crystal or pore length
                            'pore_density': 20000, #pore density per um3 - only for cylinder type
                            #'threshold': 'poresize', #poresize/porosity or si
                            #'threshold_value': 1.0, 
                            }, 
                   'velocity': False, 
                   #'bc': 'const',
                   'dx': dx 
                   }    
            
        carb_rt= rt.CarbonationRT('MultilevelAdvectionDiffusion',  domain, domain_params, bc_params, solver_params) 
        carb_rt.settings = settings
        fn.apply_settings(carb_rt)
        itr = 0 
        nitr = 10
        while itr < nitr:     
            carb_rt.advance()    
            itr += 1
            
        self.assertEqual(carb_rt.iters, nitr)

if __name__ == '__main__':
    unittest.main()
