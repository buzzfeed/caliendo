# About

Caliendo is a very simple interface for mocking APIs. It allows you to skip
(potentially heavy) calls to your database or remote resources by storing sets
of calls and caching responses based on the sequence of execution as well as
function arguments. In some cases this improves unit test performance by
several orders of magnitude.

# Installation

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

# Tests

You can run the tests for each datastore method like (from the build root):

For sqlite:
```console
env CALIENDO_CONN_STRING='ENGINE=sqlite,NAME=caliendo,USER=,PASSWORD=,HOST=' python test/caliendo_test.py
```

For mysql:
```console
env CALIENDO_CONN_STRING='ENGINE=mysql,NAME=caliendo,USER=caliendo,PASSWORD=caliendo,HOST=localhost' python test/caliendo_test.py
```

For flatfiles:
```console
python test/caliendo_test.py
```

# Configuration

Caliendo requires a supporting database table or file read/write permissions
for caching objects. The only databases currently supported are sqlite and 
mysql. One of four scenarios will happen when you import and call caliendo 
the first time:

1. No database parameters are passed and caliendo writes to the specified 
   cache files. The default location is in the caliendo build, caliendo/cache
   and caliendo/seeds. You can change where caliendo creates these directories 
   by setting the environment variable:
```console
export CALIENDO_CACHE_PREFIX=/some/absolute/path
```

2. Caliendo will look for the environment variable, `CALIENDO_CONN_STRING` 
   for a string of the format: 
     'ENGINE=[mysql or sqlite],NAME=[database name],USER=[some user],PASSWORD=[password],HOST=[host]'
   It will attempt to use this string to connect to the specified database.

3. Caliendo will load the `DATABASES` object from the module you have set in
   the `DJANGO_SETTINGS_MODULE` environment variable. It will create a table
   called `test_io`.

4. Caliendo will fail to load the Django `settings.py` module and default to
   writing flat files as described in 1. (Probably because your Django 
   settings module isn't on the path.)

# Importing

The class that provides mock-objects in `caliendo` is called `Facade`. You can
import it like:

```python
from caliendo.facade import Facade
```

# Examples

Here are a few basic examples of use.

## Basic invocation

If you have an api you want to run under Caliendo you can invoke it like so:

```python
some_api     = SomeAPI()
caliendo_api = Facade( some_api ) # Note: caliendo is invoked with the INSTANCE, not the CLASS
```

## Chaining

As of revision v0.0.19 caliendo supports chaining so you can invoke it like:

```python
caliendo_api = Facade(some_api)
baz = caliendo_api.get_foo().get_bar().get_baz() 
```

If type(baz) is not in ( float, long, str, int, dict, list, unicode ) it will be automatically wrapped by caliendo. 

## Type Checking

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

# Execution

Once you have an instance of an API running under a `Facade` you should be able
to call all the methods normally.

# Troubleshooting

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
