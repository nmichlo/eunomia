---
title: Overview
pos: 100
---

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


## Generating The Output Config

The user builds the input config consisting of a tree of groups and options. Once built the output
config is obtained by traversing the tree using directives specified in options themselves.

The starting point or entrypoint is defined by the user as the first option to visit, each visited option can specify
other options to include in the traversal. Each time an option is visited, it is included by being merged into the output
config.

!!! tldr "Merging Process"
    The merging process of merging configs is simple:
    
    1. visit an option
    2. merge the chosen option into the output config at the location specified by `__package__`
    3. recursively visit options in the order specified by `__defaults__` using depth first search.


## Option Special Keys

Options are dictionaries containing data. At their
root options can include various special keys or directives that change the behavior of the config m

!!! summary "Special Option Keys"

    === "\_\_package\_\_"
    
        `_package_: str`
        
        Specify what the root of this chosen option should be after merging.

        -----------------

        The package is a fullstop `.` delimited list of identifiers
        eg. `foo.bar.baz`. Package paths can be either absolute or relative:
        
        - **aboslute**: does not start with fullstop eg. `key.subkey`
        - **relative**: starts with fullstop eg. `.subkey.subsubkey`

        -----------------
    
        ??? info "Aliases"
            * `<root>` set the package as the root, ie. directly merge into the config. This
               is equivalent to an empty package key `''` but the intention is more clear.
            * `<group>` (default) set the package as the path to the current group that the option resides in.
              Current option is merged into the recursively visited keys of the path to the current group.
              This is equivalent to a single relative full stop `'.'`, but the intention is more clear.
    
    === "\_\_defaults\_\_"
    
        `__defaults__: Dict[str, str]`
    
        A dictionary of *group paths* to *option names* that should also be visited and merged.

        !!! hint
            `__defaults__` is similar to `defaults` in hydra config.

        -----------------

        **Group paths** are similar to package paths, but consist of identifiers delimited
        by forward slashes `/` instead of full stops. They can be absolute or relative:

        - **aboslute**: starts with a forward slash eg. `/group/subgroup`
        - **relative**: does not start with a forward slash eg. `subgroup/subsubgroup`

        The root group is not named, rather reference it as `/`. Aliases are
        not supported unlike packages.

        -----------------

        **Option names** are single identifiers that correspond to the name of an
        option in the group referenced by the group path.


-------------------------------------------------------------
