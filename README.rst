testresources
=============

testresources extends ``unittest`` with a clean and simple API to provide test
optimisation where expensive common resources are needed for test cases - for
example sample working trees for VCS systems, reference databases for
enterprise applications, or web servers ... let your imagination run wild.

Usage
-----

Here is a minimal example demonstrating how to use testresources in your
project. It's not very useful - temporary directories are *not* the kind of
resource that testresources are most useful for and you would be better off
using something like fixtures for this - but it does demonstrate some of the
key concepts and classes, which we will discuss in more detail below. Firstly,
we have our "resource manager":

.. code-block:: python

    import shutil
    import tempfile
    import testresources


    class TemporaryDirectoryResource(testresources.TestResourceManager):

        def make(self, dependency_resources):
            return tempfile.mkdtemp()

        def clean(self, resource):
            shutil.rmtree(resource)

        def isDirty(self, resource):
            # Assume the directory is always modified after use.
            return True

With the resource manager in place, we can then declare the resource in a test
and access it via the assigned attribute:

.. code-block:: python

    import os
    import unittest


    class TestMyCode(unittest.TestCase, testresources.ResourcedTestCase):

        resources = [('workdir', TemporaryDirectoryResource())]

        def test_create_file(self):
            # self.workdir is automatically set up before this test runs
            # and torn down (or reused) afterwards.
            path = os.path.join(self.workdir, 'output.txt')
            with open(path, 'w') as f:
                f.write('hello')
            self.assertTrue(os.path.exists(path))

Finally, we need to add a ``load_tests`` hook to the test module so that we cna
use the ``OptimisingTestSuite``. This ensures our test runner will reorder
tests to minimise the number of times the resource is set up and torn down:

.. code-block:: python

    def load_tests(loader, tests, pattern):
        return testresources.OptimisingTestSuite(tests)

How it works
------------

The basic idea of testresources is:

* Tests declare the resources they need in a ``resources`` attribute.
* When the test is run, the required resource objects are allocated (either
  newly constructed, or reused), and assigned to attributes of the
  ``TestCase``.

testresources distinguishes a 'resource manager' (a subclass of
``TestResourceManager``) which acts as a kind of factory, and a 'resource'
which can be any kind of object returned from the manager class's
``getResource`` method.

Resources are either clean or dirty.  Being clean means they have same state in
all important ways as a newly constructed instance and they can therefore be
safely reused.

At this time, testresources is incompatible with setUpClass and setUpModule -
when an OptimisingTestSuite is wrapped around a test suite using those
features, the result will be flattened for optimisation and those setup's will
not run at all.

Main classes
------------

``testresources.ResourcedTestCase``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By extending or mixing-in this class, tests can have necessary resources
automatically allocated and disposed or recycled.

ResourceTestCase can be used as a base class for tests, and when that is done
tests will have their ``resources`` attribute automatically checked for
resources by both OptimisingTestSuite and their own setUp() and tearDown()
methods. (This allows tests to remain functional without needing this specific
TestSuite as a container). Alternatively, you can call setUpResources(self,
resources, test_result) and tearDownResources(self, resources, test_result)
from your own classes setUp and tearDown and the same behaviour will be
activated.

To declare the use of a resource, set the ``resources`` attribute to a list of
tuples of ``(attribute_name, resource_manager)``.

During setUp, for each declared requirement, the test gains an attribute
pointing to an allocated resource, which is the result of calling
``resource_manager.getResource()``.  ``finishedWith`` will be called on each
resource during tearDown().

For example::

    class TestLog(testresources.ResourcedTestCase):

        resources = [('branch', BzrPopulatedBranch())]

        def test_log(self):
            show_log(self.branch, ...)

``testresources.TestResourceManager``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A TestResourceManager is an object that tests can use to create resources.  It
can be overridden to manage different types of resources.  Normally test code
doesn't need to call any methods on it, as this will be arranged by the
testresources machinery.

