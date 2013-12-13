# Caliendo

## About

Caliendo is a very simple interface for mocking APIs. It allows you to skip
(potentially heavy) calls to your database or remote resources by storing sets
of calls and caching responses based on the sequence of execution as well as
function arguments. In some cases this improves unit test performance by
several orders of magnitude.

## Installation

Caliendo is set up to install with `pip`. You can install it directly from
GitHub by running:

```console
pip install git+git://github.com/buzzfeed/caliendo.git#egg=caliendo
```

Alternatively if you have a copy of the source on your machine; cd to the
parent directory and run:

```console
pip install ./caliendo
```

To run tests you can use the standard unittest module. You'll have various
prompts during the process. You can just hit ctrl+d to continue. To run all
tests you should use nose with --nocapture. nose capturing interferes with
the interactive prompts.

Your tests will need to be written is TestCases of some sort (classes).
Caliendo uses the TestCase instance to figure out what module the test came
from at runtime by referring to self, which is the first argument to the
test methods.

```console

python setup.py test
```

```console

nosetests --all-modules --nocapture test/
```

## Configuration

Caliendo requires file read/write permissions for caching objects. The first time
you invoke tests calling caliendo:

1. Caliendo writes to the specified cache files. The default location is in the
   caliendo build, caliendo/cache, caliendo/evs, and caliendo/seeds, and
   caliendo/used. You can change where caliendo creates these directories and
   file by setting the environment variable:

```console
export CALIENDO_CACHE_PREFIX=/some/absolute/path

```

2. If you would like to be prompted to overwrite or modify existing cached values
   you can write the environment variable CALIENDO_PROMPT.

```console
export CALIENDO_PROMPT=True

```

### Configuration Best Practices

There are a lot of ways to set environment variables in your application. On our team we've come up with a few 'best practices' that work really well for us.

1. When using `nosetests` set the variables in the `__init__.py` file for your integration testing suite.

    ```python
    import os
    import sys
    os.environ['CALIENDO_CACHE_PREFIX'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'caliendo')
    os.environ['PURGE_CALIENDO'] = 'True'

    ```

2. When using `unittest` with setup.py (invoked like `python setup.py test`) set the variables as above in either setup.py or the `__init__.py` file for your integration test folder.

3. When using `fabric` to run tests using either of these methods include the above in your `fabfile/__init__.py` file.

## Examples

Here are a few basic examples of use.

### The Cache

