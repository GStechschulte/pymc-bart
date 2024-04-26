To run the profiling, you will need to install the additional dependencies:

```bash
pip install snakeviz line_profiler
```

`snakeviz` is used to visualize the profiling from the `cProfile` standard library. `cPorfile` is leveraged to gain a high-level view to guide which functions to profile with `line_profiler`.

`line_profiler` provides a line-by-line analysis of the function being profiled. In our case, we are interested in decorating the `.astep` method of the `PGBART` sampler with `@profile` to obtain a line-by-line profile analysis. The `.astep` method represents the main entry point of the particle sampler.

Run

```bash
kernprof -lv profiling/line_profiler.py
```

to print the line-by-line profile analysis to stdout. `line_profiler.py` contains a simple BART model with default parameters.


## Profiling notes

When running `kernprof -lv profiling/line_profiler.py` with `astep` decorated with `@profile`, the following output is obtained:

```bash
Function: astep at line 224

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   224                                               @profile
   225                                               def astep(self, _):
   226       100        159.0      1.6      0.0          variable_inclusion = np.zeros(self.num_variates, dtype="int")
   227                                           
   228       100        679.0      6.8      0.0          upper = min(self.lower + self.batch[~self.tune], self.m)
   229       100         34.0      0.3      0.0          tree_ids = range(self.lower, upper)
   230       100         38.0      0.4      0.0          self.lower = upper if upper < self.m else 0
   231                                           
   232       200         67.0      0.3      0.0          for odim in range(self.trees_shape):
   233       600        198.0      0.3      0.0              for tree_id in tree_ids:
   234       500        101.0      0.2      0.0                  self.iter += 1
   235                                                           # Compute the sum of trees without the old tree that we are attempting to replace
   236       500        312.0      0.6      0.0                  self.sum_trees_noi[odim] = (
   237       500       4075.0      8.2      0.1                      self.sum_trees[odim] - self.all_particles[odim][tree_id].tree._predict()
   238                                                           )
   239                                                           # Generate an initial set of particles
   240                                                           # at the end we return one of these particles as the new tree
   241       500      65561.0    131.1      1.9                  particles = self.init_particles(tree_id, odim)
   242                                           
   243      3869        680.0      0.2      0.0                  while True:
   244                                                               # Sample each particle (try to grow each tree), except for the first one
   245      3869        457.0      0.1      0.0                      stop_growing = True
   246     38690      10016.0      0.3      0.3                      for p in particles[1:]:
   247     69642    1044721.0     15.0     30.2                          if p.sample_tree(
   248     34821       4018.0      0.1      0.1                              self.ssv,
   249     34821       3940.0      0.1      0.1                              self.available_predictors,
   250     34821       3508.0      0.1      0.1                              self.prior_prob_leaf_node,
   251     34821       3578.0      0.1      0.1                              self.X,
   252     34821       3244.0      0.1      0.1                              self.missing_data,
   253     34821       7187.0      0.2      0.2                              self.sum_trees[odim],
   254     34821       6412.0      0.2      0.2                              self.leaf_sd[odim],
   255     34821       3868.0      0.1      0.1                              self.m,
   256     34821       4375.0      0.1      0.1                              self.response,
   257     34821       3848.0      0.1      0.1                              self.normal,
   258     34821       4114.0      0.1      0.1                              self.leaves_shape,
   259                                                                   ):
   260     16598    1610719.0     97.0     46.6                              self.update_weight(p, odim)
   261     34821       7637.0      0.2      0.2                          if p.expansion_nodes:
   262     27232       3851.0      0.1      0.1                              stop_growing = False
   263      3869        710.0      0.2      0.0                      if stop_growing:
   264       500         80.0      0.2      0.0                          break
   265                                           
   266                                                               # Normalize weights
   267      3369      29245.0      8.7      0.8                      normalized_weights = self.normalize(particles[1:])
   268                                           
   269                                                               # Resample
   270      3369     310740.0     92.2      9.0                      particles = self.resample(particles, normalized_weights)
   271                                           
   272       500       3957.0      7.9      0.1                  normalized_weights = self.normalize(particles)
   273                                                           # Get the new particle and associated tree
   274      1000       4158.0      4.2      0.1                  self.all_particles[odim][tree_id], new_tree = self.get_particle_tree(
   275       500         61.0      0.1      0.0                      particles, normalized_weights
   276                                                           )
   277                                                           # Update the sum of trees
   278       500       3106.0      6.2      0.1                  new = new_tree._predict()
   279       500        780.0      1.6      0.0                  self.sum_trees[odim] = self.sum_trees_noi[odim] + new
   280                                                           # To reduce memory usage, we trim the tree
   281       500       5786.0     11.6      0.2                  self.all_trees[odim][tree_id] = new_tree.trim()
   282                                           
   283       500         90.0      0.2      0.0                  if self.tune:
   284                                                               # Update the splitting variable and the splitting variable sampler
   285       500         79.0      0.2      0.0                      if self.iter > self.m:
   286       450       4096.0      9.1      0.1                          self.ssv = SampleSplittingVariable(self.alpha_vec)
   287                                           
   288      1955       2092.0      1.1      0.1                      for index in new_tree.get_split_variables():
   289      1455        571.0      0.4      0.0                          self.alpha_vec[index] += 1
   290                                           
   291                                                               # update standard deviation at leaf nodes
   292       500         86.0      0.2      0.0                      if self.iter > 2:
   293       498       3345.0      6.7      0.1                          self.leaf_sd[odim] = self.running_sd[odim].update(new)
   294                                                               else:
   295         2     292413.0 146206.5      8.5                          self.running_sd[odim].update(new)
   296                                           
   297                                                           else:
   298                                                               # update the variable inclusion
   299                                                               for index in new_tree.get_split_variables():
   300                                                                   variable_inclusion[index] += 1
   301                                           
   302       100         19.0      0.2      0.0          if not self.tune:
   303                                                       self.bart.all_trees.append(self.all_trees)
   304                                           
   305       100         45.0      0.5      0.0          stats = {"variable_inclusion": variable_inclusion, "tune": self.tune}
   306       100        226.0      2.3      0.0          return self.sum_trees, [stats]
```