When implementing a new ``TestResourceManager`` subclass you should consider
overriding these methods:

``make``
    Must be overridden in every concrete subclass.

    Returns a new instance of the resource object
    (the actual resource, not the TestResourceManager).  Doesn't need to worry about
    reuse, which is taken care of separately.  This method is only called when a
    new resource is definitely needed.

    ``make`` is called by ``getResource``; you should not normally need to override
    the latter.

``clean``
    Cleans up an existing resource instance, eg by deleting a directory or
    closing a network connection.  By default this does nothing, which may be
    appropriate for resources that are automatically garbage collected.

``_reset``
    Reset a no-longer-used dirty resource to a clean state.  By default this
    just discards it and creates a new one, but for some resources there may be a
    faster way to reset them.

``isDirty``
    Check whether an existing resource is dirty.  By default this just reports
    whether ``TestResourceManager.dirtied`` has been called or any of the
    dependency resources are dirty.

For instance::

    class TemporaryDirectoryResource(TestResourceManager):

        def clean(self, resource):
            shutil.rmtree(resource)

        def make(self, dependency_resources):
            return tempfile.mkdtemp()

        def isDirty(self, resource):
            # Can't detect when the directory is written to, so assume it
            # can never be reused.  We could list the directory, but that might
            # not catch it being open as a cwd etc.
            return True

The ``resources`` list on the TestResourceManager object is used to declare
dependencies. For instance, a DataBaseResource that needs a TemporaryDirectory
might be declared with a resources list::

    class DataBaseResource(TestResourceManager):

        resources = [("scratchdir", TemporaryDirectoryResource())]

Most importantly, two getResources to the same TestResourceManager with no
finishedWith call in the middle, will return the same object as long as it is
not dirty.

When a Test has a dependency and that dependency successfully completes but
returns None, the framework does *not* consider this an error: be sure to always
return a valid resource, or raise an error. Error handling hasn't been heavily
exercised, but any bugs in this area will be promptly dealt with.

A sample_ TestResourceManager can be found in the doc/ folder.

See pydoc testresources.TestResourceManager for details.

.. _sample: doc/example.py

``testresources.GenericResource``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Glue to adapt testresources to an existing resource-like class.

.. _fixtureresource:

``testresources.FixtureResource``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Glue to adapt testresources to the simpler ``fixtures.Fixture`` API. Long term
testresources is likely to consolidate on that simpler API as the recommended
method of writing resources.

This is discussed in further detail in `testresources vs. fixtures`_.

``testresources.OptimisingTestSuite``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This TestSuite will introspect all the test cases it holds directly and if
they declare needed resources, will run the tests in an order that attempts to
minimise the number of setup and tear downs required. It attempts to achieve
this by calling getResource() and finishedWith() around the sequence of tests
that use a specific resource.

Tests are added to an OptimisingTestSuite as normal. Any standard library
TestSuite objects will be flattened, while any custom TestSuite subclasses
will be distributed across their member tests. This means that any custom
logic in test suites should be preserved, at the price of some level of
optimisation.

Because the test suite does the optimisation, you can control the amount of
optimising that takes place by adding more or fewer tests to a single
OptimisingTestSuite. You could add everything to a single OptimisingTestSuite,
getting global optimisation or you could use several smaller
OptimisingTestSuites.

``testresources.TestLoader``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a trivial TestLoader that creates OptimisingTestSuites by default.

``unittest.TestResult``
~~~~~~~~~~~~~~~~~~~~~~~

testresources will log activity about resource creation and destruction to the
result object tests are run with. 6 extension methods are looked for:
``startCleanResource``, ``stopCleanResource``, ``startMakeResource``,
``stopMakeResource``, ``startResetResource`` and finally ``stopResetResource``.
``testresources.tests.ResultWithResourceExtensions`` is an example of a
``TestResult`` with these methods present.

Controlling resource reuse
--------------------------

