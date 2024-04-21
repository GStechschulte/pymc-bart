import numpy as np
import pymc as pm

import pymc_bart as pmb


def main():

    np.random.seed(0)
    n = 100
    X = np.random.uniform(0, 10, n)
    Y = np.sin(X) + np.random.normal(0, 0.5, n)

    with pm.Model() as model:
        mu = pmb.BART("mu", X.reshape(-1, 1), Y, m=50)
        y = pm.Normal("y", mu, sigma=1., observed=Y)
        step = pmb.PGBART([mu])

    for iter in range(100):
        step.astep(iter)
    
    # with Profile() as profile:
    #     for iter in range(100):
    #         step.astep(iter)

    #     (
    #         Stats(profile)
    #         .strip_dirs()
    #         .sort_stats(SortKey.CALLS)
    #         .print_stats()
    #     )

if __name__ == "__main__":
    main()