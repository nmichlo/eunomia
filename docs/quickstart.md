---
title: Quickstart
pos: 200
---


# Quickstart

While this is a quickstart, and you can play with and modify any of
these examples for your own use. Reading through the Eunomia [overview](/overview)
will greatly help.

The most important aspects to understand from the Eunomia [overview](/overview) are
that:

- Individual "input configs" called "Options", listed in the `__defaults__` keys,
  are merged in a depth first search fashion starting from the user defined "entrypoint"
  to form the "output config" or "merged config".
    - `W.I.P:` Individual "input configs" are called "Options" because they can be overridden from
      the command line. Options are mutually exclusive and are contained in a "Group"
    - Groups and Options can be nested within Groups. Options however cannot contain children.
      An input config always has a root group.
    - When input configs are merged into the output config, the `__package__` reserved key defines
      the new path in the output config. By default this path is `<group>` which is an alias for
      that path to the current group that the option resides in. The other common alias is `<root>`
      or a non-prefixed merge into the output config.
- All eunomia reserved keys with the prefix and suffix `__` (eg. `__defaults__` and `__package__`) are
  stripped from the input configs when merging takes place.
- Variable substitution can take place during merging, only variables already merged into
  the output config via DFS are made available for substitution.


## Simple YAML Example

Given the following input configs:

???+ example "Input Configs"

    ```yaml
    --8<-- "examples/docs/quickstart/configs/default.yaml"
    ```
    ```yaml
    --8<-- "examples/docs/quickstart/configs/framework/betavae.yaml"
    ```
    ```yaml
    --8<-- "examples/docs/quickstart/configs/dataset/shapes3d.yaml"
    ```

With the YAML backend, folders and nested folders indicate groups, while
YAML files indicate options or input config files.

We generate our output config by specifying the entrypoint as the option
`default` which resides in the root group `/`.

???+ example "Code"

    ```python3
    --8<-- "examples/docs/quickstart/simple_yaml.py"
    ```
    
The resulting output config of this entrypoint and input config in yaml format is:

???+ done "Output Config"

    ```yaml
    --8<-- "examples/docs/quickstart/simple_yaml.target"
    ```


### Equivalent Python

The above yaml input config generates the following representation behind
the scenes using the yaml backend.

If you would prefer to specify everything manually in python we can use
the  following equivalent pythonic nested approach, with the Object backend.

Remember, nested Group objects correspond to folders in the previous example,
and Option objects correspond to YAML files.

???+ example "Input Configs"
    
    ```python3
    --8<-- "examples/docs/quickstart/simple_pythonic.py"
    ```
    
The resulting output of the merged config in yaml format is:
    
???+ done "Output Config"

    ```yaml
    --8<-- "examples/docs/quickstart/simple_pythonic.target"
    ```

#### Custom Backends

All backends in fact generate these `Group` and `Option` objects behind the
scenes for merging by the `Loader`. You can easily write your own backend.

???+ note "Custom Backends"
    
    The `eunomia_loader` helper function automatically determines the correct
    backend to use based on the input datatype.
    
    - string are considered to be paths to the root config folder for the YAML
      backend.
    - Group objects are passed to the Object backend.
    - Dictionaries although not covered in the quickstart are passed to the
      Dictionary backend.

    If you wish you can even write your own backends by subclassing
    `#!python eunomia.backend.Backend`. The overridden function should
    return a new `Group` object from the data passed to the constructor.

    You can pass the instantiated version of your backend to the function
    `eunomia.eunomia_loader_adv`.

## Entrypoint & Packages

You'll notice that in the previous example we had the `__defaults__` key
which contained keys and values corresponding to the nested options which
should be merged into the config.

  - keys correspond to a nested group:
    - `/group/subgroup` is an **absolute** group path starting from the root
    - `group/subgroup` is a **relative** group path starting from the group containing the option.
  - values correspond to the name of an option in the group specified by the key.

If we add new files to the YAML example, we can change these defaults
to point to them.

???+ example "Input Configs"

    ```yaml
    --8<-- "examples/docs/quickstart/configs/alternate.yaml"
    ```
    
    ```yaml
    --8<-- "examples/docs/quickstart/configs/dataset/dsprites.yaml"
    ```
    
    ```yaml
    --8<-- "examples/docs/quickstart/configs/framework/vae.yaml"
    ```

Notice that various other differences exist from the previous example.

???+ attention "Input Changes"

    - In `configs/alternate.yaml` we use absolute instead of relative paths to the
      groups in the defaults list, **also** the defaults list is reordered, which
      means that this time the dataset is visited before the framework by the merge
      algorithm.

    - In `configs/dataset/dsprites.yaml` we explicitly specify the package `data.groundtruth`
      instead of the default package `<group>`.

    - In `configs/framework/vae.yaml` we explicitly specify the package `<root>`
      instead of the default package `<group>`.

Selecting the new entrypoint is as simple as changing the `'default'`
argument to `'alternate'` in the first YAML example.

???+ example "Code"
    
    ```python3
    --8<-- "examples/docs/quickstart/simple_yaml_alt.py"
    ```
    
The resulting output of the merged config in yaml format is:
    
???+ done "Output Config"

    ```yaml
    --8<-- "examples/docs/quickstart/simple_yaml_alt.target"
    ```


## Variable Substitution

Eunomia supports variable interpolation. We add a new option at the root of the
configs directory called `advanced.yaml` to demonstrate these features.

???+ example "Input Configs"

    ```yaml
    --8<-- "examples/docs/quickstart/configs/advanced.yaml"
    ```

String substitution is based heavily on f-strings. There are three supported types of substitutions that can occur:

  - _References_: `...${<ref>}...` eg. `${trainer.epochs}` is replaced with `100`.
  - _Expressions_: `...${=<expr>}...` or `...${=<expr>;}...` eg. `${=conf.trainer.epochs + 42}` evaluates to `142`.
    While attempts are made to enforce the safety of evaluated expressions, no guarantee can be made.
    **Do not evaluate untrusted code!**
  - _F-Strings_: `f"<f-string>"` or `f'<f-string>'`, these are special cases of the Expressions that only
    evaluate as normal pythonic f-strings. Behind the scenes they are wrapped as if they were `${=f"<f-string>"}`
    or `${=f'<f-string>'}`

???+ tip "Raw Values"

    Since string substitution takes place by parsing a string, if the expression or reference is 
    the only component of the string, then the raw value is used and it is not converted to a string.

    Note the resulting value for `subbed.beta_expr` will be the number `8` while the value for
    `subbed.beta_sub_ref` will be the string `'beta is 4'`

Please note that the interpreter only supports a limited subset of python, and it
can only interpret expressions, not statements:

??? warning "Interpreter Limitations"

    The python interpreter for these expressions supports a very limited subset of the language. Statements, 
    assignments, lambdas are not supported. Various common symbols are made available by
    default similar to the `asteval` library, as well as `conf` which points to the currently merging config.


??? bug "Possible Dictionary Parsing Bug"

    The semicolon `;` can usually be left out at the end of an expression, however due to a limitation
    of the current grammar used to parse expressions, the semicolon may need to be left in when used
    to evaluate dictionaries. eg. `${={'foo': 'bar'};}` instead of `${={'foo': 'bar'}}`

As with the previous example, we change the entrypoint to `'advanced''`.

???+ example "Code"

    ```python3
    --8<-- "examples/docs/quickstart/advanced_yaml.py"
    ```

The resulting output of the merged config in yaml format is:

???+ done "Output Config"

    ```yaml
    --8<-- "examples/docs/quickstart/advanced_yaml.target"
    ```
