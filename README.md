

# Installation

`caliendo` is set up to install with `pip`. You can install it directly from github by running:

    pip install git+git://github.com/buzzfeed/caliendo.git#egg=caliendo

Alternatively if you have a copy of the source on your machine; cd to the parent directory and run:

    pip install ./caliendo

# Configuration

`caliendo` requires a supporting database table for caching objects. The only databases currently supported are sqlite and MySql. One of two scenarios will happen when you import and call `caliendo` the first time:

1. `caliendo` will load the `DATABASES` object from the module you have set in the `DJANGO_SETTINGS_MODULE` environment variable. It will create a table called `test_io`.

2. `caliendo` will fail to load the Django settings.py module and default to creating a sqlite database called 'caliendo.db' in whatever directory it was invoked from. (Probably because your Django settings module isn't on the path) 

# Importing

The class that provides mock-objects in `caliendo` is called `Facade`. You can import it like:

    from caliendo.facade import Facade

# Invokation 

If you have an api you want to run under `caliendo` you can invoke it like:

    some_api     = SomeAPI( )
    caliendo_api = Facade( some_api ) # Note: caliendo is invoked with the INSTANCE, not the CLASS

# Execution

Once you have an instance of an API running under a `caliendo` facade you should be able to call all the methods normally.

# Troubleshooting

1. If you start getting unexpected API results you should clear the `caliendo` cache by simply deleting all the rows in the `test_io` table. 

2. `caliendo` doesn't support a large level of nested objects in arguments or return values. If you start getting unexpected results this may be the problem. Better nesting is to come.

3. If you alternate between calls to the `caliendo` `Facade` instance of an API and the API itself you will probably see unexpected results. `caliendo` maintains the state of the API by maintaining a reference to the API internally.

4. If you have a class inheriting from `dict` you'll need to define a `__getstate__` and a `__setstate__` method. Described: [http://stackoverflow.com/questions/5247250/why-does-pickle-getstate-accept-as-a-return-value-the-very-instance-it-requi]
