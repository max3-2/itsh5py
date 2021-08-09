#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 11:18:00 2021

@author: ez5962
"""
import numpy as np
import itsh5py
# import matplotlib.pyplot as plt

# Taken from mayavi examples!
x, y = np.mgrid[-5.:5.:200j, -5.:5:200j]
z = np.sin(x + y) + np.sin(2 * x - y) + np.cos(3 * x + 4 * y)

# Visualize the data
# plt.contourf(x, y, z)
# plt.colorbar(label='Magnitude')
# plt.savefig('cont_demo.png', transparent=True, dpi=150)

demo_file = itsh5py.save('demo', {'x': x, 'y': y, 'data': z})
demo_2_file = itsh5py.save('demo2', {'x': x, 'y': y, 'data': z, 'meta': ['type1', 2.]})

lazy_demo = itsh5py.load('demo')
lazy_demo_2 = itsh5py.load('demo2')

itsh5py.config.use_lazy = False
basic_demo = itsh5py.load('demo')
basic_demo_2 = itsh5py.load('demo2')
itsh5py.config.use_lazy = True


file = itsh5py.save('demo_att',
                    {'x': x, 'y': y, 'data': z,
                      'attrs': {'additional_str': 'meta_string',
                                'addition_float': 100.,
                                },
                     })

reloaded = itsh5py.load(file)
[f'{k}: {v} (Type {type(v)})' for k, v in reloaded.h5file.attrs.items()]
reloaded = itsh5py.load(file, unpack_attrs=True)
reloaded['attrs']

itsh5py.open_filenames()

lazy_demo_unlazied = lazy_demo.unlazy()
lazy_demo_2.close()
reloaded.close()

itsh5py.open_filenames()

file.unlink()
demo_file.unlink()
demo_2_file.unlink()
