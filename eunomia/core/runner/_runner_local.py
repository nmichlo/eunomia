from eunomia.core.runner._runner import BaseRunner


# ========================================================================= #
# Local Runner                                                              #
# ========================================================================= #


class RunnerLocal(BaseRunner):

    def _run(self, i: int, num_sweeps: int, func, merged_config: dict, changed: tuple):
        if not self._no_output:
            if num_sweeps > 1:
                if i == 1:
                    print()
                print('='*100)
                print(f'SWEEP {i} OF {num_sweeps}:', f"[{', '.join(map(repr, changed))}]" if changed else "")
                print('='*100)
                print()
        # run the program -- we dont want to catch errors!
        func(merged_config)
        # done!


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
