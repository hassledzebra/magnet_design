"""
Parallel + progress utilities for pymoo optimization runs.

Features:
- Easy parallelization using ThreadPool or Process Pool via pymoo's
  StarmapParallelization elementwise runner.
- Live progress bar with ETA and evals count using alive-progress.

Usage inside your optimization script (after you construct `problem` and `algorithm`):

    from optimizer_parallel_tools import minimize_with_progress

    res = minimize_with_progress(
        problem,
        algorithm,
        n_gen=4000,
        seed=1,
        verbose=True,
        n_workers=8,
        backend='thread',   # or 'process'
    )

Notes:
- Thread backend is often the safest default when using numpy/scipy/magpylib,
  and can still provide speedups where native code releases the GIL.
- Process backend can yield more speed but requires all objects used during
  evaluation to be picklable.
"""

from __future__ import annotations

import time
from typing import Literal, Optional

from pymoo.optimize import minimize
from pymoo.core.problem import StarmapParallelization


def _make_pool(n_workers: int, backend: Literal['thread', 'process']):
    if backend == 'thread':
        from multiprocessing.pool import ThreadPool
        pool = ThreadPool(n_workers)
    elif backend == 'process':
        from multiprocessing import Pool
        pool = Pool(n_workers)
    else:
        raise ValueError("backend must be 'thread' or 'process'")
    return pool


def setup_parallel(problem, n_workers: int = 8, backend: Literal['thread', 'process'] = 'thread'):
    """Attach a parallel elementwise runner to a pymoo ElementwiseProblem.

    Returns the pool so the caller can close/join it when done.
    """
    pool = _make_pool(n_workers, backend)
    runner = StarmapParallelization(pool.starmap)
    problem.elementwise_runner = runner
    return pool


def minimize_with_progress(
    problem,
    algorithm,
    n_gen: int,
    seed: int = 1,
    verbose: bool = True,
    n_workers: int = 8,
    backend: Literal['thread', 'process'] = 'thread',
    show_progress: bool = True,
):
    """Run pymoo minimize with parallel evaluation and a live progress bar.

    The bar advances per generation and shows ETA and total evals.
    """
    pool = setup_parallel(problem, n_workers=n_workers, backend=backend)

    # Prepare progress UI
    bar = None
    last_gen = 0
    start_time = time.time()

    if show_progress:
        try:
            from alive_progress import alive_bar
            bar_ctx = alive_bar(n_gen, title='Optimization', length=30, bar='smooth')
            bar = bar_ctx.__enter__()
        except Exception:
            bar = None

    def _cb(algorithm):
        nonlocal last_gen, start_time, bar
        try:
            gen = getattr(algorithm, 'n_gen', last_gen)
            inc = max(0, gen - last_gen)
            if bar is not None and inc > 0:
                # Update bar and status text
                bar(inc)
                n_eval = getattr(getattr(algorithm, 'evaluator', None), 'n_eval', None)
                elapsed = time.time() - start_time
                # Simple ETA based on generations
                rate = gen / elapsed if elapsed > 0 else 0
                rem = (n_gen - gen) / rate if rate > 0 else 0
                status = f"gen {gen}/{n_gen}"
                if n_eval is not None:
                    status += f" | evals {n_eval}"
                status += f" | eta {rem:0.0f}s"
                try:
                    bar.text(status)
                except Exception:
                    pass
            last_gen = gen
        except Exception:
            # Never let UI issues break the optimization
            pass

    try:
        res = minimize(
            problem,
            algorithm,
            ('n_gen', n_gen),
            seed=seed,
            verbose=verbose,
            callback=_cb,
        )
    finally:
        # Close progress bar if opened
        if bar is not None:
            try:
                bar.close()  # alive-progress bars support close()
            except Exception:
                pass
            try:
                bar_ctx.__exit__(None, None, None)
            except Exception:
                pass
        # Teardown pool
        try:
            pool.close()
            pool.join()
        except Exception:
            pass

    return res