When or how do I mark the resource dirtied?

The simplest approach is to have ``TestResourceManager.make`` call ``self.dirtied``:
the resource is always immediately dirty and will never be reused without first
being reset.  This is appropriate when the underlying resource is cheap to
reset or recreate, or when it's hard to detect whether it's been dirtied or to
trap operations that change it.

Alternatively, override ``TestResourceManager.isDirty`` and inspect the resource to
see if it is safe to reuse.

Finally, you can arrange for the returned resource to always call back to
``TestResourceManager.dirtied`` on the first operation that mutates it.

testresources vs. fixtures
--------------------------

The `fixtures <https://pypi.org/project/fixtures/>`_ library solves a similar
problem: managing test dependencies that need to be set up and torn down.
However, testresources and fixtures differ in the scope of the test
dependencies they manage.

testresources is designed for resources that are expensive to create and can be
safely shared across multiple tests.  The ``OptimisingTestSuite`` reorders
tests at the suite level so that tests sharing the same expensive resource run
consecutively, minimising the total number of setup and teardown cycles.  This
makes sense when the cost of constructing the resource is meaningfully large
relative to the cost of running the tests themselves. Examples of areas where
testresources makes sense would be provisioning database backends that are
shared across tests, or loading large, static test assets from disk.

By comparison, fixtures is designed for per-test setup and teardown. A fixture
is created fresh (or at least reset) for each test, and tests interact with it
via ``useFixture()``. fixtures is therefore far better suited for things like
mock patches, temporary directories, fake loggers, environment variables, or
fake HTTP sessions. In all these cases, the overhead of managing the resources
is low enough that recreating them per test is perfectly acceptable.

Finally, there may be cases where you wish to use the framework provided by
``fixtures.Fixture`` but avoid recreating it for every test in a module. To
this end, the ``FixtureResource`` class is what you want. As discussed
`previously <fixtureresource>`, this is a glue class that wraps any
``fixtures.Fixture`` so it can participate in testresources' suite-level
optimisation. If you already have a well-written fixture but want to avoid
recreating it for every test in a module, wrapping it in a ``FixtureResource``
and adding the ``load_tests`` hook is all that is needed. For example:

.. code-block:: python

    # Defined once at module scope so that all tests share the same instance.
    MY_RESOURCE = testresources.FixtureResource(MyExpensiveFixture())

    class MyTest(unittest.TestCase, testresources.ResourcedTestCase):
        resources = [('data', MY_RESOURCE)]

        def test_something(self):
            self.data.some_attribute  # provided by MyExpensiveFixture

    def load_tests(loader, tests, pattern):
        return testresources.OptimisingTestSuite(tests)

FAQ
---

* Can I dynamically request resources inside a test method?

  Generally, no, you shouldn't do this.  The idea is that the resources are
  declared statically, so that testresources can "smooth" resource usage across
  several tests.

  But, you may be able to find some object that is statically declared and reusable
  to act as the resource, which can then provide methods to generate sub-elements
  of itself during a test.

* If the resource is held inside the TestResourceManager object, and the
  TestResourceManager is typically constructed inline in the test case
  ``resources`` attribute, how can they be shared across different test
  classes?

  Good question.

  I guess you should arrange for a single instance to be held in an appropriate
  module scope, then referenced by the test classes that want to share it.

License
-------

Copyright (C) 2005-2013  Robert Collins <robertc@robertcollins.net>

  Licensed under either the Apache License, Version 2.0 or the BSD 3-clause
  license at the users choice. A copy of both licenses are available in the
  project source as Apache-2.0 and BSD. You may not use this file except in
  compliance with one of these two licences.

  Unless required by applicable law or agreed to in writing, software
  distributed under these licenses is distributed on an "AS IS" BASIS, WITHOUT
  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
  license you chose for the specific language governing permissions and
  limitations under that license.

  See the COPYING file for full details on the licensing of Testresources.
