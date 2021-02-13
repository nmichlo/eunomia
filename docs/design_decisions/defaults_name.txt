
# "defaults" replacement name

hydra config uses the name "defaults" for the list of other
options that should be included for merging into the output config.

- "defaults" matches well with the idea of command line arguments, but does
  not describe the recursive merging operation well.

## Ranking Based On Merging

| Names    | First Thought & Points |
| -------- | ---------------------- |
| merge    | 1. merge these files into this
| combine  | 1. merge those files
| include  | 1. copy paste into this
| import   | 4. include into this under name
| link     | 4. somehow link to those files, as if it was interpolation not merging
| visit    | 6. describes the DFS well, but not the merge operation
| defaults | 6. does not make sense, as if those values were made available to the interpreter or config, but not used
| options  | 6. settings to modify the option

## Ranking Based On DFS

| Names    | First Thought & Points |
| -------- | ---------------------- |
| link     | 1. implies relation
| visit    | 1. implies relation
| include  | 1. implies relation
| import   | 1. implies relation
| defaults | 5. no relation
| merge    | 5. no relation
| combine  | 5. no relation
| options  | 5. no relation

## Ranking Based On Being Overridable

| Names    | First Thought & Points |
| -------- | ---------------------- |
| defaults | 1. makes sense
| options  | 2. could maybe be overridden
| visit    | 2. could maybe be overridden
| include  | 2. could maybe be overridden
| import   | 5. cannot be overridden
| merge    | 5. cannot be overridden
| combine  | 5. cannot be overridden
| link     | 5. cannot be overridden

## Final Rankings

| Name     | Mrg. | Dfs. | Ovr. | Score |
| -------- | ---- | ---- | ---- | ----- |
| include  | 1    | 1    | 2    | = 2
| visit    | 6    | 1    | 2    | = 12
| link     | 4    | 1    | 5    | = 20
| import   | 4    | 1    | 5    | = 20
| combine  | 1    | 5    | 5    | = 25
| merge    | 1    | 5    | 5    | = 25
| defaults | 6    | 5    | 1    | = 30
| options  | 6    | 8    | 1    | = 48

# Decision:

"include" strikes a nice balance between merge, dfs and defaults
- include a file to be merged into the output config
- include a file to be visited by dfs
- include something else instead
