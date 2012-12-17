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

# Configuration

Caliendo requires a supporting database table for caching objects. The only
databases currently supported are sqlite and mysql. One of two scenarios will
happen when you import and call caliendo the first time:

1. Caliendo will load the `DATABASES` object from the module you have set in
   the `DJANGO_SETTINGS_MODULE` environment variable. It will create a table
   called `test_io`.

2. Caliendo will fail to load the Django `settings.py` module and default to
   creating a sqlite database called `caliendo.db` in the directory it was
   invoked from. (Probably because your Django settings module isn't on the
   path.)

# Importing

The class that provides mock-objects in `caliendo` is called `Facade`. You can
import it like:

```python
from caliendo.facade import Facade
```

# Invokation

If you have an api you want to run under Caliendo you can invoke it like so:

```python
some_api     = SomeAPI()
caliendo_api = Facade( some_api ) # Note: caliendo is invoked with the INSTANCE, not the CLASS
```

As of revision v0.0.19 caliendo supports chaining so you can invoke it like:
```python
caliendo_api = Facade(some_api)
baz = caliendo_api.get_foo().get_bar().get_baz() 
```

If type(baz) is not in ( float, long, str, int, dict, list, unicode ) it will be automatically wrapped by caliendo. 

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