Caliendo offers a cache which decorates callables. If you pass the cache the handle for the callable, and the args/kwargs; it will be 'cached'. The behavior is a little complex. Explained below:

  * When the method is called the first time a counter is issued that is keyed on a hash of the stack trace and a serialization of the function parameters.
  * If/When a matching hash is generated (e.g. a method is called with the same parameters by the same calling method the counter is incremented.
  * With each unique counter the result of the function call is pickled and stored matching a CallDescriptor. If a return value can't be pickled caliendo will attempt to munge it. If caliendo fails to munge it an error will be thrown.
  * When a method is called that matches an existing counter; the stored CallDescriptor rebuilds the original call and the original return value is returned by the cache.

```python
from caliendo.facade import cache

global side_effect
side_effect = 0
def foo():
  global side_effect
  side_effect += 1
  return side_effect

for i in range(3):
  assert cache(handle=foo) == i + 1

print side_effect
```

When the above example is run the first time; it will print 2. For every subsequent time it is run it will print 0 unless caliendo's cache is cleared.

### Service Patching

An interface inspired greatly by python Mock is `patch()`.

`patch()` is intended to be used as a decorator for integration/unit tests that need to be decoupled from external services.

When `patch` is called it returns the test it decorates in the context of the specified method replaced by it's `caliendo.facade.cache` decorated version.

When the decorated test is invoked it is patched at runtime. After the test returns it is automatically unpatched.

`patch`, by default, uses `caliendo.facade.cache`. If you pass an `rvalue` as the second parameter; your patched method will return that value.

```python

# Pretend these methods are all defined in various modules in the codebase.
# Let foo() be defined in api.services.foos
def foo():
  return 'foo'
# Let bar() be defined in api.services.bars
def bar():
  return foo()
# Let baz be defined in api.bazs
def baz():
  return bar()

# Now for our test suite.
import unittest
from caliendo.patch import patch
from api.bazs import baz

class ApiTest(unittest.TestCase):

  @patch('api.services.bars.bar', rvalue='biz')
  def test_baz(self):
    assert baz() == 'biz'
```

In the above example `bar` is nested in the service layer of the architecture. We can import it once at the head of the test suite and effectively patch it at the test's invocation.

We set the rvalue to 'biz', but if we left it alone the value 'foo' would have been cached on the initial run. Every subsequent run would not have called the `foo` or `bar` method, and would have simply returned the cached value from the initial invokation of the test.

### Expected Values

There are a bunch of idiomatic methods for testing that expected values match observed values. At the root of this functionality is the `cache`.

#### The basic behavior of these methods is all the same:

  1. The observed value is passed for the first time.
  2. Caliendo will give the user an interactive shell to check the expected value (stored in the variable `ev`)
  3. The user can modify the expected value by modifying `ev` in the shell.
  4. When the user quits with `ctrl+d` the expected value, `ev`, will be cached by `cache`.
  5. On this run the check is trivial. If the expected value stored is valid for `cache`ing (e.g. vaguely `pickle`able) the test will pass.
  6. When the `expected_value` method is invoked again in the same test/call the `cache`d value will be used for comparison to the new observed value.

#### The available methods are:

##### `expected_value.is_true_under(validator, observed_value)`

This is the most complicated method. As the first argument it takes a validator used to validate the observed value against the expected value.

The validator should take the expected value as the first argument and the observed value as the second. The return value doesn't really matter. The output of `expected_value.is_true_under()` is whatever your return value is.

```python
def validator(expected_value, observed_value):
    # Do a bunch of assertions here
    return anything

```

##### `expected_value.is_equal_to(observed_value)`

Just compares the observed value to the cached value.

##### `expected_value.is_greater_than(observed_value)`

Tests that the expected value is greater than the observed value.

##### `expected_value.is_less_than(observed_value)`

Tests that the expected value is less than the observed value.

##### `expected_value.contains(observed_value, el)`

Sorry, this one isn't so idiomatic. Tests that the observed value contains `el`

##### `expected_value.does_not_contain(observed_value, el)`

Sorry, this one isn't so idiomatic either. Tests that the observed value does not contain `el`

### Side Effects

Side effects can be run by patched methods.

If you pass an Exception that inherits from `BaseException`, `Exception`, or `StandardError` your exception will be raised.

```python

import unittest
from caliendo.patch import patch
from api.bazs import baz
import sys

class ApiTest(unittest.TestCase):

  @patch('api.services.bars.bar', side_effect=Exception("Things went foobar!"))
  def test_baz(self):
    with self.assertRaisesRegexp(Exception, r"Things went foobar!"):
        baz()

```

If you pass a callable as the side effect it will be called and the result returned. The arguments and keyword arguments to the method being patched will be passed.

```python

import unittest
from caliendo.patch import patch
from api.bazs import baz
import sys

counter = 0
def example_side_effect(*args, **kwargs):
    global counter
    counter += 1
    return 'foo'

class ApiTest(unittest.TestCase):

  @patch('api.services.bars.bar', side_effect=example_side_effect)
  def test_baz(self):
    assert baz() == 'foo'
    assert counter == 1

```


### Purge

You can purge unused cache file from the cache by using the purge functionality at `caliendo.db.flatfiles.purge`.

By including a call to purge at the end of a full run of the tests; any unused portion of any part of the cache will be erased.

This is a good way to commit minimal files to your code base.

```python

from caliendo.db.flatfiles import purge

# Run all your tests:
unittest.main()

# Then purge unused files.
purge()

```

### The Facade

This is the buggiest feature of `caliendo`.

If you have an api you want to run under Caliendo you can invoke it like so:

```python
some_api     = SomeAPI()
caliendo_api = Facade( some_api ) # Note: caliendo is invoked with the INSTANCE, not the CLASS
```

### Chaining

As of revision v0.0.19 caliendo supports chaining so you can invoke it like:

```python
caliendo_api = Facade(some_api)
baz = caliendo_api.get_foo().get_bar().get_baz()
```

If type(baz) is not in ( float, long, str, int, dict, list, unicode ) it will be automatically wrapped by caliendo.

### Type Checking

Some APIs check the types or __class__ of the variables being passed in. A caliendo facade will have a class, `caliendo.facade.Wrapper`.

In order to unwrap an object to be type-checked by the target API you have to invoke the `wrapper__unwrap()` method on the Facade'd API releasing the object to the target API.

A second method allows the implementer to specify a list of object to avoid Facading entirely. (Useful for exporting models).

```python
facaded_api = Facade(SOMEAPI())
facaded_api.wrapper__ignore( somemodule.SomeClassDefinition )
```

The above example will ensure objects with `__class__` `somemodule.SomeClassDefinition` will never be wrapped.

To stop ignoring a particular class you can do:

```python
facaded_api = Facade(SOMEAPI())
facaded_api.wrapper__ignore( somemodule.SomeClassDefinition )
facaded_api.wrapper__unignore( somemodule.SomeClassDefinition )
```

## Execution

Once you have an instance of an API running under a `Facade` you should be able
to call all the methods normally.

## Troubleshooting

1. If you start getting unexpected API results you should clear the cache by
   simply deleting all the rows in the `test_io` table.

2. Caliendo doesn't support a large level of nested objects in arguments or
   return values. If you start getting unexpected results this may be the
   problem. Better nesting is to come.

3. If you alternate between calls to the `Facade` instance of an API and the
   API itself you will probably see unexpected results. Caliendo maintains
   the state of the API by maintaining a reference to the API internally.

4. If you have a class inheriting from `dict` you'll need to define a
   `__getstate__` and a `__setstate__` method. Described:
   [http://stackoverflow.com/questions/5247250/why-does-pickle-getstate-accept-as-a-return-value-the-very-instance-it-requi]

5. If you're trying to mock a module that contains class definitions; you can
   use the classes normally except that the type will be that of a lambda
   function instead of a class.
