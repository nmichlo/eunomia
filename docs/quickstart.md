---
title: Quickstart
pos: 200
---


# Quickstart

## Option Special Keys

Options are dictionaries containing data. At their
root options can include various special keys or directives that change the behavior of the config m

!!! summary "Special Option Keys"

    === "\_package\_"
    
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
    
    === "\_merge\_"
    
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


## Examples

### Simple Examples

Given the following configuration

```yaml
--8<-- "docs/examples/quickstart/configs/default.yaml"
```
```yaml
--8<-- "docs/examples/quickstart/configs/framework/vae.yaml"
```
```yaml
--8<-- "docs/examples/quickstart/configs/dataset/shapes3d.yaml"
```

We can load the config by calling:

```python3
--8<-- "docs/examples/quickstart/example_simple_yaml.py"
```

The resulting output of the merged config in yaml format is:

```yaml
--8<-- "docs/examples/quickstart/target_simple.yaml"
```

### Modified Yaml Example

You'll notice that in the previous example we had the `__defaults__` key
which contained keys and values corresponding to the nested files which
should be merged into the config.

  - keys correspond to a nested group
    `/group/subgroup` is an absolute path starting from the root
    `group/subgroup` is a relative path starting from the group containing the option.
  - values correspond to the name of an option in the group specified by the key.

If we add new files, we can change these defaults to point to them.

```yaml
--8<-- "docs/examples/quickstart/configs/alternate.yaml"
```

```yaml
--8<-- "docs/examples/quickstart/configs/framework/betavae.yaml"
```


#### Equivalent Pythonic Example

The above yaml configuration generates the following representation behind
the scenes using the yaml backend.

If you would prefer to specify everything manually we can use the
following equivalent pythonic nested approach:

??? example
    
    ```python3
    --8<-- "docs/examples/quickstart/example_simple_pythonic.py"
    ```
    
    The resulting output of the merged config in yaml format is:
    
    ```yaml
    --8<-- "docs/examples/quickstart/target_simple.yaml"
    ```


### Variable Substitution Yaml Example

Eunomia supports variable interpolation. We add a new option at the root of the
configs directory called `advanced.yaml` to demonstrate these features.

```yaml
--8<-- "docs/examples/quickstart/configs/advanced.yaml"
```

String substitution is based heavily on f-strings. There are two types of substitutions:

  - **references**: `${<ref>}` eg. `${trainer.epochs}` is replaced with `100`.
  - **expressions**: `${=<expr>}` or `${=<expr>;}` eg. `${=conf.trainer.epochs + 42}` evaluates to `142`.
    
    Since string substitution takes place by parsing a string, if the expression or reference is 
    the only component of the string, then the raw value is used and it is not converted to a string.

??? note "Interpreter Limitations"
    The python interpreter for these expressions supports a very limited subset of the language. Statements, 
    assignments, lambdas are not supported. Various common symbols are made available by
    default similar to the `asteval` library, as well as `conf` which points to the currently merging config.

??? bug "Parsing Limitations"
    The semicolon `;` can usually be left out at the end of an expression, however due to a limitation
    of the current grammar used to parse the expression, the semicolon may need to be left in when used
    to evaluate dictionaries. eg. `${={'foo': 'bar'};}` instead of `${={'foo': 'bar'}}`

We load this option by changing the entrypoint to `'advanced'`.
Otherwise, the default entrypoint is appropriately `'default'`.

```python3
--8<-- "docs/examples/quickstart/example_advanced_yaml.py"
```

The resulting output of the merged config in yaml format is:

```yaml
--8<-- "docs/examples/quickstart/target_advanced.yaml"
```
