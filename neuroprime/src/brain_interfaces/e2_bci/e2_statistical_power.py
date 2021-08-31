#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 16:04:40 2019


#Script to emulate R Power Analysis


To calculate the required sample size, you’ll need to know four things:

The size of the response you want to detect: 
    DELTA, Δ, (abs(mean_eg-mean_cg)):
        From E1:
            min(mean_%tBAT_eg-mean_%tBAT_cg)=2%, max(mean_%tBAT_eg-mean_%tBAT_cg)=10%, so 2% is more a less the size

The variance of the response:
    From E1 or current E2:
        variance, σ=numpy.var()calculate for %tBAT

The desired significance level: 95%=1 – α, where α=0.05 is the probability of making a Type 1 Error.
The desired power: 0.8

The effect size:
    combines the minimal relevant difference and the variability into one measurement, Δ/σ.




#R code:
    #see https://stat.ethz.ch/R-manual/R-patched/library/stats/html/power.prop.test.html
    power.prop.test(p1 = .33, p2 = .67, power = .80)
    
    result:
        Two-sample comparison of proportions power calculation 

              n = 32.74418
             p1 = 0.33
             p2 = 0.67
      sig.level = 0.05
          power = 0.8
    alternative = two.sided

    NOTE: n is number in *each* group
    
    #see https://www.r-bloggers.com/calculating-required-sample-size-in-r-and-sas/
    install.packages("pwr")#statistical power
    library(pwr)
    
    delta=40 #u1-u2, difference between means (lower the difference ->bigger the sample size to detect)
    sigma=60 #standard deviation
    d=delta/sigma
    pwr.t.test(d=d, sig.level=.05, power = .80, type = 'two.sample')
    
    Result:
        Two-sample t test power calculation 

              n = 36.30569
              d = 0.6666667
      sig.level = 0.05
          power = 0.8
    alternative = two.sided

    NOTE: n is number in *each* group


@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
from builtins import * #all the standard builtins python 3 style


#see https://stackoverflow.com/questions/15204070/is-there-a-python-scipy-function-to-determine-parameters-needed-to-obtain-a-ta
from scipy.stats import norm, zscore

def sample_power_probtest(p1, p2, power=0.8, sig=0.05):
    z = norm.isf([sig/2]) #two-sided t test
    zp = -1 * norm.isf([power]) 
    d = (p1-p2)
    s =2*((p1+p2) /2)*(1-((p1+p2) /2)) #?
    n = (2*(s**2)) * ((zp + z)**2) / (d**2) #n = s * ((zp + z)**2) / (d**2)
    return int(round(n[0]))

def sample_power_difftest(d, s, power=0.8, sig=0.05):
    z = norm.isf([sig/2]) 
    zp = -1 * norm.isf([power])
    n = (2*(s**2)) * ((zp + z)**2) / (d**2)
    return int(round(n[0]))
#    z = norm.isf([sig/2])
#    zp = -1 * norm.isf([power])
#    n = s * ((zp + z)**2) / (d**2)
#    return int(round(n[0]))

if __name__ == '__main__':

    n = sample_power_probtest(0.33, 0.67, power=0.8, sig=0.05)
    print (n)  #14752
    
    delta=40 #difference between means (lower the difference ->bigger the sample size to detect)
    sigma=60 #standard deviation
    d=delta/sigma
    n = sample_power_difftest(d, 0.9, power=0.8, sig=0.05)
    print (n)  #392

