#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 10 11:44:47 2025

@author: xiningyang
"""

import numpy as np


def existing_ship_lifetime(mean, std, build_year, initial_year):

    # build_year: the time when the ship is built.
    # initial_year: the start year of the timeframe, i.e., 2025 in this study.
    # mean: the mean lifetime of the ship.
    # std: the standard deviation of normal distribution of the ship.
    
    random_lifetime=np.random.normal(mean, std, 1000000).round(0).astype(int)       
    lifetime_sample=np.random.choice(random_lifetime[random_lifetime>initial_year-build_year], 1, replace=True)
    
    return lifetime_sample


def new_ship_lifetime(mean, std):

    # mean: the mean lifetime of the ship.
    # std: the standard deviation of normal distribution of the ship.
    
    random_lifetime=np.random.normal(mean, std, 1000000).round(0).astype(int)       
    lifetime_sample=np.random.choice(random_lifetime, 1, replace=True)
    
    return lifetime_sample
