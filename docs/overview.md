
# Overview

## Terminology

We use the similar terminology to [Hydra](https://hydra.cc).

| Name              | Description                                                             
| ----------------- | -----------
| **Group**         | A node in the _input config_ tree, a mutually exclusive set of child _options_ and child _groups_. Each child has a unique name.
| **Option**        | A leaf in the _input config_ tree, a visitable object containing data or configuration values.
| **Input Config**  | Or simply `Config`, a tree of _groups_ and _options_, with the root being a group.
| **Entrypoint**    | An _option_ specified by the user as the starting point for generating a _output config_. This is the same as Hydra's `Primary Config`
| **Output** Config | Or `Merged Config`, the final generated dictionary available to the user after merging all visited _options_, starting from the _entrypoint_.
| **Node**          | Configuration values contained in options or the resulting output config. Primitive values, dictionaries, lists, tuples and other objects.
| **Package Path**  | A path to a configuration _node_, usually for referencing child values in the _output config_.
| **Group Path**    | A path to a group in the _input config_, usually for referencing child groups of the _input config_.

::: eunomia.config