The majority of the time in this function is spent in
- `p.sample_tree` = 30.2%
- `self.update_weight` = 46.6%
- `self.resample` = 9.0%
- `self.running_sd[odim].update(new)` = 8.5%


We can then continue to `@profile` the methods and functions in the call stack. Decorating the `sample_tree` method, we obtain the following output:

```bash
Function: sample_tree at line 55

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    55                                               @profile
    56                                               def sample_tree(
    57                                                   self,
    58                                                   ssv,
    59                                                   available_predictors,
    60                                                   prior_prob_leaf_node,
    61                                                   X,
    62                                                   missing_data,
    63                                                   sum_trees,
    64                                                   leaf_sd,
    65                                                   m,
    66                                                   response,
    67                                                   normal,
    68                                                   shape,
    69                                               ) -> bool:
    70     34821       3669.0      0.1      0.4          tree_grew = False
    71     34821       5478.0      0.2      0.7          if self.expansion_nodes:
    72     30754       4717.0      0.2      0.6              index_leaf_node = self.expansion_nodes.pop(0)
    73                                                       # Probability that this node will remain a leaf node
    74     30754       5519.0      0.2      0.7              prob_leaf = prior_prob_leaf_node[get_depth(index_leaf_node)]
    75                                           
    76     30754      16483.0      0.5      2.0              if prob_leaf < np.random.random():
    77     33902     751496.0     22.2     90.9                  idx_new_nodes = grow_tree(
    78     16951       1923.0      0.1      0.2                      self.tree,
    79     16951       1491.0      0.1      0.2                      index_leaf_node,
    80     16951       1666.0      0.1      0.2                      ssv,
    81     16951       1538.0      0.1      0.2                      available_predictors,
    82     16951       1467.0      0.1      0.2                      X,
    83     16951       1393.0      0.1      0.2                      missing_data,
    84     16951       1432.0      0.1      0.2                      sum_trees,
    85     16951       1405.0      0.1      0.2                      leaf_sd,
    86     16951       1616.0      0.1      0.2                      m,
    87     16951       1607.0      0.1      0.2                      response,
    88     16951       1399.0      0.1      0.2                      normal,
    89     16951       1768.0      0.1      0.2                      shape,
    90                                                           )
    91     16951       2397.0      0.1      0.3                  if idx_new_nodes is not None:
    92     16598       2628.0      0.2      0.3                      self.expansion_nodes.extend(idx_new_nodes)
    93     16598       1635.0      0.1      0.2                      tree_grew = True
    94                                           
    95     34821      13820.0      0.4      1.7          return tree_grew
```

The majority of the time in this function is spent in:
- `grow_tree` = 90.9%